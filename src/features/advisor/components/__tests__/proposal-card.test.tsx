import { expect, test, vi } from 'vitest'
import { screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { delay, http, HttpResponse } from 'msw'

import { categoriesQueryKey } from '@/hooks/use-categories'
import { advisorKeys } from '@/features/advisor/api/query-keys'
import { ProposalCard } from '@/features/advisor/components/proposal-card'
import type { ConversationDetail, Proposal } from '@/features/advisor/types/advisor'
import { server } from '@/testing/mocks/server'
import { renderWithProviders } from '@/testing/test-utils'

const CONVERSATION_ID = 7

const PENDING: Proposal = {
  id: 3,
  status: 'pending',
  target_category: 'Plano de saúde',
  created_at: '2026-09-26T12:00:00+00:00',
  applied_at: null,
  discarded_at: null,
  undone_at: null,
  undo_skipped: null,
  total_cents: -7500,
  items: [
    {
      transaction_id: 11,
      date: '2026-08-12',
      description: 'Drogaria Raia',
      amount_cents: -5000,
      from_category: 'Farmácia',
      to_category: 'Plano de saúde',
    },
    {
      transaction_id: 12,
      date: '2026-08-03',
      description: null,
      amount_cents: -2500,
      from_category: null,
      to_category: 'Plano de saúde',
    },
  ],
}

const APPLIED: Proposal = { ...PENDING, status: 'applied', applied_at: '2026-09-26T12:05:00+00:00' }

function conversationWith(proposal: Proposal): ConversationDetail {
  return {
    conversation: { id: CONVERSATION_ID, title: 't', created_at: '', updated_at: '' },
    messages: [
      {
        id: 1,
        role: 'assistant',
        text: 'Preparei a mudança.',
        created_at: '',
        provider: 'anthropic',
        tools: ['propose_recategorization'],
        proposals: [proposal],
      },
    ],
  }
}

function renderCard(proposal: Proposal) {
  const rendered = renderWithProviders(
    <ProposalCard conversationId={CONVERSATION_ID} proposal={proposal} />,
  )
  rendered.queryClient.setQueryData(
    advisorKeys.conversation(CONVERSATION_ID),
    conversationWith(proposal),
  )
  return rendered
}

test('lists each transaction with date, amount and current → new category, and the total', () => {
  renderCard(PENDING)

  expect(
    screen.getByRole('heading', { name: 'Mudar 2 lançamentos para Plano de saúde' }),
  ).toBeVisible()
  const rows = within(screen.getByRole('list', { name: 'Lançamentos da proposta' })).getAllByRole(
    'listitem',
  )
  expect(rows).toHaveLength(2)
  expect(within(rows[0]).getByText('Drogaria Raia')).toBeVisible()
  expect(within(rows[0]).getByText('Farmácia → Plano de saúde')).toBeVisible()
  expect(within(rows[0]).getByText('12/08/2026')).toBeVisible()
  expect(within(rows[0]).getByText(/50,00/)).toBeVisible()
  expect(within(rows[1]).getByText('Sem descrição')).toBeVisible()
  expect(within(rows[1]).getByText('Sem categoria → Plano de saúde')).toBeVisible()
  expect(screen.getByText(/75,00/)).toBeVisible()
  expect(screen.getByText('Aguardando você')).toBeVisible()
  expect(screen.getByRole('button', { name: 'Aplicar' })).toBeEnabled()
  expect(screen.getByRole('button', { name: 'Descartar' })).toBeEnabled()
  expect(screen.queryByRole('button', { name: 'Desfazer' })).not.toBeInTheDocument()
})

test('applies once on a double click, refreshes the affected screens and the conversation', async () => {
  let calls = 0
  server.use(
    http.post('/api/advisor/proposals/:id/apply', async () => {
      calls += 1
      await delay(30)
      return HttpResponse.json(APPLIED)
    }),
  )
  const { queryClient } = renderCard(PENDING)
  const invalidate = vi.spyOn(queryClient, 'invalidateQueries')
  const user = userEvent.setup()

  await user.dblClick(screen.getByRole('button', { name: 'Aplicar' }))

  expect(await screen.findByRole('button', { name: 'Aplicando…' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Descartar' })).toBeDisabled()
  await waitFor(() => {
    const cached = queryClient.getQueryData<ConversationDetail>(
      advisorKeys.conversation(CONVERSATION_ID),
    )
    expect(cached?.messages[0]?.proposals[0]?.status).toBe('applied')
  })
  expect(calls).toBe(1)
  expect(invalidate).toHaveBeenCalledWith({ queryKey: ['expenses'] })
  expect(invalidate).toHaveBeenCalledWith({ queryKey: categoriesQueryKey })
})

test('an applied proposal offers undo and says when it was applied', () => {
  renderCard(APPLIED)

  expect(screen.getByText('Aplicada', { selector: 'span' })).toBeVisible()
  expect(screen.getByRole('status')).toHaveTextContent(/^Aplicada em .+\.$/)
  expect(screen.getByRole('button', { name: 'Desfazer' })).toBeEnabled()
  expect(screen.queryByRole('button', { name: 'Aplicar' })).not.toBeInTheDocument()
})

test('an undone proposal tells how many transactions kept a later change', () => {
  renderCard({ ...APPLIED, status: 'undone', undone_at: APPLIED.applied_at, undo_skipped: 1 })

  expect(screen.getByRole('status')).toHaveTextContent(
    '1 lançamento que você mudou depois ficou como estava.',
  )
  expect(screen.queryByRole('button')).not.toBeInTheDocument()
})

test('a discarded proposal says nothing changed and offers no action', () => {
  renderCard({ ...PENDING, status: 'discarded', discarded_at: APPLIED.applied_at })

  expect(screen.getByRole('status')).toHaveTextContent('Nada foi alterado.')
  expect(screen.queryByRole('button')).not.toBeInTheDocument()
})

test('a refused action shows the server reason and keeps the buttons', async () => {
  server.use(
    http.post('/api/advisor/proposals/:id/undo', () =>
      HttpResponse.json({ detail: 'A proposta já foi desfeita.' }, { status: 409 }),
    ),
  )
  renderCard(APPLIED)
  const user = userEvent.setup()

  await user.click(screen.getByRole('button', { name: 'Desfazer' }))

  expect(await screen.findByRole('alert')).toHaveTextContent('A proposta já foi desfeita.')
  expect(screen.getByRole('button', { name: 'Desfazer' })).toBeEnabled()
})
