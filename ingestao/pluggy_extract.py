"""Extração somente-leitura dos dados financeiros pessoais via API da Pluggy.

Subcomandos:
  criar-item   cria o item do conector 200 (MeuPluggy), cadastra-o em Conexões e devolve a
               URL de autorização
  status       mostra status, execução e warnings de cada conexão cadastrada (ou de --item)
  extrair      baixa accounts, transactions, bills, loans, investments e identity de cada
               conexão cadastrada (ou de --item)

As conexões são as da tela Conexões do painel, na base apontada por DASH_DB_PATH.
Rode da raiz do projeto: uv run python -m ingestao.pluggy_extract <subcomando>.

O CLIENT_SECRET e a apiKey nunca são impressos nem gravados em disco.
Nenhum endpoint de escrita além do POST /items explicitamente confirmado é chamado.
"""

import argparse
import json
import os
import sqlite3
import time
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Mapping
from datetime import datetime
from typing import Any, cast

from dotenv import load_dotenv

from app.db import connect
from app.migrate import run_migrations
from app.queries.pluggy_connections import list_item_ids
from app.sync.connections import DuplicateConnectionError, add_connection
from ingestao.raw import salvar

API = "https://api.pluggy.ai"
DEFAULT_ENV_FILE = ".env"
CREDENTIALS = ("PLUGGY_CLIENT_ID", "PLUGGY_CLIENT_SECRET")
CONNECTOR_MEU_PLUGGY = 200

NO_CONNECTIONS = "Nenhuma conexão cadastrada. Cadastre em Conexões ou passe --item."

ESCRITA_PROIBIDA = ("/payments", "/payment-", "/transfers", "/smart-transfers", "/boletos")


class MissingCredentialsError(RuntimeError):
    pass


def read_credentials(env: Mapping[str, str] | None = None) -> tuple[str, str]:
    if env is None:
        # Reason: same rule as app/config.py — the file named by DASH_ENV_FILE
        # fills only what the process environment does not already define.
        load_dotenv(os.environ.get("DASH_ENV_FILE", DEFAULT_ENV_FILE), override=False)
        env = os.environ
    missing = [name for name in CREDENTIALS if not env.get(name)]
    if missing:
        raise MissingCredentialsError(f"Faltam as credenciais da Pluggy: {', '.join(missing)}.")
    return env["PLUGGY_CLIENT_ID"], env["PLUGGY_CLIENT_SECRET"]


