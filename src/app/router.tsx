import { flushSync } from 'react-dom'
import { createBrowserRouter, RouterProvider } from 'react-router'
import type { RouteObject } from 'react-router'
import { paths } from '@/config/paths'
import { ProtectedRoute } from '@/lib/auth'
import { CategoriesRoute } from '@/app/routes/categories'
import { DashboardRoute } from '@/app/routes/dashboard'
import { ExpensesRoute } from '@/app/routes/expenses'
import { LoginRoute } from '@/app/routes/login'

export const routes: RouteObject[] = [
  { path: paths.login, element: <LoginRoute /> },
  {
    path: paths.dashboard,
    element: (
      <ProtectedRoute>
        <DashboardRoute />
      </ProtectedRoute>
    ),
  },
  {
    path: paths.expenses,
    element: (
      <ProtectedRoute>
        <ExpensesRoute />
      </ProtectedRoute>
    ),
  },
  {
    path: paths.categories,
    element: (
      <ProtectedRoute>
        <CategoriesRoute />
      </ProtectedRoute>
    ),
  },
]

export const router = createBrowserRouter(routes, { basename: '/app/' })

export function AppRouter(): React.JSX.Element {
  return (
    <RouterProvider
      router={router}
      flushSync={(update) => {
        flushSync(update)
      }}
    />
  )
}
