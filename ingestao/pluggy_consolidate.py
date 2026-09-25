#!/usr/bin/env python3
"""Consolida os JSONs brutos da Pluggy numa tabela única de transações.

Lê data/raw/, escreve data/processed/. Não faz nenhuma chamada de rede.
Marca transferências entre contas próprias e pagamentos de fatura para que não
contem duas vezes no total de gasto, e identifica recorrências e parcelamentos.
"""

import csv
import glob
import json
import os
import re
import unicodedata
from collections import defaultdict
from datetime import datetime
from typing import Any

RAW = "data/raw"
PROC = "data/processed"

REGRAS_CATEGORIA = [
    (
        "Alimentação",
        r"ifood|rappi|uber\s*eats|restaurante|padaria|lanchonete|pizzar|burger|mcdonald|subway|bar\b|cafe|churrasc",
    ),
    (
        "Supermercado",
        r"supermercado|mercado|atacad|carrefour|assai|assaí|big\b|extra\b"
        r"|pao de acucar|hortifruti|sacolao",
    ),
    (
        "Transporte",
        r"uber|99\s*(app|pop|taxi)|cabify|posto|combustivel|gasolina|ipiranga"
        r"|shell|petrobras|estacionamento|pedagio|sem parar|conectcar",
    ),
    (
        "Saúde",
        r"farmacia|drogaria|drogasil|pacheco|raia|hospital|clinica|laborator"
        r"|unimed|amil|bradesco saude|odonto|dentista|psicolog",
    ),
    (
        "Assinaturas",
        r"netflix|spotify|amazon prime|disney|hbo|max\b|youtube|globoplay|deezer"
        r"|apple\.com|icloud|google\s*(one|storage)|microsoft|office\s*365"
        r"|adobe|chatgpt|openai|anthropic|claude",
    ),
    (
        "Moradia",
        r"aluguel|condominio|condomínio|energia|enel|cemig|light\b|copel|celpe"
        r"|neoenergia|sabesp|cagece|compesa|casan|agua\b|água\b|gas\b|gás\b",
    ),
    ("Telecom", r"vivo|claro|tim\b|oi\b|net\b|internet|telefon|banda larga|fibra"),
    (
        "Educação",
        r"escola|colegio|colégio|faculdade|universidade|curso|udemy|alura|coursera|mensalidade",
    ),
    (
        "Compras",
        r"mercado\s*livre|shopee|aliexpress|amazon|magazine|magalu|americanas"
        r"|casas bahia|renner|riachuelo|zara|shein",
    ),
    (
        "Lazer",
        r"cinema|ingresso|teatro|show|steam|playstation|xbox|nintendo|academia|smartfit|gympass",
    ),
    (
        "Impostos e tarifas",
        r"tarifa|iof|juros|multa|imposto|darf|das\b|inss|ipva|iptu|anuidade|manutencao de conta",
    ),
    ("Saques", r"saque|retirada|withdraw"),
    (
        "Investimentos",
        r"aplicacao|aplicação|resgate|cdb|tesouro|fundo|acoes|ações|corretora"
        r"|xp\b|rico\b|clear\b|nuinvest|inter invest",
    ),
]

PADRAO_TRANSFERENCIA = re.compile(r"transfer|ted\b|doc\b|pix\b|envio|recebiment|p2p", re.I)
PADRAO_PAGTO_FATURA = re.compile(
    r"pagamento\s+(de\s+)?(fatura|cart[aã]o)|pagto\s+fatura|fatura\s+cart|credit\s*card\s*payment|pagamento\s+recebido",
    re.I,
)
PADRAO_PARCELA = re.compile(r"(?<!\d)(\d{1,2})\s*(?:/|\s+de\s+)\s*(\d{1,2})(?!\d)")


