export const paths = {
  login: '/login',
  dashboard: '/',
  expenses: '/expenses',
  categories: '/categories',
  connections: '/connections',
} as const

// Reason: these screens live in the server-rendered panel outside the SPA, so
// they are plain hrefs that leave the client router with a full page load.
export const legacyScreens = [
  { href: '/', label: 'Resumo' },
  { href: '/objetivo', label: 'Objetivo' },
  { href: '/dividas', label: 'Dívidas' },
  { href: '/simulador', label: 'Simulador' },
  { href: '/consultor', label: 'Consultor' },
  { href: '/configuracao', label: 'Configuração' },
] as const
