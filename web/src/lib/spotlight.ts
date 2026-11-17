import { useEffect } from 'react'

/** One pointer listener for the whole page: the `.spotlight` element under the pointer gets --mouse-x/--mouse-y
 *  (pointer position inside it), which its border glow follows. Only for a fine pointer that can hover. */
export function useSpotlight() {
  useEffect(() => {
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return
    let frame = 0
    let last: PointerEvent | null = null
    const update = () => {
      frame = 0
      if (!last) return
      const el = (last.target as Element | null)?.closest?.('.spotlight') as HTMLElement | null
      if (!el) return
      const r = el.getBoundingClientRect()
      el.style.setProperty('--mouse-x', `${last.clientX - r.left}px`)
      el.style.setProperty('--mouse-y', `${last.clientY - r.top}px`)
    }
    const onMove = (e: PointerEvent) => {
      last = e
      if (!frame) frame = requestAnimationFrame(update)
    }
    document.addEventListener('pointermove', onMove, { passive: true })
    return () => { document.removeEventListener('pointermove', onMove); cancelAnimationFrame(frame) }
  }, [])
}
