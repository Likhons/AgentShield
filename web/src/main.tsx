import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ToastProvider } from './components/Toast'
import { startSmoothScroll } from './lib/motion'
import '@fontsource-variable/plus-jakarta-sans/wght.css'
import '@fontsource-variable/jetbrains-mono/wght.css'
// Hind Siliguri: only the Bangla subset (Latin characters fall through to Plus Jakarta Sans)
import '@fontsource/hind-siliguri/bengali-400.css'
import '@fontsource/hind-siliguri/bengali-500.css'
import '@fontsource/hind-siliguri/bengali-600.css'
import '@fontsource/hind-siliguri/bengali-700.css'
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
