import { Button } from '@/components/ui/button'

export function Alert({
  message,
  action,
}: {
  message: string
  action?: { label: string; onClick: () => void }
}): React.JSX.Element {
  return (
    <div role="alert" className="mt-6 rounded-md border border-red-200 bg-red-50 p-4">
      <p className="text-red-800">{message}</p>
      {action ? (
        <div className="mt-4">
          <Button variant="danger" onClick={action.onClick}>
            {action.label}
          </Button>
        </div>
      ) : null}
    </div>
  )
}
