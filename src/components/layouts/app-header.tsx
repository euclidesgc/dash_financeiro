import type { ReactNode } from 'react'
import { NavLink } from 'react-router'
import { paths } from '@/config/paths'

function navLinkClassName({ isActive }: { isActive: boolean }): string {
  const base = 'text-sm font-medium underline-offset-4 hover:underline'
  return isActive ? `${base} text-gray-900 underline` : `${base} text-gray-600`
}

export function AppHeader({
  userLogin,
  action,
}: {
  userLogin?: string
  action?: ReactNode
}): React.JSX.Element {
  return (
    <header className="border-b border-gray-200">
      <div className="mx-auto flex max-w-2xl flex-wrap items-center justify-between gap-4 p-4">
        <div className="flex items-center gap-4">
          <span className="font-medium text-gray-900">dash_financeiro</span>
          <nav aria-label="Principal" className="flex items-center gap-4">
            <NavLink to={paths.dashboard} end className={navLinkClassName}>
              Saldos
            </NavLink>
            <NavLink to={paths.expenses} className={navLinkClassName}>
              Gastos
            </NavLink>
          </nav>
        </div>
        <div className="flex items-center gap-4">
          <span className="text-gray-600">{userLogin}</span>
          {action}
        </div>
      </div>
    </header>
  )
}
