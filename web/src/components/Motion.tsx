import { useEffect, useState, type ReactNode } from 'react'
import { reducedMotion, useInView } from '../lib/motion'

/** Content rises into place once, the first time it is seen. */
export function Reveal({ children, className = '', delay = 0 }: { children: ReactNode; className?: string; delay?: number }) {
  const [ref, seen] = useInView<HTMLDivElement>(0.2)
  return (
    <div ref={ref} className={`reveal min-w-0 ${seen ? 'is-in' : ''} ${className}`} style={{ transitionDelay: `${delay}s` }}>
      {children}
    </div>
  )
}

/** Counts from 0 to `to` once `run` is true (900 ms, ease-out). */
export function CountUp({ to, run = true, format = (n: number) => String(n) }: { to: number; run?: boolean; format?: (n: number) => string }) {
  const [n, setN] = useState(() => (reducedMotion() ? to : 0))
  useEffect(() => {
    if (!run || reducedMotion()) return
    let frame = 0
    const start = performance.now()
    const tick = (t: number) => {
      const k = Math.min(1, (t - start) / 900)
      setN(Math.round(to * (1 - Math.pow(1 - k, 3))))
      if (k < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [run, to])
  return <>{format(n)}</>
}

/** A KPI string such as "104", "0/20" or "0.6 ms": the leading whole number counts up, the rest stays. */
export function AnimatedValue({ value }: { value: string }) {
  const m = /^(\d+)(.*)$/s.exec(value)
  if (!m || m[1].length > 7) return <>{value}</>
  return (
    <>
      <CountUp to={Number(m[1])} />
      {m[2]}
    </>
  )
}

