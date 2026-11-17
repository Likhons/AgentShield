import { useEffect } from 'react'

const MAX_TILT = 3.5 // degrees

/** One pointer listener for the whole app.
 *  - `.spotlight`: the element under the pointer gets --mouse-x/--mouse-y, which its border glow follows.
 *  - `.tilt`: the card leans towards the pointer (--rx/--ry up to ±3.5deg, --ty -3px) and springs back on leave.
 *  Only for a fine pointer that can hover, and never with reduced motion (tilt). */
export function useSpotlight() {
  useEffect(() => {
    if (!window.matchMedia('(hover: hover) and (pointer: fine)').matches) return
    const tiltAllowed = !window.matchMedia('(prefers-reduced-motion: reduce)').matches
    let frame = 0
    let last: PointerEvent | null = null
    let tilted: HTMLElement | null = null

    const release = () => {
      if (!tilted) return
      tilted.classList.remove('is-tilting')
      tilted.style.removeProperty('--rx')
      tilted.style.removeProperty('--ry')
      tilted.style.removeProperty('--ty')
      tilted = null
    }

    const update = () => {
      frame = 0
      if (!last) return
      const target = last.target as Element | null
      const spot = target?.closest?.('.spotlight') as HTMLElement | null
      if (spot) {
        const r = spot.getBoundingClientRect()
        spot.style.setProperty('--mouse-x', `${last.clientX - r.left}px`)
        spot.style.setProperty('--mouse-y', `${last.clientY - r.top}px`)
      }
      const tilt = tiltAllowed ? (target?.closest?.('.tilt') as HTMLElement | null) : null
      if (tilt !== tilted) release()
      if (tilt) {
        const r = tilt.getBoundingClientRect()
        const x = (last.clientX - r.left) / r.width - 0.5
        const y = (last.clientY - r.top) / r.height - 0.5
        tilt.classList.add('is-tilting')
        tilt.style.setProperty('--rx', `${(-y * 2 * MAX_TILT).toFixed(2)}deg`)
        tilt.style.setProperty('--ry', `${(x * 2 * MAX_TILT).toFixed(2)}deg`)
        tilt.style.setProperty('--ty', '-3px')
        tilted = tilt
      }
    }
    const onMove = (e: PointerEvent) => {
      last = e
      if (!frame) frame = requestAnimationFrame(update)
    }
    const onLeave = () => { last = null; release() }
    document.addEventListener('pointermove', onMove, { passive: true })
    document.documentElement.addEventListener('pointerleave', onLeave)
    return () => {
      document.removeEventListener('pointermove', onMove)
      document.documentElement.removeEventListener('pointerleave', onLeave)
      cancelAnimationFrame(frame)
      release()
    }
  }, [])
}
