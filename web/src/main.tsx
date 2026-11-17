import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import App from './App'
import { ToastProvider } from './components/Toast'
import { startSmoothScroll } from './lib/motion'
import '@fontsource-variable/plus-jakarta-sans/wght.css'
import '@fontsource-variable/jetbrains-mono/wght.css'
// Bricolage Grotesque for headings (weight + optical size), Fraunces italic for the accent words in headlines
import '@fontsource-variable/bricolage-grotesque/opsz.css'
import '@fontsource-variable/fraunces/wght-italic.css'
// Tiro Bangla: Bangla serif for callouts and quotes (its own Latin too, so English words in a callout match)
import '@fontsource/tiro-bangla/400.css'
// Bangla: Baloo Da 2 (text) and Anek Bangla (display), Bengali subset only
import './fonts-bn.css'
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
