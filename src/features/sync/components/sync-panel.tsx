import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { ApiError } from '@/lib/api-client'
import { formatDateTime } from '@/utils/format-date-time'
import { useSyncStatus } from '@/features/sync/api/get-sync-status'
import { useRunSync } from '@/features/sync/api/run-sync'

const GENERIC_MUTATION_ERROR =
  'Não foi possível atualizar. Verifique se o servidor está no ar e tente de novo.'

function mutationErrorMessage(error: unknown): string {
  if (error instanceof ApiError && (error.status === 409 || error.status === 503)) {
    return error.detail
  }
  return GENERIC_MUTATION_ERROR
}

export function SyncPanel(): React.JSX.Element {
  const { data, isPending, isError, refetch } = useSyncStatus()
  const { mutate, isPending: isRunning, isError: isRunError, error: runError } = useRunSync()

  return (
    <>
      <h2 className="mt-8 text-lg font-semibold">Atualização dos registros</h2>

      {isPending ? (
        <p role="status" className="mt-6 text-gray-600">
          Carregando situação da atualização…
        </p>
      ) : isError ? (
        <Alert
          message="Não foi possível carregar a situação da atualização."
          action={{ label: 'Tentar de novo', onClick: () => void refetch() }}
        />
      ) : (
        <SyncStatusPanel data={data} isRunning={isRunning} onRun={() => { mutate() }} />
      )}

      {!isPending && !isError && (isRunning || data.running) ? (
        <p role="status" className="mt-2 text-gray-600">
          Atualização em andamento. Isso pode levar alguns minutos.
        </p>
      ) : null}

      {!isPending && !isError && isRunError ? (
        <Alert message={mutationErrorMessage(runError)} action={{ label: 'Tentar de novo', onClick: () => { mutate() } }} />
      ) : null}

      {!isPending && !isError && !isRunError && data.last_run?.status === 'failed' ? (
        <Alert
          message={`A última atualização falhou: ${data.last_run.reason ?? 'sem detalhe registrado.'}`}
          action={{ label: 'Tentar de novo', onClick: () => { mutate() } }}
        />
      ) : null}
    </>
  )
}

function SyncStatusPanel({
  data,
  isRunning,
  onRun,
}: {
  data: { running: boolean; last_run: { finished_at: string | null; status: 'ok' | 'failed'; reason: string | null } | null }
  isRunning: boolean
  onRun: () => void
}): React.JSX.Element {
  const busy = isRunning || data.running
  const lastRun = data.last_run
  const finishedAt = lastRun ? formatDateTime(lastRun.finished_at) : null

  return (
    <section className="mt-6 flex flex-wrap items-center justify-between gap-4 rounded-md border border-gray-200 p-4">
      <div className="min-w-0">
        <p className="text-gray-900">
          {finishedAt ? `Última atualização: ${finishedAt}` : 'Nunca atualizado'}
        </p>
        {busy ? (
          <span className="mt-1 inline-block rounded-full px-2 py-0.5 text-sm bg-amber-100 text-amber-800">
            Em andamento
          </span>
        ) : lastRun?.status === 'ok' ? (
          <span className="mt-1 inline-block rounded-full px-2 py-0.5 text-sm bg-green-100 text-green-800">
            Concluída
          </span>
        ) : lastRun?.status === 'failed' ? (
          <span className="mt-1 inline-block rounded-full px-2 py-0.5 text-sm bg-red-100 text-red-800">
            Falhou
          </span>
        ) : null}
      </div>
      <Button type="button" onClick={onRun} disabled={busy}>
        {busy ? 'Atualizando…' : 'Atualizar agora'}
      </Button>
    </section>
  )
}
