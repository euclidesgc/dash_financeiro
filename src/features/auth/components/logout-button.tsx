import { useNavigate } from 'react-router'
import { Button } from '@/components/ui/button'
import { paths } from '@/config/paths'
import { useLogout } from '@/features/auth/api/logout'

export function LogoutButton(): React.JSX.Element {
  const navigate = useNavigate()
  const logoutMutation = useLogout()

  return (
    <Button
      variant="secondary"
      type="button"
      disabled={logoutMutation.isPending}
      onClick={() => {
        logoutMutation.mutate(undefined, {
          onSuccess: () => {
            void navigate(paths.login, { replace: true })
          },
        })
      }}
    >
      Sair
    </Button>
  )
}
