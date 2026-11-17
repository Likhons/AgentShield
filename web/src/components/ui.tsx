import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import { ApiError, type Decision } from '../lib/api'

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`card p-4 sm:p-5 ${className}`}>{children}</section>
}

/** Page title. A short mono path sits above it instead of an icon tile, like a location in a console. */
export function PageHeader({ title, sub, right }: { title: string; sub: ReactNode; right?: ReactNode }) {
  return (
    <header className="mb-6 flex flex-col gap-4 border-b border-line pb-5 sm:flex-row sm:items-end sm:justify-between">
      <div className="min-w-0">
        <div className="font-mono text-[0.72rem] text-muted">
          <span className="text-soft">agentshield</span> / {title.toLowerCase()}
        </div>
        <h1 className="mt-1.5 text-[clamp(1.8rem,2.6vw,2.3rem)] leading-[1.08] font-semibold tracking-[-0.035em]">{title}</h1>
        <p className="mt-2 max-w-[74ch] text-[0.92rem] leading-relaxed text-body">{sub}</p>
      </div>
      {right && <div className="flex shrink-0 flex-wrap gap-2">{right}</div>}
    </header>
  )
}

export interface Stat {
  label: string
  value: ReactNode
  note?: ReactNode
  /** CSS colour for the number */
  tone?: string
  /** takes two columns (custom content such as a split bar) */
  wide?: boolean
}

/** Key numbers in one glass rail split by hairlines: no icon tiles, the numbers carry the page. */
export function StatRail({ items, label }: { items: Stat[]; label: string }) {
  return (
    <dl aria-label={label} className="stat-rail glass grid grid-cols-2 overflow-hidden">
      {items.map((s, i) => (
        <div key={s.label} className={`stat-cell spring-in min-w-0 px-4 py-4 sm:px-5 sm:py-5 ${s.wide ? 'is-wide' : ''}`} style={{ ['--i' as string]: i }}>
          <dt className="text-[0.8rem] text-muted">{s.label}</dt>
          <dd className="mt-2 font-display text-[1.75rem] leading-none font-semibold tracking-[-0.03em] tabular-nums sm:text-[2.1rem]" style={s.tone ? { color: s.tone } : undefined}>
            {s.value}
          </dd>
          {s.note && <dd className="mt-2 text-[0.75rem] leading-snug text-muted">{s.note}</dd>}
        </div>
      ))}
    </dl>
  )
}

export function PanelTitle({ icon: Icon, title, sub, right }: { icon: LucideIcon; title: string; sub?: string; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-start justify-between gap-3">
      <div className="flex items-start gap-2.5">
        <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-line2 bg-accent/15">
          <Icon size={17} className="text-soft" aria-hidden />
        </span>
        <div>
          <h2 className="text-[1.08rem] font-bold leading-snug">{title}</h2>
          {sub && <p className="mt-0.5 text-sm text-muted">{sub}</p>}
        </div>
      </div>
      {right}
    </div>
  )
}

const BADGE: Record<Decision, { label: string; cls: string }> = {
  allow: { label: 'ALLOW', cls: 'bg-ok/15 border-ok/35 text-ok' },
  ask_human: { label: 'ASK', cls: 'bg-warn/15 border-warn/35 text-warn' },
  block: { label: 'BLOCK', cls: 'bg-bad/18 border-bad/35 text-bad-ink' },
}

export function DecisionBadge({ decision }: { decision: Decision }) {
  const b = BADGE[decision]
  return (
    <span className={`inline-flex items-center rounded-md border px-2 py-0.5 text-[0.72rem] font-bold tracking-wider ${b.cls}`}>
      {b.label}
    </span>
  )
}

export function Spinner({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center gap-2.5 py-6 text-sm text-muted">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-accent/30 border-t-accent2" aria-hidden />
      {label}
    </div>
  )
}

export function ErrorNote({ error }: { error: unknown }) {
  const msg = error instanceof Error ? error.message : String(error)
  // an ApiError is a real answer from the server (e.g. "Live mode is off"); anything else means no answer at all
  const fromServer = error instanceof ApiError
  return (
    <div role="alert" className="rounded-xl border border-bad/40 bg-bad/10 px-4 py-3 text-sm text-bad-soft">
      {fromServer ? msg : `Could not reach the API: ${msg}. Is it running? (uvicorn webapi.app:build_app --factory --port 8000)`}
    </div>
  )
}

/** Placeholder block with a slow shimmer, shown while data loads (keeps the layout from jumping). */
export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`skeleton rounded-xl ${className}`} aria-hidden />
}

/** Page-shaped placeholder: a row of stat cards and two content blocks. */
export function PageSkeleton({ cards = 4 }: { cards?: number }) {
  return (
    <div role="status" aria-label="Loading" className="flex flex-col gap-4">
      <div className="grid grid-cols-2 gap-2.5 md:grid-cols-4 md:gap-4">
        {Array.from({ length: cards }, (_, i) => <Skeleton key={i} className="h-24" />)}
      </div>
      <Skeleton className="h-12" />
      <Skeleton className="h-72" />
    </div>
  )
}
