import { expect, test } from 'vitest'
import { screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { delay, http, HttpResponse } from 'msw'

import { AdvisorChat } from '@/features/advisor/components/advisor-chat'
import { FAKE_ADVISOR_ANSWER, fakeAdvisorStatus } from '@/testing/mocks/handlers'
import { server } from '@/testing/mocks/server'
import { renderWithProviders } from '@/testing/test-utils'

const QUESTION = 'quais foram meus gastos com posto em agosto?'

async function ask(text: string): Promise<void> {
  const user = userEvent.setup()
  await user.type(await screen.findByLabelText('Sua pergunta'), text)
  await user.click(screen.getByRole('button', { name: 'Perguntar' }))
}

test('explains how to configure a key when no provider is available', async () => {
  server.use(
    http.get('/api/advisor/status', () =>
      HttpResponse.json({
        available: false,
        provider: null,
        model: null,
        message: 'O consultor precisa de uma chave de IA.',
      }),
    ),
  )

  renderWithProviders(<AdvisorChat />, { route: '/advisor' })

  expect(await screen.findByRole('heading', { name: 'Falta a chave da IA' })).toBeVisible()
  expect(screen.getByText('O consultor precisa de uma chave de IA.')).toBeVisible()
  expect(screen.getByText('ANTHROPIC_API_KEY')).toBeVisible()
  expect(screen.getByRole('link', { name: 'Configuração' })).toHaveAttribute('href', '/configuracao')
  expect(screen.queryByLabelText('Sua pergunta')).not.toBeInTheDocument()
})

test('shows the empty invitation and the answering provider before the first question', async () => {
  renderWithProviders(<AdvisorChat />, { route: '/advisor' })

  expect(await screen.findByText(/Pergunte sobre seus gastos e entradas/)).toBeVisible()
  expect(screen.getByText('Respostas por Anthropic (claude-opus-5).')).toBeVisible()
  expect(screen.queryByRole('button', { name: 'Nova conversa' })).not.toBeInTheDocument()
})

test('sends a question, shows the waiting state and then the answer', async () => {
  server.use(
    http.post('/api/advisor/conversations/:id/messages', async () => {
      await delay(50)
      return undefined
    }),
  )
  renderWithProviders(<AdvisorChat />, { route: '/advisor' })

  await ask(QUESTION)

  expect(await screen.findByText('Consultando suas contas…')).toBeVisible()
  expect(screen.getByRole('button', { name: 'Consultando…' })).toBeDisabled()
  expect(await screen.findByText(FAKE_ADVISOR_ANSWER)).toBeVisible()
  expect(screen.getByText(QUESTION)).toBeVisible()
  expect(
    screen.getByText('Respondido por Anthropic · consultou seus lançamentos'),
  ).toBeVisible()
  expect(screen.getByLabelText('Sua pergunta')).toHaveValue('')
  expect(screen.queryByText('Consultando suas contas…')).not.toBeInTheDocument()
})

test('the latest conversation comes back when the screen opens again', async () => {
  const first = renderWithProviders(<AdvisorChat />, { route: '/advisor' })
  await ask(QUESTION)
  await screen.findByText(FAKE_ADVISOR_ANSWER)
  first.unmount()

  renderWithProviders(<AdvisorChat />, { route: '/advisor' })

  expect(await screen.findByText(FAKE_ADVISOR_ANSWER)).toBeVisible()
  expect(screen.getByText(QUESTION)).toBeVisible()
})

test('"Nova conversa" clears the screen for a fresh conversation', async () => {
  const user = userEvent.setup()
  renderWithProviders(<AdvisorChat />, { route: '/advisor' })
  await ask(QUESTION)
  await screen.findByText(FAKE_ADVISOR_ANSWER)

  await user.click(screen.getByRole('button', { name: 'Nova conversa' }))

  expect(await screen.findByText(/Pergunte sobre seus gastos e entradas/)).toBeVisible()
  expect(screen.queryByText(FAKE_ADVISOR_ANSWER)).not.toBeInTheDocument()
})

test('a provider failure shows the server message and keeps the question typed', async () => {
  server.use(
    http.post('/api/advisor/conversations/:id/messages', () =>
      HttpResponse.json(
        { detail: 'O consultor está indisponível: a chave da Anthropic foi recusada.' },
        { status: 502 },
      ),
    ),
  )
  renderWithProviders(<AdvisorChat />, { route: '/advisor' })

  await ask(QUESTION)

  expect(await screen.findByRole('alert')).toHaveTextContent(
    'O consultor está indisponível: a chave da Anthropic foi recusada.',
  )
  expect(screen.getByLabelText('Sua pergunta')).toHaveValue(QUESTION)
})

test('an empty question is refused before sending', async () => {
  const user = userEvent.setup()
  renderWithProviders(<AdvisorChat />, { route: '/advisor' })

  await user.click(await screen.findByRole('button', { name: 'Perguntar' }))

  expect(await screen.findByText('Escreva a pergunta.')).toBeVisible()
  expect(screen.getByLabelText('Sua pergunta')).toHaveAttribute('aria-invalid', 'true')
})

test('a status failure offers to try again', async () => {
  let calls = 0
  server.use(
    http.get('/api/advisor/status', () => {
      calls += 1
      return calls === 1
        ? HttpResponse.json({ detail: 'erro' }, { status: 500 })
        : HttpResponse.json(fakeAdvisorStatus)
    }),
  )
  const user = userEvent.setup()
  renderWithProviders(<AdvisorChat />, { route: '/advisor' })

  await user.click(await screen.findByRole('button', { name: 'Tentar de novo' }))

  await waitFor(() => {
    expect(screen.getByLabelText('Sua pergunta')).toBeVisible()
  })
})

test('a Gemini answer names Gemini', async () => {
  server.use(
    http.get('/api/advisor/status', () =>
      HttpResponse.json({ ...fakeAdvisorStatus, provider: 'gemini', model: 'gemini-2.5-flash' }),
    ),
  )
  renderWithProviders(<AdvisorChat />, { route: '/advisor' })

  expect(await screen.findByText('Respostas por Gemini (gemini-2.5-flash).')).toBeVisible()
})
