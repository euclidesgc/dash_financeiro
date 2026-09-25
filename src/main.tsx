import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import { AppProvider } from '@/app/provider'
import { AppRouter } from '@/app/router'

// eslint-disable-next-line @typescript-eslint/no-non-null-assertion -- invariante: o index.html é nosso, o elemento #root sempre existe.
createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <AppProvider>
      <AppRouter />
    </AppProvider>
  </StrictMode>,
)
