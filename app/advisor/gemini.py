import json
from dataclasses import dataclass

import httpx

MODEL = "gemini-2.5-flash"
ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
TIMEOUT_SECONDS = 20

# The one rule the model cannot break. Every figure it is allowed to say is
# already in the context, computed by tested code: if it did the arithmetic it
# would get it wrong, and a wrong number in the central unit of this product
# destroys trust in everything else (invariante 23).
INSTRUCTION = (
    "Você lê um painel financeiro pessoal e responde em português do Brasil, "
    "em no máximo quatro frases, sem exclamação e sem tom animado. "
    "VOCÊ NUNCA CALCULA. Todo número que você citar precisa aparecer literalmente "
    "no contexto abaixo, copiado dígito a dígito. Se a resposta exigir uma conta "
    "que o contexto não traz pronta, diga que o painel ainda não calcula isso e "
    "aponte a tela onde o dono pode ver. Não invente categoria, data nem valor."
)


class AdvisorUnavailableError(RuntimeError):
    pass


@dataclass(frozen=True)
class Reading:
    text: str
    model: str


def ask(question: str, context: str, *, api_key: str | None) -> Reading:
    if not api_key:
        raise AdvisorUnavailableError(
            "A leitura da IA está indisponível: falta a chave GEMINI_API_KEY no ambiente. "
            "Os números da tela são os mesmos, e eles não dependem dela."
        )
    body = {
        "systemInstruction": {"parts": [{"text": INSTRUCTION}]},
        "contents": [{"parts": [{"text": f"{context}\n\nPergunta: {question}"}]}],
    }
    try:
        answer = httpx.post(
            ENDPOINT.format(model=MODEL),
            params={"key": api_key},
            json=body,
            timeout=TIMEOUT_SECONDS,
        )
        answer.raise_for_status()
        parts = answer.json()["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
    except (httpx.HTTPError, KeyError, IndexError, ValueError, json.JSONDecodeError) as failure:
        raise AdvisorUnavailableError(
            f"A leitura da IA está indisponível ({type(failure).__name__}). "
            "Os números da tela são os mesmos, e eles não dependem dela."
        ) from None
    if not text:
        raise AdvisorUnavailableError(
            "A leitura da IA voltou vazia. Os números da tela são os mesmos."
        )
    return Reading(text=text, model=MODEL)
