import json
from dataclasses import dataclass

import httpx

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


UNAUTHORISED = (401, 403)
TOO_MANY = 429


def _refused(status: int) -> str:
    # The owner cannot act on "HTTPStatusError". They can act on "the key was
    # refused" (norma 16: interface em pt-BR, e erro que diz o próximo ato).
    if status in UNAUTHORISED:
        return "a chave foi recusada pelo provedor"
    if status == TOO_MANY:
        return "o provedor recusou por excesso de chamadas; tente daqui a pouco"
    return "o provedor respondeu com erro"


def _said(reason: str) -> str:
    return (
        f"A leitura da IA está indisponível: {reason}. "
        "Os números da tela são os mesmos, e eles não dependem dela."
    )


@dataclass(frozen=True)
class Reading:
    text: str
    model: str


def ask(question: str, context: str, *, api_key: str | None, model: str) -> Reading:
    if not api_key:
        raise AdvisorUnavailableError(
            "A leitura da IA está indisponível: falta a chave da IA. Informe em "
            "/configuracao. Os números da tela são os mesmos, e eles não dependem dela."
        )
    body = {
        "systemInstruction": {"parts": [{"text": INSTRUCTION}]},
        "contents": [{"parts": [{"text": f"{context}\n\nPergunta: {question}"}]}],
    }
    try:
        answer = httpx.post(
            ENDPOINT.format(model=model),
            headers={"x-goog-api-key": api_key},
            json=body,
            timeout=TIMEOUT_SECONDS,
        )
        answer.raise_for_status()
        parts = answer.json()["candidates"][0]["content"]["parts"]
        text = "".join(part.get("text", "") for part in parts).strip()
    except httpx.TimeoutException:
        raise AdvisorUnavailableError(_said("o modelo demorou demais para responder")) from None
    except httpx.HTTPStatusError as failure:
        raise AdvisorUnavailableError(_said(_refused(failure.response.status_code))) from None
    except httpx.HTTPError:
        raise AdvisorUnavailableError(_said("não foi possível alcançar o modelo")) from None
    except (KeyError, IndexError, ValueError, json.JSONDecodeError):
        raise AdvisorUnavailableError(_said("o modelo respondeu num formato inesperado")) from None
    if not text:
        raise AdvisorUnavailableError(
            "A leitura da IA voltou vazia. Os números da tela são os mesmos."
        )
    return Reading(text=text, model=model)
