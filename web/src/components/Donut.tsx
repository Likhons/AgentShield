import { useState } from 'react'
import { useInView } from '../lib/motion'
import { CountUp } from './Motion'

export interface Slice {
  label: string
  value: number
  color: string
}

/** Donut + legend. Slices sweep in one after another the first time the chart is seen; pointing at a slice or
 *  its legend row (or tapping the row on a phone) lifts that slice, dims the rest and shows its count in the centre. */
export default function Donut({ slices, centerLabel }: { slices: Slice[]; centerLabel: string }) {
  const [ref, seen] = useInView<HTMLDivElement>(0.3)
  const [active, setActive] = useState<number | null>(null)
  const total = slices.reduce((s, x) => s + x.value, 0)
  const pcts = slices.map((s) => (total ? (s.value / total) * 100 : 0))
  const starts = pcts.map((_, i) => pcts.slice(0, i).reduce((a, b) => a + b, 0))
  const a = active !== null ? slices[active] : null

  return (
    <div ref={ref} className="flex flex-col items-center gap-5 sm:flex-row sm:justify-center" onMouseLeave={() => setActive(null)}>
      <div className="relative h-[168px] w-[168px] shrink-0">
        <svg width="168" height="168" viewBox="0 0 160 160" role="img" aria-label={`${total} ${centerLabel}`} className="overflow-visible">
          <circle cx="80" cy="80" r="58" fill="none" stroke="var(--color-track)" strokeWidth="20" />
          {slices.map((s, i) => (
            <circle
              key={s.label}
              cx="80" cy="80" r="58" fill="none" stroke={s.color} pathLength={100}
              className="donut-slice"
              strokeWidth={active === i ? 25 : 20}
              strokeDasharray={seen ? `${pcts[i].toFixed(2)} ${(100 - pcts[i]).toFixed(2)}` : '0 100'}
              strokeDashoffset={(-starts[i]).toFixed(2)}
              opacity={active === null || active === i ? 1 : 0.28}
              style={{ transitionDelay: seen && active === null ? `${i * 140}ms` : '0ms' }}
              transform="rotate(-90 80 80)"
              onMouseEnter={() => setActive(i)}
            />
          ))}
        </svg>
        <div className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center" aria-live="polite">
          {a ? (
            <>
              <span key={a.label} className="donut-center text-[1.8rem] leading-none font-display font-bold tabular-nums" style={{ color: a.color }}>{a.value}</span>
              <span className="mt-1 max-w-[88px] text-[0.72rem] leading-tight text-muted">{a.label}</span>
            </>
          ) : (
            <>
              <span className="text-[1.8rem] leading-none font-display font-bold tabular-nums"><CountUp to={total} run={seen} /></span>
              <span className="mt-1 text-xs text-muted">{centerLabel}</span>
            </>
          )}
        </div>
      </div>
      <ul className="flex w-full max-w-[290px] flex-col gap-1">
        {slices.map((s, i) => (
          <li key={s.label}>
            <button
              type="button"
              aria-pressed={active === i}
              onMouseEnter={() => setActive(i)}
              onClick={() => setActive((x) => (x === i ? null : i))}
              className={`flex min-h-9 w-full items-center justify-between gap-2 rounded-lg px-2 text-[0.84rem] transition-[background-color,opacity] duration-300 ${
                active === null || active === i ? 'opacity-100' : 'opacity-45'
              } ${active === i ? 'bg-fg/[0.05]' : ''}`}
            >
              <span className="flex items-center gap-2 text-left whitespace-nowrap">
                <span className="h-3 w-3 shrink-0 rounded-[3px] transition-transform duration-300" style={{ background: s.color, transform: active === i ? 'scale(1.25)' : undefined }} aria-hidden />
                {s.label}
              </span>
              <span className="font-bold whitespace-nowrap tabular-nums">
                {s.value} ({total ? ((s.value / total) * 100).toFixed(1) : '0.0'}%)
              </span>
            </button>
          </li>
        ))}
      </ul>
    </div>
  )
}
