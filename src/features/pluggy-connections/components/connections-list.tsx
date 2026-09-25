import { Alert } from '@/components/ui/alert'
import { useConnections } from '@/features/pluggy-connections/api/get-connections'
import { ConnectionItem } from '@/features/pluggy-connections/components/connection-item'

export function ConnectionsList(): React.JSX.Element {
  const connections = useConnections()

  function content(): React.JSX.Element {
    if (connections.isPending) {
      return (
        <p role="status" className="mt-6 text-gray-600">
          Carregando conexões…
        </p>
      )
    }
    if (connections.isError) {
      return (
        <Alert
          message="Não foi possível carregar as conexões."
          action={{ label: 'Tentar de novo', onClick: () => void connections.refetch() }}
        />
      )
    }
    if (connections.data.connections.length === 0) {
      return (
        <p className="mt-6 rounded-md border border-dashed border-gray-300 p-6 text-center text-gray-600">
          Nenhuma conexão cadastrada. Cadastre acima a primeira para a atualização buscar seus
          bancos.
        </p>
      )
    }
    return (
      <ul className="mt-6 divide-y divide-gray-200">
        {connections.data.connections.map((connection) => (
          <ConnectionItem key={connection.item_id} connection={connection} />
        ))}
      </ul>
    )
  }

  return (
    <section aria-labelledby="connections-heading">
      <h2 id="connections-heading" className="mt-8 text-lg font-semibold">
        Cadastradas
      </h2>
      {content()}
    </section>
  )
}
