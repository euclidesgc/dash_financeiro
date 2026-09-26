import { useSearchParams } from 'react-router'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'
import { useAdvisorStatus } from '@/features/advisor/api/get-advisor-status'
import { useConversation } from '@/features/advisor/api/get-conversation'
import { useConversations } from '@/features/advisor/api/get-conversations'
import { useSendQuestion } from '@/features/advisor/api/send-question'
import { ChatMessageItem } from '@/features/advisor/components/chat-message-item'
import { MissingKeyNotice } from '@/features/advisor/components/missing-key-notice'
import { QuestionForm } from '@/features/advisor/components/question-form'

const CONVERSATION_PARAM = 'c'
const NEW_CONVERSATION = 'new'
const SEND_FAILED = 'Não foi possível enviar a pergunta. Tente de novo.'

function parseConversationId(value: string | null): number | null {
  return value !== null && /^\d+$/.test(value) ? Number(value) : null
}

function sendErrorMessage(error: unknown): string {
  return error instanceof ApiError && error.status !== 422 && error.detail ? error.detail : SEND_FAILED
}

export function AdvisorChat(): React.JSX.Element {
  const status = useAdvisorStatus()
  const [params, setParams] = useSearchParams()
  const asked = params.get(CONVERSATION_PARAM)
  const available = status.data?.available === true
  const conversations = useConversations({ enabled: available && asked === null })
  const latestId = asked === null ? (conversations.data?.conversations[0]?.id ?? null) : null
  const conversationId = parseConversationId(asked) ?? latestId
  const conversation = useConversation(available ? conversationId : null)
  const send = useSendQuestion()

  if (status.isPending) {
    return (
      <p role="status" className="mt-6 text-gray-600">
        Carregando o consultor…
      </p>
    )
  }
  if (status.isError) {
    return (
      <Alert
        message="Não foi possível verificar o consultor."
        action={{ label: 'Tentar de novo', onClick: () => void status.refetch() }}
      />
    )
  }
  if (!status.data.available) {
    return <MissingKeyNotice message={status.data.message} />
  }

  function startNewConversation(): void {
    send.reset()
    setParams({ [CONVERSATION_PARAM]: NEW_CONVERSATION })
  }

  function ask(text: string, onSent: () => void): void {
    send.mutate(
      { conversationId, text },
      {
        onSuccess: (result) => {
          onSent()
          if (result.conversationId !== conversationId) {
            setParams({ [CONVERSATION_PARAM]: String(result.conversationId) })
          }
        },
      },
    )
  }

  function history(): React.JSX.Element {
    const loading =
      (asked === null && conversations.isPending) ||
      (conversationId !== null && conversation.isPending)
    if (loading) {
      return (
        <p role="status" className="mt-6 text-gray-600">
          Carregando a conversa…
        </p>
      )
    }
    if (conversations.isError || conversation.isError) {
      return (
        <Alert
          message="Não foi possível carregar a conversa."
          action={{
            label: 'Tentar de novo',
            onClick: () => {
              void conversations.refetch()
              void conversation.refetch()
            },
          }}
        />
      )
    }
    const messages = conversation.data?.messages ?? []
    if (messages.length === 0 && !send.isPending) {
      return (
        <p className="mt-6 rounded-md border border-dashed border-gray-300 p-6 text-center text-gray-600">
          Pergunte sobre seus gastos e entradas, por exemplo: “quanto gastei com farmácia em
          agosto?”
        </p>
      )
    }
    return (
      <ol aria-label="Conversa" className="mt-6 flex flex-col gap-4">
        {messages.map((message) => (
          <ChatMessageItem key={message.id} conversationId={conversationId} message={message} />
        ))}
        {send.isPending ? (
          <li className="flex justify-end">
            <div className="max-w-[85%] rounded-md bg-blue-50 px-4 py-3 text-gray-900 whitespace-pre-wrap break-words opacity-70">
              <span className="sr-only">Você: </span>
              {send.variables.text}
            </div>
          </li>
        ) : null}
      </ol>
    )
  }

  const providerName = status.data.provider === 'anthropic' ? 'Anthropic' : 'Gemini'

  return (
    <>
      <div className="mt-6 flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-gray-600">
          Respostas por {providerName}
          {status.data.model ? ` (${status.data.model})` : ''}.
        </p>
        {conversationId !== null ? (
          <Button variant="secondary" onClick={startNewConversation} disabled={send.isPending}>
            Nova conversa
          </Button>
        ) : null}
      </div>
      {history()}
      {send.isPending ? (
        <p role="status" className="mt-4 text-gray-600">
          Consultando suas contas…
        </p>
      ) : null}
      {send.isError ? <Alert message={sendErrorMessage(send.error)} /> : null}
      <QuestionForm isPending={send.isPending} onAsk={ask} />
    </>
  )
}
