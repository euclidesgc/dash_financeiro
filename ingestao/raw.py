import json
import os
from datetime import date
from typing import Any

RAW = "data/raw"


def salvar(nome: str, conteudo: Any, pagina: int | None = None) -> str:
    os.makedirs(RAW, exist_ok=True)
    hoje = date.today().isoformat()
    sufixo = f"_p{pagina}" if pagina is not None else ""
    caminho = os.path.join(RAW, f"{nome}_{hoje}{sufixo}.json")
    with open(caminho, "w") as arquivo:
        json.dump(conteudo, arquivo, ensure_ascii=False, indent=2)
    return caminho
