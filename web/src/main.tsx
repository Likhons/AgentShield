import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ToastProvider } from './components/Toast'
import { startSmoothScroll } from './lib/motion'
import '@fontsource-variable/instrument-sans/wght.css'
import '@fontsource-variable/bricolage-grotesque/opsz.css'
import '@fontsource-variable/anek-bangla/wght.css'
import '@fontsource-variable/geist-mono/wght.css'
import './index.css'

startSmoothScroll()

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, refetchOnWindowFocus: false, retry: 1 } },
})

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <ToastProvider>
          <App />
        </ToastProvider>
      </BrowserRouter>
    </QueryClientProvider>
  </StrictMode>,
)