def normalizar(texto: str | None) -> str:
    if not texto:
        return ""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"\d{2}/\d{2}(/\d{2,4})?", " ", t)
    t = PADRAO_PARCELA.sub(" ", t)
    t = re.sub(r"[^a-z\s]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    return t


def carregar(padrao: str) -> list[dict[str, Any]]:
    itens: list[dict[str, Any]] = []
    for caminho in sorted(glob.glob(os.path.join(RAW, padrao))):
        with open(caminho) as arquivo:
            corpo = json.load(arquivo)
        if isinstance(corpo, dict) and "results" in corpo:
            itens.extend(corpo["results"])
        elif isinstance(corpo, list):
            itens.extend(corpo)
        else:
            itens.append(corpo)
    return itens


def dedup(registros: list[dict[str, Any]]) -> list[dict[str, Any]]:
    vistos: set[Any] = set()
    saida: list[dict[str, Any]] = []
    for r in registros:
        chave = r.get("id")
        if chave and chave in vistos:
            continue
        if chave:
            vistos.add(chave)
        saida.append(r)
    return saida


def inferir_categoria(descricao: str | None) -> str:
    alvo = normalizar(descricao)
    for nome, padrao in REGRAS_CATEGORIA:
        if re.search(padrao, alvo):
            return nome
    return "Não classificado"


def instituicao_da_conta(conta: dict[str, Any]) -> str:
    for chave in ("marketingName", "institutionName", "name"):
        valor = conta.get(chave)
        if isinstance(valor, str) and valor.strip():
            return valor.strip()
    return "Desconhecida"


def parcelas_da_transacao(
    transacao: dict[str, Any],
) -> tuple[int, int, str] | tuple[None, None, None]:
    meta = transacao.get("creditCardMetadata") or {}
    atual = meta.get("installmentNumber")
    total = meta.get("totalInstallments")
    if atual and total:
        return int(atual), int(total), "api"
    achado = PADRAO_PARCELA.search(transacao.get("description") or "")
    if achado:
        a, t = int(achado.group(1)), int(achado.group(2))
        if 1 <= a <= t <= 48 and t > 1:
            return a, t, "descricao"
    return None, None, None


class NoRawAccountsError(RuntimeError):
    pass


def main() -> None:
    try:
        resumo = consolidate()
    except NoRawAccountsError as erro:
        raise SystemExit(str(erro)) from erro
    print(f"transacoes: {resumo['transacoes']}")
    print(f"  marcadas como transferencia/pagto de fatura: {resumo['transferencias']}")
    print(f"  categoria inferida por mim (Pluggy veio vazia): {resumo['inferidas']}")
    print(f"  saques em dinheiro (destino nao rastreavel): {resumo['saques']}")
    print(f"  lancamentos anulados por estorno: {resumo['estornadas']}")
    print(f"  recorrentes detectadas: {resumo['recorrentes']}")
    print(f"  parcelamentos detectados: {resumo['parcelamentos']}")


def consolidate() -> dict[str, int]:
    contas = dedup(carregar("accounts_*.json"))
    transacoes = dedup(carregar("*transactions_*.json"))
    if not contas:
        raise NoRawAccountsError("Sem data/raw/accounts_*.json — rode a extração antes.")
    os.makedirs(PROC, exist_ok=True)

    indice_conta: dict[Any, dict[str, Any]] = {c["id"]: c for c in contas}
    linhas: list[dict[str, Any]] = []
    for t in transacoes:
        conta = indice_conta.get(t.get("accountId"), {})
        categoria_pluggy = (t.get("category") or "").strip()
        inferida = not categoria_pluggy
        categoria = categoria_pluggy or inferir_categoria(t.get("description"))
        atual, total, fonte = parcelas_da_transacao(t)
        bruto = t.get("amount") or 0.0
        tipo = t.get("type") or ("CREDIT" if bruto > 0 else "DEBIT")
        valor = -bruto if conta.get("type") == "CREDIT" else bruto
        linhas.append(
            {
                "id": t.get("id"),
                "data": (t.get("date") or "")[:10],
                "conta_id": t.get("accountId"),
                "conta": conta.get("name"),
                "conta_tipo": conta.get("type"),
                "instituicao": instituicao_da_conta(conta),
                "descricao": (t.get("description") or "").strip(),
                "descricao_raw": (t.get("descriptionRaw") or "").strip(),
                # Reason: merchant arrives as None, not absent, in 1556 of
                # 1942 entries — t.get("merchant", {}) would raise
                # AttributeError on 80% of the base. An empty string is
                # absence, not a value — businessName comes back empty in
                # 48 entries that do have a trade name.
                "nome_fantasia": ((t.get("merchant") or {}).get("name") or "").strip(),
                "razao_social": ((t.get("merchant") or {}).get("businessName") or "").strip(),
                "cnpj": ((t.get("merchant") or {}).get("cnpj") or "").strip(),
                "recebedor": (
                    ((t.get("paymentData") or {}).get("receiver") or {}).get("name") or ""
                ).strip(),
                "valor": valor,
                "valor_bruto_api": bruto,
                "tipo": tipo,
                "categoria_pluggy": categoria_pluggy,
                "categoria": categoria,
                "categoria_inferida": inferida,
                "parcela_atual": atual,
                "parcela_total": total,
                "parcela_fonte": fonte,
                "chave": normalizar(t.get("description")),
            }
        )

    linhas.sort(key=lambda linha: (linha["data"], linha["conta"] or "", linha["id"] or ""))
    marcar_transferencias(linhas, indice_conta)
    recorrentes = detectar_recorrentes(linhas)
    parcelamentos = agrupar_parcelamentos(linhas)

    campos = [
        "id",
        "data",
        "conta",
        "conta_tipo",
        "instituicao",
        "descricao",
        "valor",
        "tipo",
        "categoria_pluggy",
        "categoria",
        "categoria_inferida",
        "parcela_atual",
        "parcela_total",
        "parcela_fonte",
        "eh_transferencia",
        "motivo_transferencia",
        "eh_saque",
        "eh_estorno",
        "estornada_por",
        "valor_bruto_api",
        "nome_fantasia",
        "razao_social",
        "cnpj",
        "recebedor",
    ]
    with open(os.path.join(PROC, "transacoes.csv"), "w", newline="") as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=campos, extrasaction="ignore")
        escritor.writeheader()
        escritor.writerows(linhas)
    with open(os.path.join(PROC, "transacoes.json"), "w") as arquivo:
        json.dump(linhas, arquivo, ensure_ascii=False, indent=2)
    with open(os.path.join(PROC, "recorrentes.json"), "w") as arquivo:
        json.dump(recorrentes, arquivo, ensure_ascii=False, indent=2)
    with open(os.path.join(PROC, "parcelamentos.json"), "w") as arquivo:
        json.dump(parcelamentos, arquivo, ensure_ascii=False, indent=2)

    return {
        "transacoes": len(linhas),
        "transferencias": sum(1 for linha in linhas if linha["eh_transferencia"]),
        "inferidas": sum(1 for linha in linhas if linha["categoria_inferida"]),
        "saques": sum(1 for linha in linhas if linha.get("eh_saque")),
        "estornadas": sum(1 for linha in linhas if linha.get("estornada_por")),
        "recorrentes": len(recorrentes),
        "parcelamentos": len(parcelamentos),
    }


