import type { LucideIcon } from 'lucide-react'
import type { ReactNode } from 'react'
import type { Decision } from '../lib/api'

export function Card({ children, className = '' }: { children: ReactNode; className?: string }) {
  return <section className={`card p-4 sm:p-5 ${className}`}>{children}</section>
}

export function PageHeader({ icon: Icon, title, sub, right }: { icon: LucideIcon; title: string; sub: string; right?: ReactNode }) {
  return (
    <header className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
      <div className="flex items-center gap-3.5">
        <span className="icon-tile h-12 w-12">
          <Icon size={24} className="text-[#D8B4FE]" aria-hidden />
        </span>
        <div className="min-w-0">
          <h1 className="text-[1.7rem] leading-tight font-extrabold tracking-tight">{title}</h1>
          <p className="mt-0.5 text-sm text-muted">{sub}</p>
        </div>
      </div>
      {right && <div className="flex shrink-0 gap-2">{right}</div>}
    </header>
  )
}

export function PanelTitle({ icon: Icon, title, sub, right }: { icon: LucideIcon; title: string; sub?: string; right?: ReactNode }) {
  return (
    <div className="mb-3 flex items-start justify-between gap-3">
      <div className="flex items-start gap-2.5">
        <span className="mt-0.5 inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-lg border border-line2 bg-accent/15">
          <Icon size={17} className="text-[#C084FC]" aria-hidden />
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
  block: { label: 'BLOCK', cls: 'bg-bad/18 border-bad/35 text-[#FF6B78]' },
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
  return (
    <div role="alert" className="rounded-xl border border-bad/40 bg-bad/10 px-4 py-3 text-sm text-[#FF8A94]">
      Could not load data: {msg}. Is the API running? (uvicorn webapi.app:build_app --factory --port 8000)
    </div>
  )
}
