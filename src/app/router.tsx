import { createBrowserRouter, RouterProvider } from 'react-router'
import type { RouteObject } from 'react-router'
import { paths } from '@/config/paths'
import { ProtectedRoute } from '@/lib/auth'
import { DashboardRoute } from '@/app/routes/dashboard'
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
]

export const router = createBrowserRouter(routes, { basename: '/app' })

export function AppRouter(): React.JSX.Element {
  return <RouterProvider router={router} />
}