def marcar_transferencias(
    linhas: list[dict[str, Any]], indice_conta: dict[Any, dict[str, Any]]
) -> None:
    for linha in linhas:
        linha["eh_transferencia"] = False
        linha["motivo_transferencia"] = ""

    por_valor: defaultdict[Any, list[int]] = defaultdict(list)
    for i, linha in enumerate(linhas):
        if linha["valor"] is None:
            continue
        por_valor[round(abs(linha["valor"]), 2)].append(i)

    for valor, indices in por_valor.items():
        if valor == 0:
            continue
        debitos = [i for i in indices if (linhas[i]["valor"] or 0) < 0]
        creditos = [i for i in indices if (linhas[i]["valor"] or 0) > 0]
        usados = set()
        for d in debitos:
            ld = linhas[d]
            for c in creditos:
                if c in usados:
                    continue
                lc = linhas[c]
                if ld["conta_id"] == lc["conta_id"]:
                    continue
                if not ld["data"] or not lc["data"]:
                    continue
                delta = abs(
                    (datetime.fromisoformat(ld["data"]) - datetime.fromisoformat(lc["data"])).days
                )
                if delta > 3:
                    continue
                fatura = lc["conta_tipo"] == "CREDIT" or PADRAO_PAGTO_FATURA.search(
                    ld["descricao"] or ""
                )
                motivo = "pagamento de fatura" if fatura else "transferência entre contas próprias"
                for alvo in (ld, lc):
                    alvo["eh_transferencia"] = True
                    alvo["motivo_transferencia"] = motivo
                usados.add(c)
                break

    for linha in linhas:
        if linha["eh_transferencia"]:
            continue
        if PADRAO_PAGTO_FATURA.search(linha["descricao"] or ""):
            linha["eh_transferencia"] = True
            linha["motivo_transferencia"] = "pagamento de fatura (sem par encontrado)"

    marcar_por_categoria_pluggy(linhas)
    netar_estornos(linhas)


def marcar_por_categoria_pluggy(linhas: list[dict[str, Any]]) -> None:
    """A contraparte pode estar numa conta que não foi compartilhada; nesse caso o
    pareamento débito/crédito não acha par e a categoria da Pluggy é o único sinal."""
    for linha in linhas:
        categoria = linha["categoria_pluggy"] or ""
        if categoria == "Credit card payment" and not linha["eh_transferencia"]:
            linha["eh_transferencia"] = True
            linha["motivo_transferencia"] = "pagamento de fatura (categoria Pluggy)"
        if categoria == "Same person transfer" and not linha["eh_transferencia"]:
            linha["eh_transferencia"] = True
            linha["motivo_transferencia"] = "transferência entre contas próprias (categoria Pluggy)"
        linha["eh_saque"] = categoria == "Same person transfer - CASH"
        if linha["eh_saque"]:
            linha["eh_transferencia"] = False
            linha["motivo_transferencia"] = ""


