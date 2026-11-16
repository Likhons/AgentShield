export interface Slice {
  label: string
  value: number
  color: string
}

/** Donut + legend (same drawing as the Streamlit dashboard: one stroked circle per slice). */
export default function Donut({ slices, centerLabel }: { slices: Slice[]; centerLabel: string }) {
  const total = slices.reduce((s, x) => s + x.value, 0)
  const pcts = slices.map((s) => (total ? (s.value / total) * 100 : 0))
  const starts = pcts.map((_, i) => pcts.slice(0, i).reduce((a, b) => a + b, 0))
  return (
    <div className="flex flex-col items-center gap-5 sm:flex-row sm:justify-center">
      <div className="relative h-[156px] w-[156px] shrink-0">
        <svg width="156" height="156" viewBox="0 0 160 160" role="img" aria-label={`${total} ${centerLabel}`}>
          <circle cx="80" cy="80" r="58" fill="none" stroke="#1E2952" strokeWidth="20" />
          {slices.map((s, i) => (
            <circle key={s.label} cx="80" cy="80" r="58" fill="none" stroke={s.color} strokeWidth="20" pathLength={100}
              strokeDasharray={`${pcts[i].toFixed(2)} ${(100 - pcts[i]).toFixed(2)}`} strokeDashoffset={(-starts[i]).toFixed(2)}
              transform="rotate(-90 80 80)" />
          ))}
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-[1.7rem] leading-none font-extrabold">{total}</span>
          <span className="mt-1 text-xs text-muted">{centerLabel}</span>
        </div>
      </div>
      <ul className="flex w-full max-w-[280px] flex-col gap-2.5">
        {slices.map((s) => (
          <li key={s.label} className="flex items-center justify-between gap-3 text-sm">
            <span className="flex items-center gap-2">
              <span className="h-3 w-3 rounded-[3px]" style={{ background: s.color }} aria-hidden />
              {s.label}
            </span>
            <span className="font-bold tabular-nums">
              {s.value} ({total ? ((s.value / total) * 100).toFixed(1) : '0.0'}%)
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}
