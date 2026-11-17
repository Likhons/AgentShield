import Lenis from 'lenis'
import 'lenis/dist/lenis.css'
import { useEffect, useRef, useState } from 'react'

// Shared motion helpers. Every effect is skipped (final state shown at once) when the user asks for reduced motion.

export const reducedMotion = () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches

// ---------------------------------------------------------------------------
// smooth scrolling for the whole app (one Lenis instance) + scroll locking for dialogs

let lenis: Lenis | null = null
let locks = 0

export function startSmoothScroll() {
  if (!anchorsBound) {
    anchorsBound = true
    document.addEventListener('click', onAnchorClick)
  }
  if (lenis || reducedMotion()) return
  // in-page links are handled by onAnchorClick (it knows about the fixed header and section padding)
  lenis = new Lenis({ autoRaf: true, lerp: 0.12 })
}

let anchorsBound = false

/** Page position of an element's layout box (transforms such as a reveal's translateY do not count). */
function layoutTop(el: HTMLElement): number {
  let y = 0
  let node: HTMLElement | null = el
  while (node) {
    y += node.offsetTop
    node = node.offsetParent as HTMLElement | null
  }
  return y
}

/** Where to scroll so a section's content (not its padded edge) sits just below the fixed or sticky header. */
export function anchorTarget(el: HTMLElement): number {
  // landing sections keep their padding on an inner .mx-auto wrapper; other targets are used as they are
  const inner = (el.querySelector(':scope > .mx-auto') as HTMLElement | null) ?? null
  const contentTop = inner ? layoutTop(inner) + parseFloat(getComputedStyle(inner).paddingTop) : layoutTop(el)
  const header = [...document.querySelectorAll<HTMLElement>('[data-scroll-header]')].find((h) => h.getClientRects().length > 0)
  const gap = (header ? header.getBoundingClientRect().bottom : 0) + 24
  return Math.max(0, contentTop - gap)
}

export function scrollToAnchor(el: HTMLElement) {
  if (lenis) {
    lenis.resize()
    lenis.scrollTo(anchorTarget(el), { duration: 1.1 })
  } else {
    window.scrollTo({ top: anchorTarget(el), behavior: reducedMotion() ? 'auto' : 'smooth' })
  }
}

function onAnchorClick(e: MouseEvent) {
  if (e.defaultPrevented || e.button !== 0 || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return
  const a = (e.target as Element | null)?.closest?.('a[href^="#"]') as HTMLAnchorElement | null
  const id = a?.getAttribute('href')?.slice(1)
  if (!a || !id || id === 'main') return // the skip link keeps its native jump and focus
  const el = document.getElementById(id)
  if (!el) return
  e.preventDefault()
  scrollToAnchor(el)
  history.replaceState(null, '', `#${id}`)
}

/** Dialogs, drawers and sheets call this so the page behind them does not move. Nested locks are counted.
 *  The root gets overflow 'hidden' (keeps the scroll position; 'clip' would jump to the top). */
export function lockScroll() {
  locks += 1
  if (locks > 1) return
  document.documentElement.style.overflow = 'hidden'
  lenis?.stop()
}

export function unlockScroll() {
  locks = Math.max(0, locks - 1)
  if (locks) return
  document.documentElement.style.overflow = ''
  lenis?.start()
}

export function scrollToTop() {
  if (lenis) lenis.scrollTo(0, { immediate: true })
  else window.scrollTo(0, 0)
}

export function smoothScrollTo(el: HTMLElement, offset = -80) {
  if (lenis) {
    // the target usually just appeared and made the page taller: re-measure first, or the scroll stops short
    lenis.resize()
    lenis.scrollTo(el, { offset, duration: 1.1 })
  }
  else el.scrollIntoView({ behavior: reducedMotion() ? 'auto' : 'smooth', block: 'start' })
}

// ---------------------------------------------------------------------------
// in-view and list stagger (components that animate live in components/Motion.tsx)

/** True once the element has scrolled into view (stays true). */
export function useInView<T extends Element>(threshold = 0.35) {
  const ref = useRef<T>(null)
  // no animation to wait for: show the final state straight away
  const [seen, setSeen] = useState(() => reducedMotion() || !('IntersectionObserver' in window))
  useEffect(() => {
    const el = ref.current
    if (!el || seen) return
    const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { setSeen(true); io.disconnect() } }, { threshold })
    io.observe(el)
    return () => io.disconnect()
  }, [seen, threshold])
  return [ref, seen] as const
}

/** Style for the n-th item of a list that should arrive one after another (capped so long lists do not lag). */
export const stagger = (i: number) => ({ ['--i' as string]: Math.min(i, 12) })