def autenticar() -> str:
    client_id, client_secret = read_credentials()
    corpo = json.dumps({"clientId": client_id, "clientSecret": client_secret}).encode()
    req = urllib.request.Request(
        f"{API}/auth", data=corpo, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(req, timeout=60) as resposta:
        # Reason: apiKey is always a string in Pluggy's contract; json.loads
        # returns Any.
        return cast(str, json.loads(resposta.read())["apiKey"])


def chamar(
    api_key: str, path: str, metodo: str = "GET", corpo: dict[str, Any] | None = None
) -> tuple[int, Any]:
    if metodo != "GET" and any(p in path for p in ESCRITA_PROIBIDA):
        raise SystemExit(f"BLOQUEADO: {metodo} {path} é endpoint de movimentação de dinheiro")
    if metodo == "DELETE":
        raise SystemExit("BLOQUEADO: este script nunca apaga item ou consentimento")
    dados = json.dumps(corpo).encode() if corpo is not None else None
    cabecalhos = {"X-API-KEY": api_key}
    if dados:
        cabecalhos["Content-Type"] = "application/json"
    req = urllib.request.Request(API + path, data=dados, headers=cabecalhos, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=120) as resposta:
            return resposta.status, json.loads(resposta.read())
    except urllib.error.HTTPError as erro:
        texto = erro.read().decode(errors="replace")
        try:
            return erro.code, json.loads(texto)
        except json.JSONDecodeError:
            return erro.code, {"raw": texto[:500]}


def paginar(api_key: str, path: str, params: dict[str, Any]) -> tuple[list[Any], int, Any]:
    resultados: list[Any] = []
    pagina = 1
    while True:
        query = dict(params)
        query.update({"page": pagina, "pageSize": 500})
        status, corpo = chamar(api_key, f"{path}?{urllib.parse.urlencode(query)}")
        if status != 200:
            return resultados, status, corpo
        lote = corpo.get("results", [])
        resultados.extend(lote)
        salvar(
            path.strip("/").replace("/", "_")
            + "_"
            + params.get("accountId", params.get("itemId", "todos"))[:8],
            corpo,
            pagina,
        )
        total_paginas = corpo.get("totalPages", 1)
        if pagina >= total_paginas or not lote:
            break
        pagina += 1
    return resultados, 200, None


def paginar_cursor(api_key: str, path: str, params: dict[str, Any]) -> tuple[list[Any], int, Any]:
    """GET /v2/* pagina por cursor: a resposta traz `next` como query string
    (`?accountId=...&after=...`), e `null` encerra."""
    resultados: list[Any] = []
    sufixo = "?" + urllib.parse.urlencode(params)
    pagina = 1
    while True:
        status, corpo = chamar(api_key, path + sufixo)
        if status != 200:
            return resultados, status, corpo
        lote = corpo.get("results", [])
        resultados.extend(lote)
        salvar(
            path.strip("/").replace("/", "_") + "_" + params.get("accountId", "todos")[:8],
            corpo,
            pagina,
        )
        proximo = corpo.get("next")
        if not proximo or not lote:
            break
        if proximo.startswith("?"):
            sufixo = proximo
        elif proximo.startswith("http"):
            partes = urllib.parse.urlparse(proximo)
            sufixo = "?" + partes.query
        else:
            query = dict(params)
            query["after"] = proximo
            sufixo = "?" + urllib.parse.urlencode(query)
        pagina += 1
    return resultados, 200, None


def itens_salvos(conn: sqlite3.Connection) -> list[str]:
    return list_item_ids(conn)


def registrar_item(conn: sqlite3.Connection, item_id: str) -> None:
    try:
        add_connection(conn, item_id)
    except DuplicateConnectionError:
        return


def _abrir_base() -> sqlite3.Connection:
    run_migrations()
    return connect()


def _ids_pedidos(args: argparse.Namespace) -> list[str]:
    if args.item:
        return [args.item]
    conn = _abrir_base()
    try:
        ids = itens_salvos(conn)
    finally:
        conn.close()
    if not ids:
        raise SystemExit(NO_CONNECTIONS)
    return ids


def cmd_criar_item(args: argparse.Namespace) -> None:
    if not args.confirmo:
        raise SystemExit("Criação de item exige --confirmo (autorização explícita do humano).")
    api_key = autenticar()
    conector = args.conector or CONNECTOR_MEU_PLUGGY
    corpo = {"connectorId": conector, "parameters": {}, "oauthRedirectUri": args.redirect}
    status, item = chamar(api_key, "/items", metodo="POST", corpo=corpo)
    print(f"POST /items -> {status}")
    if status not in (200, 201):
        print(json.dumps(item, ensure_ascii=False, indent=2)[:1200])
        raise SystemExit(1)
    item_id = item["id"]
    conn = _abrir_base()
    try:
        registrar_item(conn, item_id)
    finally:
        conn.close()
    salvar(f"item_criado_{item_id[:8]}", item)
    print(f"itemId: {item_id}  (cadastrado em Conexões)")
    print(f"conector: {(item.get('connector') or {}).get('name')}")
    print(f"status: {item.get('status')} / {item.get('executionStatus')}")
    url = extrair_oauth_url(item)
    for _ in range(30):
        if url:
            break
        time.sleep(3)
        _, item = chamar(api_key, f"/items/{item_id}")
        url = extrair_oauth_url(item)
        print(f"  aguardando oauthUrl... status={item.get('status')}/{item.get('executionStatus')}")
    if url:
        print("\n=== ABRA ESTA URL NO NAVEGADOR E AUTORIZE ===")
        print(url)
    else:
        print("\nNao veio oauthUrl. Item bruto salvo em data/raw/.")


def extrair_oauth_url(item: dict[str, Any]) -> str | None:
    parametro = item.get("parameter") or {}
    if isinstance(parametro, dict):
        if parametro.get("name") in ("oauthUrl", "oauth"):
            # Reason: Pluggy's "data"/"value" are always a string or
            # absent; dict[str, Any] makes the read Any to the checker.
            return cast(str | None, parametro.get("data") or parametro.get("value"))
        if parametro.get("data", "").startswith("http"):
            return cast(str, parametro["data"])
    acao = item.get("userAction") or {}
    for chave in ("data", "url", "instructions"):
        valor = acao.get(chave)
        if isinstance(valor, str) and valor.startswith("http"):
            return valor
    return None


def cmd_status(args: argparse.Namespace) -> None:
    ids = _ids_pedidos(args)
    api_key = autenticar()
    for item_id in ids:
        status_de_um(api_key, item_id)


def status_de_um(api_key: str, item_id: str) -> None:
    status, item = chamar(api_key, f"/items/{item_id}")
    print(f"GET /items/{item_id} -> {status}")
    if status != 200:
        print(json.dumps(item, ensure_ascii=False, indent=2)[:800])
        raise SystemExit(1)
    salvar(f"item_{item_id[:8]}", item)
    conector = item.get("connector") or {}
    print(f"  conector: {conector.get('id')} / {conector.get('name')}")
    print(f"  status: {item.get('status')} | execucao: {item.get('executionStatus')}")
    print(f"  ultima atualizacao: {item.get('lastUpdatedAt')}")
    print(f"  consentimento expira: {item.get('consentExpiresAt')}")
    print(f"  statusDetail: {json.dumps(item.get('statusDetail'), ensure_ascii=False)}")
    url = extrair_oauth_url(item)
    if url:
        print(f"  AGUARDANDO AUTORIZACAO: {url}")


def cmd_extrair(args: argparse.Namespace) -> None:
    ids = _ids_pedidos(args)
    api_key = autenticar()
    geral: list[dict[str, Any]] = []
    for item_id in ids:
        print(f"\n########## item {item_id} ##########")
        geral.append(extrair_um(api_key, item_id, args))
    salvar("inventario_geral", geral)
    total_contas = sum(len(g["contas"]) for g in geral)
    total_txs = sum(c["transacoes"] for g in geral for c in g["contas"])
    print(f"\n=== TOTAL: {len(geral)} itens, {total_contas} contas, {total_txs} transacoes ===")


def extrair_um(api_key: str, item_id: str, args: argparse.Namespace) -> dict[str, Any]:
    inventario: dict[str, Any] = {
        "itemId": item_id,
        "extraidoEm": datetime.now().isoformat(),
        "contas": [],
        "faltantes": [],
    }

    status, item = chamar(api_key, f"/items/{item_id}")
    if status != 200:
        raise SystemExit(f"GET /items/{item_id} -> {status}: {item}")
    salvar(f"item_{item_id[:8]}", item)
    inventario["conector"] = (item.get("connector") or {}).get("name")
    inventario["itemStatus"] = item.get("status")
    inventario["itemExecutionStatus"] = item.get("executionStatus")
    inventario["statusDetail"] = item.get("statusDetail")
    inventario["consentExpiresAt"] = item.get("consentExpiresAt")

    status, contas = chamar(
        api_key, f"/accounts?{urllib.parse.urlencode({'itemId': item_id, 'pageSize': 500})}"
    )
    if status != 200:
        raise SystemExit(f"GET /accounts -> {status}: {contas}")
    salvar(f"accounts_{item_id[:8]}", contas)
    lista_contas = contas.get("results", [])
    print(f"contas: {len(lista_contas)}")

    for conta in lista_contas:
        conta_id = conta["id"]
        rotulo = f"{conta.get('name')} ({conta.get('type')}/{conta.get('subtype')})"
        transacoes, st, err = paginar_cursor(api_key, "/v2/transactions", {"accountId": conta_id})
        if st != 200:
            inventario["faltantes"].append(f"transactions da conta {rotulo}: HTTP {st} {err}")
            transacoes = []
        datas = sorted(t["date"] for t in transacoes if t.get("date"))
        inventario["contas"].append(
            {
                "id": conta_id,
                "nome": conta.get("name"),
                "tipo": conta.get("type"),
                "subtipo": conta.get("subtype"),
                "numero": conta.get("number"),
                "saldo": conta.get("balance"),
                "moeda": conta.get("currencyCode"),
                "transacoes": len(transacoes),
                "primeira": datas[0][:10] if datas else None,
                "ultima": datas[-1][:10] if datas else None,
            }
        )
        print(
            f"  {rotulo}: {len(transacoes)} transacoes "
            f"({datas[0][:10] if datas else '-'} a {datas[-1][:10] if datas else '-'})"
        )

        if conta.get("type") == "CREDIT":
            faturas, st, err = paginar(api_key, "/bills", {"accountId": conta_id})
            if st != 200:
                inventario["faltantes"].append(f"bills da conta {rotulo}: HTTP {st} {err}")
            else:
                print(f"    faturas: {len(faturas)}")

    for nome, path in [
        ("loans", "/loans"),
        ("investments", "/investments"),
        ("identity", "/identity"),
    ]:
        registros, st, err = paginar(api_key, path, {"itemId": item_id})
        if st != 200:
            inventario["faltantes"].append(f"{nome}: HTTP {st} {err}")
            print(f"{nome}: indisponivel (HTTP {st})")
        else:
            print(f"{nome}: {len(registros)}")

    _, categorias = chamar(api_key, "/categories?pageSize=500")
    salvar("categories", categorias)
    salvar(f"inventario_{item_id[:8]}", inventario)
    return inventario


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("criar-item")
    p.add_argument("--confirmo", action="store_true")
    p.add_argument("--conector", type=int)
    p.add_argument("--redirect", default="https://ganza.duckdns.org/")
    p.set_defaults(func=cmd_criar_item)

    p = sub.add_parser("status")
    p.add_argument("--item")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("extrair")
    p.add_argument("--item")
    p.add_argument("--desde", default="2000-01-01")
    p.set_defaults(func=cmd_extrair)

    args = parser.parse_args()
    try:
        args.func(args)
    except MissingCredentialsError as erro:
        raise SystemExit(str(erro)) from erro


if __name__ == "__main__":
    main()