def netar_estornos(linhas: list[dict[str, Any]]) -> None:
    """ESTORNO devolve um débito lançado antes; os dois se anulam e nenhum é gasto."""
    for linha in linhas:
        linha["eh_estorno"] = False
        linha["estornada_por"] = ""
    estornos = [linha for linha in linhas if "ESTORNO" in (linha["descricao"] or "").upper()]
    for estorno in estornos:
        estorno["eh_estorno"] = True
        alvo_valor = round(abs(estorno["valor"] or 0), 2)
        candidatos = [
            linha
            for linha in linhas
            if linha is not estorno
            and not linha["eh_estorno"]
            and not linha["estornada_por"]
            and round(abs(linha["valor"] or 0), 2) == alvo_valor
            and (linha["valor"] or 0) < 0
            and linha["data"] <= estorno["data"]
        ]
        if candidatos:
            original = max(candidatos, key=lambda linha: linha["data"])
            original["estornada_por"] = estorno["id"]
            estorno["estornada_por"] = original["id"]


def detectar_recorrentes(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grupos: defaultdict[Any, list[dict[str, Any]]] = defaultdict(list)
    for linha in linhas:
        if (
            linha["eh_transferencia"]
            or linha.get("estornada_por")
            or (linha["valor"] or 0) >= 0
            or not linha["chave"]
            or not linha["data"]
        ):
            continue
        grupos[linha["chave"]].append(linha)

    recorrentes: list[dict[str, Any]] = []
    for chave, itens in grupos.items():
        meses: defaultdict[str, list[Any]] = defaultdict(list)
        for linha in itens:
            meses[linha["data"][:7]].append(abs(linha["valor"]))
        if len(meses) < 3:
            continue
        ordenados = sorted(meses)
        consecutivos, maior = 1, 1
        for a, b in zip(ordenados, ordenados[1:], strict=False):
            ya, ma = int(a[:4]), int(a[5:7])
            yb, mb = int(b[:4]), int(b[5:7])
            consecutivos = consecutivos + 1 if (yb * 12 + mb) - (ya * 12 + ma) == 1 else 1
            maior = max(maior, consecutivos)
        if maior < 3:
            continue
        valores = [v for vs in meses.values() for v in vs]
        media = sum(valores) / len(valores)
        if media == 0:
            continue
        variacao = max(abs(v - media) / media for v in valores)
        if variacao > 0.35:
            continue
        recorrentes.append(
            {
                "chave": chave,
                "descricao": itens[-1]["descricao"],
                "instituicao": itens[-1]["instituicao"],
                "categoria": itens[-1]["categoria"],
                "meses": len(meses),
                "meses_consecutivos": maior,
                "valor_medio": round(media, 2),
                "ultimo_mes": max(ordenados),
                "primeiro_mes": min(ordenados),
                "ocorrencias": len(itens),
            }
        )
    recorrentes.sort(key=lambda r: -r["valor_medio"])
    return recorrentes


def agrupar_parcelamentos(linhas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grupos: defaultdict[Any, list[dict[str, Any]]] = defaultdict(list)
    for linha in linhas:
        if linha["parcela_total"]:
            chave_grupo = (
                linha["chave"],
                linha["parcela_total"],
                round(abs(linha["valor"] or 0), 2),
            )
            grupos[chave_grupo].append(linha)
    saida: list[dict[str, Any]] = []
    for (_chave, total, valor), itens in grupos.items():
        vistas = sorted({i["parcela_atual"] for i in itens if i["parcela_atual"]})
        ultima = max(itens, key=lambda i: i["data"])
        saida.append(
            {
                "descricao": ultima["descricao"],
                "instituicao": ultima["instituicao"],
                "conta": ultima["conta"],
                "valor_parcela": valor,
                "total_parcelas": total,
                "parcelas_vistas": vistas,
                "ultima_parcela_vista": max(vistas) if vistas else None,
                "data_ultima": ultima["data"],
                "restantes": total - max(vistas) if vistas else None,
                "fonte": ultima["parcela_fonte"],
            }
        )
    saida.sort(key=lambda p: -(p["valor_parcela"] * (p["restantes"] or 0)))
    return saida


if __name__ == "__main__":
    main()
