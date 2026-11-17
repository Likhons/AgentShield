import { keepPreviousData, useQuery } from '@tanstack/react-query'
import {
  Activity, ChevronLeft, ChevronRight, CircleCheck, CircleHelp, CircleX, Download, FileText, Filter, Layers, Search, Zap,
  type LucideIcon,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import { useSearchParams } from 'react-router-dom'
import AuditDetail from '../components/AuditDetail'
import ToolIcon from '../components/ToolIcon'
import { AnimatedValue } from '../components/Motion'
import { Card, DecisionBadge, ErrorNote, PageHeader, PageSkeleton } from '../components/ui'
import { api, type AuditRecord, type Decision, type Thresholds } from '../lib/api'
import { riskLevel, utcFull } from '../lib/audit'
import { short } from '../lib/format'
import { lockScroll, stagger, unlockScroll } from '../lib/motion'
import { useToast } from '../lib/toast'

const DATE_RANGES: Record<string, number | null> = {
  'All time': null,
  'Last 24 hours': 24,
  'Last 7 days': 24 * 7,
  'Last 30 days': 24 * 30,
}
const PAGE_SIZES = [8, 15, 25, 50]
const DEFAULT_THRESHOLDS: Thresholds = { ask_human_at: 0.4, block_at: 0.75 }

function useDebounced<T>(value: T, ms = 300): T {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

function Kpi({ icon: Icon, tint, label, value, note, wide = false }: { icon: LucideIcon; tint: string; label: string; value: string; note: string; wide?: boolean }) {
  return (
    <div className={`card flex items-center gap-3.5 p-4 ${wide ? 'col-span-2 md:col-span-1' : ''}`}>
      <span className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full" style={{ background: `color-mix(in srgb, ${tint} 13%, transparent)`, border: `1px solid color-mix(in srgb, ${tint} 33%, transparent)` }}>
        <Icon size={20} color={tint} aria-hidden />
      </span>
      <div className="min-w-0">
        <div className="text-[0.8rem] text-muted">{label}</div>
        <div className="text-[1.45rem] leading-tight font-display font-bold tabular-nums"><AnimatedValue value={value} /></div>
        <div className="text-[0.74rem] font-semibold" style={{ color: tint }}>{note}</div>
      </div>
    </div>
  )
}

function pageList(current: number, total: number): (number | '…')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)
  const pages = new Set([1, total, current - 1, current, current + 1].filter((p) => p >= 1 && p <= total))
  const sorted = [...pages].sort((a, b) => a - b)
  const out: (number | '…')[] = []
  sorted.forEach((p, i) => {
    if (i > 0 && p - sorted[i - 1] > 1) out.push('…')
    out.push(p)
  })
  return out
}

function RecordCard({ r, thresholds, onOpen, index }: { r: AuditRecord; thresholds: Thresholds; onOpen: () => void; index: number }) {
  const risk = riskLevel(r.risk_score, thresholds)
  return (
    <li className="stagger-item" style={stagger(index)}>
      <button type="button" onClick={onOpen} className="flex w-full flex-col gap-2 rounded-xl border border-line2/50 bg-card2/50 px-3.5 py-3 text-left transition hover:border-line2">
        <span className="flex w-full items-center justify-between gap-2">
          <span className="flex items-center gap-2 font-bold">
            <span className="inline-flex h-7 w-7 items-center justify-center rounded-lg border border-line2 bg-accent/15"><ToolIcon tool={r.tool_name} size={14} aria-hidden /></span>
            {r.tool_name}
          </span>
          <DecisionBadge decision={r.decision} />
        </span>
        <span className="flex w-full items-center justify-between text-xs">
          <span className="text-muted">{utcFull(r.timestamp)} UTC</span>
          <span className={`font-bold ${risk.text}`}>Risk {r.risk_score.toFixed(2)} · {risk.label}</span>
        </span>
        <code className="w-full truncate rounded-lg border border-line bg-bg px-2.5 py-1.5 font-mono text-[0.78rem] text-soft">{JSON.stringify(r.arguments)}</code>
        <span className="flex w-full items-center justify-between text-xs font-semibold text-soft">
          <span>Tap for full Audit Details & Bangla reason</span>
          <span>View →</span>
        </span>
      </button>
    </li>
  )
}

