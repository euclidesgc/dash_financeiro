import { useState } from 'react'
import { Alert } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { formatDateTime } from '@/utils/format-date-time'
import { useRemoveConnection } from '@/features/pluggy-connections/api/remove-connection'
import type { PluggyConnection } from '@/features/pluggy-connections/types/pluggy-connection'

export function ConnectionItem({
  connection,
}: {
  connection: PluggyConnection
}): React.JSX.Element {
  const [confirming, setConfirming] = useState(false)
  const removal = useRemoveConnection()
  const shortId = connection.item_id.slice(0, 8)
  const createdAt = formatDateTime(connection.created_at)

  function confirmRemoval(): void {
    if (removal.isPending) return
    removal.mutate({ itemId: connection.item_id })
  }

  return (
    <li className="flex flex-wrap items-start justify-between gap-x-4 gap-y-3 py-3">
      <div className="flex min-w-0 flex-1 flex-col gap-1">
        <span className="min-w-0 truncate font-mono text-sm text-gray-900" title={connection.item_id}>
          {connection.item_id}
        </span>
        {createdAt ? (
          <span className="text-sm text-gray-600 tabular-nums">{`Cadastrada em ${createdAt}`}</span>
        ) : null}
      </div>

      {confirming ? (
        <div className="w-full">
          <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-red-200 bg-red-50 p-3">
            <p className="text-sm text-red-800">{`Remover a conexão ${shortId}…? A atualização deixa de buscar esse banco.`}</p>
            <div className="flex gap-2">
              <Button
                type="button"
                variant="danger"
                disabled={removal.isPending}
                onClick={confirmRemoval}
              >
                {removal.isPending ? 'Removendo…' : 'Confirmar'}
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="bg-white"
                disabled={removal.isPending}
                onClick={() => {
                  setConfirming(false)
                  removal.reset()
                }}
              >
                Cancelar
              </Button>
            </div>
          </div>
          {removal.isError ? (
            <Alert message="Não foi possível remover a conexão. Tente de novo." />
          ) : null}
        </div>
      ) : (
        <Button
          type="button"
          variant="secondary"
          aria-label={`Remover a conexão ${connection.item_id}`}
          onClick={() => {
            setConfirming(true)
          }}
        >
          Remover
        </Button>
      )}
    </li>
  )
}
