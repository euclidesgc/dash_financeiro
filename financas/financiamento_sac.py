#!/usr/bin/env python3
"""Simulação SAC do financiamento imobiliário, a partir dos dados do contrato.

Determinística e sem correção monetária futura — o índice do contrato não é
conhecido, então todo valor aqui é nominal, a saldo e taxa de hoje.
"""

import json

DADOS = json.load(open("data/manual/financiamento_caixa.json"))
SALDO = DADOS["saldo_devedor"]
MESES = DADOS["prazo_restante_meses"]
TAXA_AA = DADOS["juros_efetivos_aa_pct"] / 100
TAXA_AM = (1 + TAXA_AA) ** (1 / 12) - 1
ENCARGO_OBSERVADO = 2456.09


def simular(
    saldo: float, meses: int, taxa: float, amortizacao_extra: float = 0.0
) -> dict[str, float]:
    """Amortização constante do contrato original; o aporte extra reduz o PRAZO,
    porque a parcela segue a mesma e o saldo acaba antes."""
    amortizacao = saldo / meses
    saldo -= amortizacao_extra
    juros_total = 0.0
    parcelas: list[float] = []
    while saldo > 0.005 and len(parcelas) < meses + 1:
        juros = saldo * taxa
        principal = min(amortizacao, saldo)
        parcelas.append(principal + juros)
        juros_total += juros
        saldo -= principal
    return {
        "parcelas": len(parcelas),
        "primeira": parcelas[0] if parcelas else 0,
        "ultima": parcelas[-1] if parcelas else 0,
        "juros_total": juros_total,
        "pago_total": sum(parcelas),
    }


def main() -> None:
    print(f"saldo devedor      R$ {SALDO:>12,.2f}")
    print(f"prazo restante     {MESES} meses ({MESES / 12:.1f} anos)")
    print(f"juros efetivos     {DADOS['juros_efetivos_aa_pct']}% a.a. = {TAXA_AM * 100:.4f}% a.m.")
    print()

    base = simular(SALDO, MESES, TAXA_AM)
    print("=== MANTENDO O CONTRATO ATE O FIM (SAC, sem correcao monetaria) ===")
    print(
        f"  primeira parcela     R$ {base['primeira']:>10,.2f}   "
        f"(observado no extrato: R$ {ENCARGO_OBSERVADO:,.2f})"
    )
    print(f"  ultima parcela       R$ {base['ultima']:>10,.2f}")
    print(f"  JUROS TOTAIS         R$ {base['juros_total']:>10,.2f}")
    print(f"  total desembolsado   R$ {base['pago_total']:>10,.2f}")
    seguros = ENCARGO_OBSERVADO - base["primeira"]
    print(
        f"  seguros/taxas fora do calculo: R$ {seguros:,.2f}/mes -> "
        f"R$ {seguros * MESES:,.2f} em {MESES} meses"
    )
    print()

    liq = DADOS["liquidacao_recursos_proprios"]["valor_total_da_divida"]
    print("=== LIQUIDANDO AGORA ===")
    print(
        f"  valor da liquidacao em "
        f"{DADOS['liquidacao_recursos_proprios']['data_prevista']}: R$ {liq:>10,.2f}"
    )
    print(f"  economia nominal de juros:  R$ {base['juros_total'] - (liq - SALDO):>10,.2f}")
    print(
        f"  (a liquidacao custa R$ {liq - SALDO:,.2f} acima do saldo — "
        f"sao as 2 prestacoes em aberto e encargos)"
    )
    print()

    print("=== AMORTIZANDO ANTECIPADO (reduzindo prazo) ===")
    print(f"  {'aporte':>10}  {'prazo':>7}  {'meses a menos':>13}  {'juros evitados':>16}")
    for extra in (5000, 10000, 20000, 50000):
        s = simular(SALDO, MESES, TAXA_AM, extra)
        print(
            f"  R$ {extra:>7,}  {s['parcelas']:>5}m  {MESES - s['parcelas']:>11}m  "
            f"R$ {base['juros_total'] - s['juros_total']:>13,.2f}"
        )
    print()

    print("=== COMPARACAO DE TAXA: onde cada real rende mais ===")
    juros_ce_itau = 362.80
    saldo_ce_itau = 10313.24
    print(f"  financiamento CAIXA        {TAXA_AM * 100:>6.2f}% a.m.")
    print(
        f"  cheque especial Itau       {100 * juros_ce_itau / saldo_ce_itau:>6.2f}% a.m.  "
        f"(R$ {juros_ce_itau:,.2f} cobrados em 06/08 sobre saldo de R$ {saldo_ce_itau:,.2f})"
    )
    razao = (juros_ce_itau / saldo_ce_itau) / TAXA_AM
    print(f"  o cheque especial custa {razao:.1f}x a taxa do financiamento")
    print()
    print(
        f"  R$ 10.000 no cheque especial evitam  "
        f"R$ {10000 * juros_ce_itau / saldo_ce_itau:>8,.2f}/mes"
    )
    print(f"  R$ 10.000 amortizados no financiamento evitam R$ {10000 * TAXA_AM:>8,.2f}/mes")


if __name__ == "__main__":
    main()
