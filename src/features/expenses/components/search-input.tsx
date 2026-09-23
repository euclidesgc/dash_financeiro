import { useCallback, useEffect, useId, useRef, useState } from 'react'
import { Button } from '@/components/ui/button'

const SEARCH_DEBOUNCE_MS = 300

function effectiveTerm(text: string): string | null {
  const trimmed = text.trim()
  return trimmed.length < 2 ? null : trimmed
}

export function SearchInput({
  value,
  onCommit,
}: {
  value: string | null
  onCommit: (text: string) => void
}): React.JSX.Element {
  const id = useId()
  const [draft, setDraft] = useState(value ?? '')
  const lastCommittedRef = useRef<string | null>(value)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const onCommitRef = useRef(onCommit)

  useEffect(() => {
    onCommitRef.current = onCommit
  }, [onCommit])

  const commit = useCallback((text: string): void => {
    if (timerRef.current !== null) {
      clearTimeout(timerRef.current)
      timerRef.current = null
    }
    lastCommittedRef.current = effectiveTerm(text)
    onCommitRef.current(text)
  }, [])

  useEffect(() => {
    if (effectiveTerm(draft) === lastCommittedRef.current) {
      return
    }
    const timer = setTimeout(() => {
      timerRef.current = null
      commit(draft)
    }, SEARCH_DEBOUNCE_MS)
    timerRef.current = timer
    return () => {
      clearTimeout(timer)
      if (timerRef.current === timer) {
        timerRef.current = null
      }
    }
  }, [draft, commit])

  useEffect(() => {
    if (value !== lastCommittedRef.current) {
      lastCommittedRef.current = value
      setDraft(value ?? '')
    }
  }, [value])

  return (
    <form
      role="search"
      className="flex flex-col gap-1"
      onSubmit={(event) => {
        event.preventDefault()
        commit(draft)
      }}
    >
      <label htmlFor={id} className="block text-sm font-medium text-gray-900">
        Buscar
      </label>
      <div className="flex items-center gap-2">
        <input
          type="search"
          id={id}
          value={draft}
          placeholder="Descrição ou recebedor"
          autoComplete="off"
          onChange={(event) => {
            setDraft(event.target.value)
          }}
          className="mt-1 block min-h-10 min-w-48 rounded-md border border-gray-300 px-3 py-2 text-gray-900 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600"
        />
        {draft !== '' && (
          <Button
            type="button"
            variant="secondary"
            aria-label="Limpar busca"
            onClick={() => {
              setDraft('')
              commit('')
            }}
          >
            Limpar
          </Button>
        )}
      </div>
    </form>
  )
}
