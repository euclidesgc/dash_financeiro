import json
import re

import httpx

from app.config import load_config

ENDPOINT = "https://brasilapi.com.br/api/cnpj/v1/{cnpj}"
# Reason: the configuration screen does not wait for a model — shorter than
# the advisor's on purpose, because the owner is looking at a list and
# expects it to answer.
TIMEOUT_SECONDS = 8

DIGITS = re.compile(r"\D")
CNPJ_LENGTH = 14

NOT_FOUND = 404


class LookupUnavailableError(RuntimeError):
    pass


class InvalidCnpjError(ValueError):
    pass


def enabled() -> bool:
    # Reason: opt-in, like the advisor of item 009. This product is local by
    # definition, and each lookup tells a third party that this person has a
    # commercial relationship with that CNPJ — from a list ordered by how
    # much money each one represents (RF-25a).
    return load_config().cnpj_lookup


def digits(raw: str) -> str:
    # Reason: the value comes from a third party, not from the owner — a
    # CNPJ carrying a slash or a scheme would change the target of the
    # request (RF-25b).
    cleaned = DIGITS.sub("", raw or "")
    if len(cleaned) != CNPJ_LENGTH:
        raise InvalidCnpjError(f"CNPJ inválido: “{raw}”. São {CNPJ_LENGTH} dígitos.")
    return cleaned


def _said(reason: str) -> str:
    return f"A consulta não respondeu: {reason}."


def trade_name(cnpj: str) -> str:
    cleaned = digits(cnpj)
    try:
        answer = httpx.get(ENDPOINT.format(cnpj=cleaned), timeout=TIMEOUT_SECONDS)
        answer.raise_for_status()
        payload = answer.json()
        found = (payload.get("nome_fantasia") or payload.get("razao_social") or "").strip()
    except httpx.TimeoutException:
        raise LookupUnavailableError(_said("o tempo esgotou")) from None
    except httpx.HTTPStatusError as failure:
        if failure.response.status_code == NOT_FOUND:
            raise LookupUnavailableError(_said("a fonte não conhece este CNPJ")) from None
        raise LookupUnavailableError(_said("a fonte respondeu com erro")) from None
    except httpx.HTTPError:
        raise LookupUnavailableError(_said("não foi possível alcançar a fonte")) from None
    except (AttributeError, KeyError, ValueError, json.JSONDecodeError):
        raise LookupUnavailableError(_said("a fonte respondeu num formato inesperado")) from None
    if not found:
        raise LookupUnavailableError(_said("a fonte não trouxe nome para este CNPJ"))
    return found
