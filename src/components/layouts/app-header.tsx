import type { ReactNode } from 'react'
import { NavLink } from 'react-router'
import { legacyScreens, paths } from '@/config/paths'

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
      <div className="mx-auto flex max-w-2xl flex-wrap items-center justify-between gap-x-4 gap-y-2 p-4">
        <span className="font-medium text-gray-900">dash_financeiro</span>
        <nav
          aria-label="Principal"
          className="order-last flex w-full flex-wrap items-center gap-x-4 gap-y-2 sm:order-none sm:mr-auto sm:w-auto"
        >
          <NavLink to={paths.dashboard} end className={navLinkClassName}>
            Saldos
          </NavLink>
          <NavLink to={paths.expenses} className={navLinkClassName}>
            Gastos
          </NavLink>
          <NavLink to={paths.categories} className={navLinkClassName}>
            Categorias
          </NavLink>
          <NavLink to={paths.connections} className={navLinkClassName}>
            Conexões
          </NavLink>
          <details className="group open:basis-full">
            <summary className="cursor-pointer text-sm font-medium text-gray-600 underline-offset-4 hover:underline">
              Mais telas
            </summary>
            <ul className="mt-2 flex flex-wrap gap-x-4 gap-y-2">
              {legacyScreens.map((screen) => (
                <li key={screen.href}>
                  <a
                    href={screen.href}
                    className="text-sm font-medium text-gray-600 underline-offset-4 hover:underline"
                  >
                    {screen.label}
                  </a>
                </li>
              ))}
            </ul>
          </details>
        </nav>
        <div className="flex min-w-0 items-center gap-4">
          <span className="truncate text-gray-600">{userLogin}</span>
          {action}
        </div>
      </div>
    </header>
  )
}
