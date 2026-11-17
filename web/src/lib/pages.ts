import type { QueryClient } from '@tanstack/react-query'
import { api } from './api'

// One import function per lazy page, shared by the router and the prefetchers: the browser fetches each chunk
// once, so a page that was warmed in the background opens without a spinner.
export const loaders = {
  playground: () => import('../pages/Playground'),
  benchmarks: () => import('../pages/Benchmarks'),
  audit: () => import('../pages/AuditLog'),
  policies: () => import('../pages/Policies'),
  datasets: () => import('../pages/Datasets'),
  network: () => import('../pages/Network'),
}
type PageKey = keyof typeof loaders

/** Runs when the browser is idle (or after a short delay where requestIdleCallback is missing). */
export function whenIdle(fn: () => void, timeout = 2500) {
  if ('requestIdleCallback' in window) window.requestIdleCallback(fn, { timeout })
  else setTimeout(fn, 1200)
}

/** Loads page chunks in the background. Slow connections and data saver mode are left alone. */
export function prefetchPages(keys: PageKey[] = Object.keys(loaders) as PageKey[]) {
  const conn = (navigator as Navigator & { connection?: { saveData?: boolean; effectiveType?: string } }).connection
  if (conn?.saveData || conn?.effectiveType === '2g' || conn?.effectiveType === 'slow-2g') return
  whenIdle(() => keys.forEach((k) => void loaders[k]().catch(() => {})))
}

/** Warms one page before the click: its chunk and the data it shows first. */
export function warmRoute(path: string, qc: QueryClient) {
  const key = path.replace(/^\//, '') as PageKey
  void loaders[key]?.().catch(() => {})
  const prefetch = (queryKey: string[], queryFn: () => Promise<unknown>) => void qc.prefetchQuery({ queryKey, queryFn })
  if (key === 'playground') { prefetch(['overview'], api.overview); prefetch(['scenarios'], api.scenarios) }
  if (key === 'benchmarks') prefetch(['benchmarks'], api.benchmarks)
  if (key === 'policies') prefetch(['policies'], api.policies)
  if (key === 'datasets') prefetch(['datasets'], api.datasets)
  if (key === 'network') prefetch(['network'], api.network)
}

/** Wakes the API (free hosting sleeps when idle) while the visitor is still reading the landing page. */
export function wakeApi() {
  void fetch('/health', { cache: 'no-store' }).catch(() => {})
}
