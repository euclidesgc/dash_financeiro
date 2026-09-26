import type { ChatMessage } from '@/features/advisor/types/advisor'

const PROVIDER_LABELS: Record<string, string> = {
  anthropic: 'Anthropic',
  gemini: 'Gemini',
}

function describeAnswer(message: ChatMessage): string | null {
  const provider = message.provider ? (PROVIDER_LABELS[message.provider] ?? message.provider) : null
  const consulted = message.tools.length > 0 ? 'consultou seus lançamentos' : null
  const parts = [provider ? `Respondido por ${provider}` : null, consulted].filter(Boolean)
  return parts.length > 0 ? parts.join(' · ') : null
}

export function ChatMessageItem({ message }: { message: ChatMessage }): React.JSX.Element {
  if (message.role === 'user') {
    return (
      <li className="flex justify-end">
        <div className="max-w-[85%] rounded-md bg-blue-50 px-4 py-3 text-gray-900 whitespace-pre-wrap break-words">
          <span className="sr-only">Você: </span>
          {message.text}
        </div>
      </li>
    )
  }
  const note = describeAnswer(message)
  return (
    <li className="flex flex-col items-start">
      <div className="max-w-[85%] rounded-md border border-gray-200 px-4 py-3 text-gray-900 whitespace-pre-wrap break-words">
        <span className="sr-only">Consultor: </span>
        {message.text}
      </div>
      {note ? <p className="mt-1 text-xs text-gray-600">{note}</p> : null}
    </li>
  )
}
