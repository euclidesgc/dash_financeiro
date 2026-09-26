import { expect, test } from 'vitest'
import { render, screen } from '@testing-library/react'

import { ChatMessageItem } from '@/features/advisor/components/chat-message-item'
import type { ChatMessage } from '@/features/advisor/types/advisor'

function answer(tools: string[]): ChatMessage {
  return {
    id: 1,
    role: 'assistant',
    text: 'Em agosto: Mercado −R$ 900,00.',
    created_at: '2026-09-26T10:00:00+00:00',
    provider: 'gemini',
    tools,
    proposals: [],
  }
}

function renderItem(message: ChatMessage): void {
  render(
    <ul>
      <ChatMessageItem conversationId={1} message={message} />
    </ul>,
  )
}

test('names the spending summary when the advisor used it', () => {
  renderItem(answer(['spending_summary']))

  expect(screen.getByText('Respondido por Gemini · consultou o resumo de gastos')).toBeVisible()
})

test('names both sources once each when the advisor used both tools', () => {
  renderItem(answer(['search_transactions', 'spending_summary', 'search_transactions']))

  expect(
    screen.getByText('Respondido por Gemini · consultou seus lançamentos e o resumo de gastos'),
  ).toBeVisible()
})

test('names the monthly projection when the advisor used it', () => {
  renderItem(answer(['commitments_by_month']))

  expect(
    screen.getByText(
      'Respondido por Gemini · consultou as parcelas e contas dos próximos meses',
    ),
  ).toBeVisible()
})

test('names the payoff lookup when the advisor used it', () => {
  renderItem(answer(['debt_payoff']))

  expect(
    screen.getByText('Respondido por Gemini · consultou o valor para quitar as dívidas'),
  ).toBeVisible()
})

test('names the liquidity ranking when the advisor used it', () => {
  renderItem(answer(['debts_by_liquidity']))

  expect(
    screen.getByText(
      'Respondido por Gemini · consultou as dívidas que mais liberam dinheiro no mês',
    ),
  ).toBeVisible()
})

test('leaves the note to the provider when no tool was used', () => {
  renderItem(answer([]))

  expect(screen.getByText('Respondido por Gemini')).toBeVisible()
})
