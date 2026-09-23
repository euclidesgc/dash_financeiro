import { Component } from 'react'
import type { ErrorInfo, ReactNode } from 'react'
import { Button } from '@/components/ui/button'

interface ErrorBoundaryProps {
  children: ReactNode
}

interface ErrorBoundaryState {
  hasError: boolean
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  state: ErrorBoundaryState = { hasError: false }

  static getDerivedStateFromError(): ErrorBoundaryState {
    return { hasError: true }
  }

  override componentDidCatch(error: Error, info: ErrorInfo): void {
    console.error(error, info)
  }

  override render(): ReactNode {
    if (this.state.hasError) {
      return (
        <div role="alert" className="mt-6 rounded-md border border-red-200 bg-red-50 p-4">
          <p className="text-red-800">Algo deu errado.</p>
          <div className="mt-4">
            <Button
              variant="danger"
              onClick={() => {
                window.location.reload()
              }}
            >
              Recarregar a página
            </Button>
          </div>
        </div>
      )
    }

    return this.props.children
  }
}
