#!/usr/bin/env python3
"""Saldo devedor e custo de quitação do CDC do veículo (Price), a partir da CCB.

Determinístico. O saldo devedor de um CDC é o valor presente das parcelas ainda
não vencidas, descontadas à taxa do contrato — é o que a lei manda o banco
oferecer na quitação antecipada (art. 52 §2º do CDC).
"""

import json
from datetime import date

D = json.load(open("data/manual/cdc_safra_veiculo.json"))
PMT = D["valor_parcela"]
JUROS = D["juros_efetivo_mensal_pct"] / 100
N = D["prazo_meses"]
HOJE = date(2026, 9, 5)


def valor_presente(parcelas: int, pmt: float, taxa: float) -> float:
    return pmt * (1 - (1 + taxa) ** -parcelas) / taxa


def parcelas_vencidas() -> int:
    ano, mes = 2025, 6
    vencidas = 0
    for _ in range(N):
        if date(ano, mes, 11) <= HOJE:
            vencidas += 1
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return vencidas


def main() -> None:
    print(f"contrato CCB {D['ccb']} — {D['garantia'][:38]}")
    print(
        f"principal R$ {D['principal']:,.2f} · {N}x R$ {PMT:,.2f} · "
        f"{D['juros_efetivo_mensal_pct']}% a.m. "
        f"({D['juros_efetivo_anual_pct']}% a.a.) · CET {D['cet_anual_pct']}% a.a."
    )
    print()

    pv60 = valor_presente(N, PMT, JUROS)
    com_tarifas = D["principal"] + D["tarifa_cadastro"] + D["iof_total"] + D["tarifa_avaliacao_bem"]
    print("=== conferencia do contrato ===")
    print(f"  valor presente das 60 parcelas a 1,63% a.m.: R$ {pv60:>10,.2f}")
    print(f"  principal declarado:                         R$ {D['principal']:>10,.2f}")
    print(f"  principal + tarifas + IOF:                   R$ {com_tarifas:>10,.2f}")
    print(
        f"  -> as tarifas e o IOF foram financiados junto: "
        f"diferenca R$ {pv60 - D['principal']:,.2f}"
    )
    print()

    pagas = parcelas_vencidas()
    restantes = N - pagas
    saldo = valor_presente(restantes, PMT, JUROS)
    nominal = restantes * PMT
    print(f"=== POSICAO EM {HOJE.strftime('%d/%m/%Y')} ===")
    print(f"  parcelas pagas:      {pagas} de {N}  (ultima vencida: 11/08/2026)")
    print(
        f"  parcelas restantes:  {restantes}  (de 11/09/2026 a {D['ultimo_vencimento'][8:10]}/"
        f"{D['ultimo_vencimento'][5:7]}/{D['ultimo_vencimento'][:4]})"
    )
    print(f"  a pagar nominal:     R$ {nominal:>10,.2f}")
    print(f"  SALDO DEVEDOR hoje:  R$ {saldo:>10,.2f}   (valor presente a {JUROS * 100:.2f}% a.m.)")
    print(f"  juros ainda embutidos: R$ {nominal - saldo:>8,.2f}")
    print()

    print("=== QUITACAO ANTECIPADA ===")
    print(f"  paga hoje R$ {saldo:,.2f} e deixa de pagar R$ {nominal:,.2f}")
    print(f"  ECONOMIA NOMINAL: R$ {nominal - saldo:,.2f}")
    print("  (o banco e obrigado a dar o desconto proporcional dos juros nao corridos)")
    print()

    print("=== AMORTIZAR PARCIALMENTE (reduzindo prazo, quitando as ultimas parcelas) ===")
    print(f"  {'aporte':>10}  {'parcelas quitadas':>18}  {'juros evitados':>16}")
    for extra in (5000, 10000, 15000, 20000):
        quitadas = 0
        gasto = 0.0
        while quitadas < restantes:
            pos = restantes - quitadas
            custo = PMT / (1 + JUROS) ** pos
            if gasto + custo > extra:
                break
            gasto += custo
            quitadas += 1
        print(f"  R$ {extra:>7,}  {quitadas:>16}  R$ {quitadas * PMT - gasto:>13,.2f}")
    print()

    print("=== ONDE CADA REAL RENDE MAIS, agora com o CDC na conta ===")
    linhas = [
        ("cheque especial Itau", 3.52, "R$ 362,80 sobre R$ 10.313,24 em 06/08/2026"),
        ("CDC do veiculo (Safra)", 1.63, "taxa do contrato"),
        ("financiamento imobiliario", 0.72, "8,9899% a.a. efetivos"),
    ]
    for nome, taxa, obs in linhas:
        print(
            f"  {nome:<28} {taxa:>5.2f}% a.m.  R$ 10.000 economizam "
            f"R$ {10000 * taxa / 100:>7,.2f}/mes   ({obs})"
        )


if __name__ == "__main__":
    main()
