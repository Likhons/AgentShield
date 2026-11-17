import { flushSync } from 'react-dom'
import { useSyncExternalStore } from 'react'

// Day / night theme. The choice lives on <html data-theme> and in localStorage; index.html applies it before
// the first paint (no flash). Default is night: the brand look of the demo and the video.

export type Theme = 'dark' | 'light'
const KEY = 'agentshield-theme'
const META = { dark: '#060908', light: '#f3f6f1' }

export const currentTheme = (): Theme => (document.documentElement.dataset.theme === 'light' ? 'light' : 'dark')

function apply(theme: Theme) {
  const root = document.documentElement
  root.dataset.theme = theme
  root.style.colorScheme = theme
  document.querySelector('meta[name="theme-color"]')?.setAttribute('content', META[theme])
  try {
    localStorage.setItem(KEY, theme)
  } catch {
    /* private mode: the choice lasts for this page only */
  }
  window.dispatchEvent(new Event('themechange'))
}

/** Switches the theme. With View Transitions the new theme spreads as a circle from (x, y), e.g. the toggle. */
export function setTheme(theme: Theme, from?: { x: number; y: number }) {
  const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  const doc = document as Document & { startViewTransition?: (cb: () => void) => { ready: Promise<void> } }
  if (!doc.startViewTransition || reduce || !from) {
    apply(theme)
    return
  }
  const { x, y } = from
  const r = Math.hypot(Math.max(x, innerWidth - x), Math.max(y, innerHeight - y))
  const t = doc.startViewTransition(() => flushSync(() => apply(theme)))
  t.ready.then(() => {
    document.documentElement.animate(
      { clipPath: [`circle(0px at ${x}px ${y}px)`, `circle(${r}px at ${x}px ${y}px)`] },
      { duration: 650, easing: 'cubic-bezier(0.16, 1, 0.3, 1)', pseudoElement: '::view-transition-new(root)' },
    )
  }).catch(() => {})
}

const subscribe = (cb: () => void) => {
  window.addEventListener('themechange', cb)
  return () => window.removeEventListener('themechange', cb)
}

export const useTheme = () => useSyncExternalStore(subscribe, currentTheme, () => 'dark' as Theme)
