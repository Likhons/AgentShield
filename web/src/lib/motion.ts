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
  if (lenis || reducedMotion()) return
  lenis = new Lenis({ autoRaf: true, anchors: { offset: -80 }, lerp: 0.12 })
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