export default function AuditLog() {
  const toast = useToast()
  const [params, setParams] = useSearchParams()
  const selectedId = params.get('id')
  const [decision, setDecision] = useState<Decision | 'all'>('all')
  const [searchInput, setSearchInput] = useState('')
  const search = useDebounced(searchInput.trim())
  const [range, setRange] = useState('All time')
  const [tool, setTool] = useState('')
  const [taint, setTaint] = useState<'all' | 'tainted' | 'untainted'>('all')
  const [minRisk, setMinRisk] = useState(0)
  const [pageSize, setPageSize] = useState(8)
  const [page, setPage] = useState(1)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const [newest, setNewest] = useState<string | null>(null)
  const filtersRef = useRef<HTMLDivElement>(null)

  const hours = DATE_RANGES[range]
  const since = hours && newest ? new Date(new Date(newest).getTime() - hours * 3600_000).toISOString() : undefined
  const filters = {
    decision: decision === 'all' ? undefined : decision,
    search: search || undefined,
    tool: tool || undefined,
    tainted: taint === 'all' ? undefined : taint === 'tainted',
    min_risk: minRisk > 0 ? minRisk : undefined,
    since,
  }
  const advActive = [tool !== '', taint !== 'all', minRisk > 0, range !== 'All time'].filter(Boolean).length
  const anyActive = advActive > 0 || decision !== 'all' || search !== ''

  // any filter change starts again at page 1
  const filterKey = JSON.stringify([filters, pageSize])
  const [lastKey, setLastKey] = useState(filterKey)
  if (filterKey !== lastKey) {
    setLastKey(filterKey)
    setPage(1)
  }

  const { data, error, isPending, isFetching } = useQuery({
    queryKey: ['audit', 'page', filters, pageSize, page],
    queryFn: () => api.audit({ ...filters, limit: pageSize, offset: (page - 1) * pageSize }),
    placeholderData: keepPreviousData,
  })
  if (data?.newest && data.newest !== newest) setNewest(data.newest)
  const thresholds = data?.thresholds ?? DEFAULT_THRESHOLDS

  const inPage = data?.records.find((r) => r.id === selectedId)
  const single = useQuery({
    queryKey: ['audit', 'record', selectedId],
    queryFn: () => api.auditRecord(selectedId!),
    enabled: !!selectedId && !inPage,
  })
  const selected = inPage ?? single.data ?? null

  const select = (id: string | null) => {
    const next = new URLSearchParams(params)
    if (id) next.set('id', id)
    else next.delete('id')
    setParams(next, { replace: true })
  }

  // phone sheet: lock background scroll and close on Escape
  useEffect(() => {
    if (!selected) return
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && select(null)
    document.addEventListener('keydown', onKey)
    const narrow = window.matchMedia('(max-width: 1279px)').matches
    if (narrow) lockScroll()
    return () => {
      document.removeEventListener('keydown', onKey)
      if (narrow) unlockScroll()
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selected?.id])

  // close the filter panel on outside click
  useEffect(() => {
    if (!filtersOpen) return
    const onDown = (e: MouseEvent) => !filtersRef.current?.contains(e.target as Node) && setFiltersOpen(false)
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [filtersOpen])

  const clearAll = () => {
    setDecision('all')
    setSearchInput('')
    setRange('All time')
    setTool('')
    setTaint('all')
    setMinRisk(0)
  }

  const stats = data?.stats
  const counts = data?.counts
  const total = data?.total ?? 0
  const pages = Math.max(1, Math.ceil(total / pageSize))
  const pct = (n: number, digits = 0) => (stats?.total ? `${((n / stats.total) * 100).toFixed(digits)}% of total` : '0% of total')
  const chips: { id: Decision | 'all'; name: string; count: number }[] = useMemo(
    () => [
      { id: 'all', name: 'All', count: counts?.total ?? 0 },
      { id: 'allow', name: 'Allow', count: counts?.allow ?? 0 },
      { id: 'ask_human', name: 'Ask', count: counts?.ask_human ?? 0 },
      { id: 'block', name: 'Block', count: counts?.block ?? 0 },
    ],
    [counts],
  )

  const headerRight = (
    <>
      <a
        href={api.auditCsvUrl(filters)}
        download
        onClick={() => toast(`Downloading ${data?.total ?? ''} audit records as CSV`.replace('  ', ' '), 'info')}
        className="inline-flex min-h-11 items-center gap-2 rounded-xl border border-line2 bg-card2/80 px-4 text-sm font-semibold hover:bg-accent/12"
      >
        <Download size={16} aria-hidden /> Export (CSV)
      </a>
      <select
        aria-label="Date range"
        value={range}
        onChange={(e) => setRange(e.target.value)}
        className="min-h-11 rounded-xl border border-line2 bg-card2/80 px-3 text-sm"
      >
        {Object.keys(DATE_RANGES).map((k) => <option key={k}>{k}</option>)}
      </select>
    </>
  )

  return (
    <>
      <PageHeader icon={FileText} title="Audit Log" sub="Every AgentShield decision, newest first (SQLite, path from AUDIT_DB_PATH)." right={headerRight} />

      {error && <ErrorNote error={error} />}
      {isPending && <PageSkeleton cards={5} />}

      {stats && (
        <>
          <div className="grid grid-cols-2 gap-2.5 md:grid-cols-3 xl:grid-cols-5 xl:gap-4">
            <Kpi wide icon={Layers} tint="var(--color-soft)" label="Checked Calls" value={String(stats.total)} note="100% SQLite logged" />
            <Kpi icon={CircleCheck} tint="var(--color-ok)" label="Allowed" value={String(stats.allow)} note={pct(stats.allow)} />
            <Kpi icon={CircleHelp} tint="var(--color-warn)" label="Asked Human" value={String(stats.ask_human)} note={pct(stats.ask_human, 1)} />
            <Kpi icon={CircleX} tint="var(--color-bad)" label="Blocked" value={String(stats.block)} note={pct(stats.block)} />
            <Kpi icon={Zap} tint="var(--color-info)" label="Median Latency" value={stats.median_latency_ms == null ? '–' : `${stats.median_latency_ms.toFixed(1)} ms`} note={`LLM judge: ${stats.llm_calls}/${stats.total}`} />
          </div>
          <p className="mt-3 inline-flex items-center gap-2 rounded-lg border border-line bg-card/70 px-3 py-1.5 text-[0.82rem] text-muted">
            <Activity size={14} className="text-soft" aria-hidden />
            LLM judge called for <b className="text-ink">{stats.llm_calls}</b> of <b className="text-ink">{stats.total}</b> checks.
          </p>
        </>
      )}

      {/* toolbar */}
      <div className="my-4 flex flex-col gap-2.5 xl:flex-row xl:items-center">
        <div role="radiogroup" aria-label="Decision filter" className="grid shrink-0 grid-cols-4 gap-1 rounded-xl border border-line bg-card/70 p-1 sm:flex">
          {chips.map((c) => (
            <button
              key={c.id}
              type="button"
              role="radio"
              aria-checked={decision === c.id}
              onClick={() => setDecision(c.id)}
              className={`flex min-h-11 flex-col items-center justify-center rounded-lg px-1 text-[0.84rem] leading-tight font-semibold whitespace-nowrap transition sm:min-h-10 sm:flex-row sm:gap-1 sm:px-3.5 sm:text-sm ${
                decision === c.id ? 'btn-primary' : 'text-body hover:bg-fg/5'
              }`}
            >
              {c.name}
              <span className="text-[0.72rem] font-medium tabular-nums opacity-75 sm:text-sm sm:font-semibold sm:opacity-100">({c.count})</span>
            </button>
          ))}
        </div>
        <div className="flex flex-1 flex-col gap-2.5 sm:flex-row">
        <label className="relative flex-1">
          <span className="sr-only">Search audit log</span>
          <Search size={16} className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted" aria-hidden />
          <input
            type="search"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            placeholder="Search tool, arguments, or decision…"
            className="min-h-11 w-full rounded-xl border border-line bg-card2/80 pr-3 pl-9 text-sm placeholder:text-muted"
          />
        </label>
        <div className="flex gap-2">
          <div ref={filtersRef} className="relative flex-1 sm:flex-none">
            <button
              type="button"
              aria-expanded={filtersOpen}
              onClick={() => setFiltersOpen((o) => !o)}
              className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-line2 bg-card2/80 px-4 text-sm font-semibold"
            >
              <Filter size={15} aria-hidden /> {advActive ? `Filters (${advActive})` : 'Filters'}
            </button>
            {filtersOpen && (
              <div className="card absolute right-0 z-20 mt-2 flex w-[min(320px,calc(100vw-2rem))] flex-col gap-3 p-4">
                <label className="flex flex-col gap-1 text-sm font-semibold">
                  Tool
                  <select value={tool} onChange={(e) => setTool(e.target.value)} className="min-h-10 rounded-lg border border-line bg-card2 px-2.5 font-normal">
                    <option value="">All tools</option>
                    {data?.tools.map((t) => <option key={t}>{t}</option>)}
                  </select>
                </label>
                <label className="flex flex-col gap-1 text-sm font-semibold">
                  Taint status
                  <select value={taint} onChange={(e) => setTaint(e.target.value as typeof taint)} className="min-h-10 rounded-lg border border-line bg-card2 px-2.5 font-normal">
                    <option value="all">All</option>
                    <option value="tainted">Tainted only</option>
                    <option value="untainted">Untainted only</option>
                  </select>
                </label>
                <label className="flex flex-col gap-1 text-sm font-semibold">
                  Minimum risk score: {minRisk.toFixed(2)}
                  <input type="range" min={0} max={1} step={0.05} value={minRisk} onChange={(e) => setMinRisk(Number(e.target.value))} className="h-10 cursor-pointer accent-[var(--color-mark)]" />
                </label>
                <label className="flex flex-col gap-1 text-sm font-semibold">
                  Rows per page
                  <select value={pageSize} onChange={(e) => setPageSize(Number(e.target.value))} className="min-h-10 rounded-lg border border-line bg-card2 px-2.5 font-normal">
                    {PAGE_SIZES.map((n) => <option key={n} value={n}>{n}</option>)}
                  </select>
                </label>
                <button type="button" onClick={clearAll} className="min-h-10 rounded-lg border border-line text-sm font-semibold hover:border-line2">
                  Clear all filters
                </button>
              </div>
            )}
          </div>
          {anyActive && (
            <button type="button" onClick={clearAll} className="min-h-11 rounded-xl border border-line px-4 text-sm font-semibold hover:border-line2">
              Reset
            </button>
          )}
        </div>
        </div>
      </div>

      {data && (
        <div className={`grid items-start gap-4 ${selected ? 'xl:grid-cols-[1.85fr_1fr]' : ''}`}>
          <Card className={`min-w-0 p-2! sm:p-3! transition-opacity ${isFetching ? 'opacity-70' : ''}`}>
            {data.records.length === 0 ? (
              <p className="px-3 py-6 text-sm text-muted">
                No audit events match these filters.{' '}
                {anyActive && <button type="button" onClick={clearAll} className="font-semibold text-soft underline">Clear filters</button>}
              </p>
            ) : (
              <>
                <div className="hidden overflow-x-auto md:block">
                  <table className="w-full border-separate border-spacing-y-1 text-left text-sm">
                    {/* columns drop out as space shrinks; with the detail panel open the panel shows arguments and reason */}
                    <thead className="text-xs text-muted">
                      <tr>
                        <th className="px-3 py-2 font-medium">Time (UTC)</th>
                        <th className="px-3 py-2 font-medium">Tool</th>
                        <th className={`px-3 py-2 font-medium ${selected ? 'hidden min-[1700px]:table-cell' : ''}`}>Arguments</th>
                        <th className="px-3 py-2 font-medium">Risk</th>
                        <th className="px-3 py-2 font-medium">Decision</th>
                        <th className={`hidden px-3 py-2 font-medium ${selected ? 'min-[1880px]:table-cell' : 'xl:table-cell'}`}>Reason</th>
                      </tr>
                    </thead>
                    <tbody>
                      {data.records.map((r, i) => {
                        const risk = riskLevel(r.risk_score, thresholds)
                        const active = r.id === selectedId
                        return (
                          <tr
                            key={r.id}
                            onClick={() => select(r.id)}
                            style={stagger(i)}
                            className={`stagger-item cursor-pointer transition [&>td]:py-2.5 [&>td]:first:rounded-l-lg [&>td]:last:rounded-r-lg ${
                              active ? '[&>td]:bg-accent/18' : '[&>td]:bg-card2/40 hover:[&>td]:bg-accent/8'
                            }`}
                          >
                            <td className="px-3 whitespace-nowrap text-muted">
                              {utcFull(r.timestamp)}
                            </td>
                            <td className="px-3">
                              <button type="button" onClick={(e) => { e.stopPropagation(); select(r.id) }} className="-my-2.5 flex items-center gap-2 py-2.5 font-semibold whitespace-nowrap" aria-label={`Inspect ${r.tool_name} event`}>
                                <ToolIcon tool={r.tool_name} size={14} className="text-soft" aria-hidden /> {r.tool_name}
                              </button>
                            </td>
                            <td className={`max-w-[180px] px-3 xl:max-w-[220px] ${selected ? 'hidden min-[1700px]:table-cell' : ''}`}><code className="block truncate font-mono text-[0.78rem] text-soft">{JSON.stringify(r.arguments)}</code></td>
                            <td className="px-3 whitespace-nowrap"><span className={`rounded-md border px-2 py-0.5 text-xs font-bold ${risk.cls}`}>{r.risk_score.toFixed(2)} · {risk.label}</span></td>
                            <td className="px-3"><DecisionBadge decision={r.decision} /></td>
                            <td className={`hidden px-3 text-muted ${selected ? 'min-[1880px]:table-cell' : 'xl:table-cell'}`}>{short(r.reason_en, selected ? 60 : 90)}</td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                </div>
                <ul className="flex flex-col gap-2.5 md:hidden">
                  {data.records.map((r, i) => (
                    <RecordCard key={r.id} r={r} index={i} thresholds={thresholds} onOpen={() => select(r.id)} />
                  ))}
                </ul>
              </>
            )}

            {/* pagination */}
            <nav aria-label="Pagination" className="mt-2 flex flex-col items-center justify-between gap-2 border-t border-line px-2 pt-3 pb-1 sm:flex-row">
              <span className="text-sm text-muted">
                {total ? `Showing ${(page - 1) * pageSize + 1}–${Math.min(page * pageSize, total)} of ${total}` : 'Showing 0 of 0'}
              </span>
              <div className="flex items-center gap-1">
                <button type="button" aria-label="Previous page" disabled={page <= 1} onClick={() => setPage(page - 1)} className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-line disabled:opacity-35">
                  <ChevronLeft size={16} aria-hidden />
                </button>
                {pageList(page, pages).map((p, i) =>
                  p === '…' ? (
                    <span key={`e${i}`} className="px-1 text-muted">…</span>
                  ) : (
                    <button
                      key={p}
                      type="button"
                      aria-current={p === page ? 'page' : undefined}
                      onClick={() => setPage(p)}
                      className={`h-10 min-w-10 rounded-lg px-2 text-sm font-semibold ${p === page ? 'btn-primary' : 'hover:bg-fg/5'}`}
                    >
                      {p}
                    </button>
                  ),
                )}
                <button type="button" aria-label="Next page" disabled={page >= pages} onClick={() => setPage(page + 1)} className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-line disabled:opacity-35">
                  <ChevronRight size={16} aria-hidden />
                </button>
              </div>
            </nav>
          </Card>

          {/* detail: side panel on wide screens */}
          {selected && (
            <aside key={selected.id} data-lenis-prevent className="card modal-in sticky top-6 hidden max-h-[calc(100dvh-3rem)] min-w-0 overflow-y-auto p-4 xl:block">
              <AuditDetail record={selected} thresholds={thresholds} onClose={() => select(null)} />
            </aside>
          )}
        </div>
      )}

      {/* detail: full-screen sheet on phones and tablets (portal: fixed stays fixed under animated ancestors) */}
      {selected &&
        createPortal(
        <div role="dialog" aria-modal="true" aria-label="Audit details" data-lenis-prevent className="sheet-in fixed inset-0 z-50 overflow-y-auto bg-bg/95 px-4 py-4 backdrop-blur-md xl:hidden">
          <button type="button" onClick={() => select(null)} className="mb-3 inline-flex min-h-11 items-center gap-1.5 rounded-xl border border-line2 bg-accent/18 px-4 text-sm font-semibold">
            ← Back to Audit Log
          </button>
          <AuditDetail record={selected} thresholds={thresholds} onClose={() => select(null)} />
        </div>,
          document.body,
        )}
    </>
  )
}
