import os

import httpx
from fastapi.testclient import TestClient

from app.auth.seed import seed_user
from app.db import connect
from app.main import create_app

# httpx.get é trocado dentro do processo que serve, e por isso o app sobe aqui
# em vez de num uvicorn à parte: o critério pede a degradação da rota, não o
# transporte. Toda saída de rede desta execução morre nesta função.
SAIU_PARA_A_REDE = []


def nunca_responde(*args, **kwargs):
    SAIU_PARA_A_REDE.append(args[0] if args else kwargs.get("url"))
    raise httpx.TimeoutException("demorou")


httpx.get = nunca_responde

LOGIN = "validador"
PASSWORD = "senha-de-validacao-9k2"
COM_CNPJ = os.environ.get("DASH_PAYEE_COM_CNPJ", "pagamento de boleto mycon")
APELIDO = "Consórcio Coimex"

app = create_app()
conn = connect()
seed_user(conn, LOGIN, PASSWORD)
cnpj = conn.execute(
    "SELECT MIN(merchant_cnpj) AS cnpj FROM transactions WHERE payee = ? AND merchant_cnpj IS NOT NULL",
    (COM_CNPJ,),
).fetchone()["cnpj"]
print(f"beneficiario={COM_CNPJ!r} cnpj_na_base={cnpj!r}")
conn.close()

with TestClient(app, follow_redirects=False) as client:
    client.post("/login", data={"login": LOGIN, "senha": PASSWORD})
    client.post("/configuracao/beneficiario", data={"beneficiario": COM_CNPJ, "nome": APELIDO})

    primeira = client.post("/configuracao/cnpj", data={"beneficiario": COM_CNPJ})
    print("1) com CNPJ válido, rede muda:", primeira.status_code)
    print("   diz que o tempo esgotou:", "tempo esgotou" in primeira.text)
    print("   o nome que já existia permanece:", APELIDO in primeira.text)
    print("   tentou a rede:", len(SAIU_PARA_A_REDE))

    adulterado = connect()
    adulterado.execute(
        "UPDATE transactions SET merchant_cnpj = '../etc' WHERE payee = ?", (COM_CNPJ,)
    )
    adulterado.commit()
    adulterado.close()
    antes = len(SAIU_PARA_A_REDE)

    segunda = client.post("/configuracao/cnpj", data={"beneficiario": COM_CNPJ})
    print("2) com CNPJ adulterado para ../etc:", segunda.status_code)
    print("   recusa dizendo que são 14 dígitos:", "14 dígitos" in segunda.text)
    print("   saiu para a rede:", len(SAIU_PARA_A_REDE) - antes)
    print("   o nome que já existia permanece:", APELIDO in segunda.text)
