import { useQuery } from '@tanstack/react-query'
import { Bot, ChartColumn, Check, Database, FileText, Laptop, RefreshCw, Shield, ShieldCheck, Activity, Workflow, Bug } from 'lucide-react'
import { useEffect, useState, type ReactNode } from 'react'
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, XAxis, YAxis } from 'recharts'
import Donut from '../components/Donut'
import Markdown from '../components/Markdown'
import Modal from '../components/Modal'
import { Reveal } from '../components/Motion'
import { reducedMotion, stagger, useInView } from '../lib/motion'
import { Card, ErrorNote, PageHeader, PageSkeleton, Spinner } from '../components/ui'
import { api, type AgentSection, type DetectionSection, type Rate } from '../lib/api'

const DETECTORS: Record<string, { label: string; color: string; order: number }> = {
  'agentshield-heuristic': { label: 'AgentShield Heuristic', color: 'var(--color-mark)', order: 0 },
  'promptguard-22m': { label: 'PromptGuard-22m', color: 'var(--color-info)', order: 1 },
  'promptguard-86m': { label: 'PromptGuard-86m', color: 'var(--color-bad)', order: 2 },
  'agentshield-model': { label: 'AgentShield XLM-R', color: 'var(--color-ok)', order: 3 },
}
const detectorMeta = (d: string) => DETECTORS[d] ?? { label: d, color: 'var(--color-mark)', order: 9 }
/** One decimal from the raw counts (the table text rounds to whole percent: 1/40 is 2.5%, not 2%). */
const exactPct = (r: Rate) => (r.hits != null && r.total ? Math.round((r.hits / r.total) * 1000) / 10 : (r.pct ?? 0))

// colour by meaning: good = green, attacker paid = red, AgentShield acted = lime/amber
const OUTCOME_COLORS: Record<string, string> = {
  paid: 'var(--color-ok)',
  'never tried': 'var(--color-info)',
  blocked: 'var(--color-mark)',
  'not attempted': 'var(--color-muted)',
  'held for approval': 'var(--color-warn)',
  'attacker paid': 'var(--color-bad)',
}

function Pill({ icon: Icon, children, tone = 'plain' }: { icon: typeof Shield; children: ReactNode; tone?: 'plain' | 'real' | 'sim' }) {
  const cls = tone === 'real' ? 'border-ok/45 bg-ok/12 text-ok-ink' : tone === 'sim' ? 'border-warn/45 bg-warn/10 text-warn' : 'border-line bg-bg/60 text-body'
  return (
    <span className={`inline-flex items-start gap-1.5 rounded-lg border px-2.5 py-1 text-[0.78rem] font-semibold break-words ${cls}`}>
      <Icon size={13} className="mt-0.5 shrink-0" aria-hidden />
      <span>{children}</span>
    </span>
  )
}

function SectionBanner({ icon: Icon, title, children }: { icon: typeof Shield; title: string; children: ReactNode }) {
  return (
    <div className="glass spotlight flex flex-col items-start gap-3 p-4 sm:flex-row sm:items-center sm:gap-4 sm:p-5">
      <span className="icon-tile relative h-12 w-12"><Icon size={24} className="text-soft" aria-hidden /></span>
      <div className="relative min-w-0">
        <h2 className="text-[1.2rem] font-semibold tracking-[-0.02em]">{title}</h2>
        <div className="bm-pills mt-2 flex flex-wrap gap-1.5">{children}</div>
      </div>
    </div>
  )
}

function TableCard({ hint, children }: { hint: string; children: ReactNode }) {
  const [ref, seen] = useInView<HTMLDivElement>(0.15)
  return (
    <div ref={ref} className={`card bm-table overflow-hidden ${seen ? 'is-seen' : ''}`}>
      <div className="border-b border-accent/25 bg-accent/10 px-3.5 py-1.5 text-[0.73rem] font-semibold text-soft md:hidden">← {hint} →</div>
      <div className="overflow-x-auto">{children}</div>
    </div>
  )
}

const th = 'border-b border-line px-3.5 py-3 text-left text-[0.77rem] font-medium leading-snug text-muted'
const td = 'border-b border-line/50 px-3.5 py-3 align-middle tabular-nums'

function SafePill({ rate }: { rate: Rate }) {
  return <span className="bm-pill inline-block rounded-lg border border-ok/45 bg-ok/14 px-2.5 py-1 text-[0.8rem] font-bold whitespace-nowrap text-ok-ink">{rate.text}</span>
}

type Tone = 'bad' | 'ok' | 'mark' | 'warn'
const BAR: Record<Tone, string> = { bad: 'bg-bad', ok: 'bg-ok', mark: 'bg-mark', warn: 'bg-warn' }

/** A rate as text (or pill) with a thin bar under it that fills to the rate once the table is seen. */
function RateCell({ rate, tone, pill = false, row }: { rate: Rate; tone: Tone; pill?: boolean; row: number }) {
  const pct = rate.hits != null && rate.total ? (rate.hits / rate.total) * 100 : (rate.pct ?? 0)
  return (
    <div className="flex flex-col gap-1.5">
      {pill ? <span><SafePill rate={rate} /></span> : <span>{rate.text}</span>}
      <span className="h-[3px] w-full max-w-[9rem] overflow-hidden rounded-full bg-track" aria-hidden>
        <span className={`bm-bar block h-full rounded-full ${BAR[tone]}`} style={{ width: `${pct}%`, ...stagger(row) }} />
      </span>
    </div>
  )
}

/** Eases a number from `from` to `to` (1.3 s) once `run` turns true. */
function Tween({ from, to, run, delay = 0, format }: { from: number; to: number; run: boolean; delay?: number; format: (n: number) => string }) {
  const [v, setV] = useState(() => (reducedMotion() ? to : from))
  useEffect(() => {
    if (!run || reducedMotion()) return
    let frame = 0
    const t0 = performance.now() + delay
    const tick = (t: number) => {
      const k = Math.min(1, Math.max(0, (t - t0) / 1300))
      setV(from + (to - from) * (1 - Math.pow(1 - k, 3)))
      if (k < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)
    return () => cancelAnimationFrame(frame)
  }, [run, from, to, delay])
  return <>{format(v)}</>
}

/** 0-100 % track with the 95% interval as a band and the estimate as a dot. The WITHOUT interval stays as a
 *  dashed ghost; the dot travels from the WITHOUT estimate to the WITH estimate. */
function CiStrip({ before, after, tone, seen }: { before?: Rate; after?: Rate; tone: Tone; seen: boolean }) {
  if (!after?.ci || after.pct == null) return null
  const [lo, hi] = after.ci
  const from = before?.pct ?? after.pct
  const origin = hi > lo ? ((after.pct - lo) / (hi - lo)) * 100 : 50
  return (
    <div className="relative mt-4">
      <div className="relative h-5" aria-hidden>
        <span className="absolute inset-x-0 top-1/2 h-[3px] -translate-y-1/2 rounded-full bg-track" />
        {before?.ci && (
          <span className="absolute top-1/2 h-[9px] -translate-y-1/2 rounded-full border border-dashed border-fg/30"
            style={{ left: `${before.ci[0]}%`, width: `${Math.max(1, before.ci[1] - before.ci[0])}%` }} />
        )}
        <span className={`ci-band absolute top-1/2 h-[7px] -translate-y-1/2 rounded-full ${BAR[tone]} ${seen ? 'is-in' : ''}`}
          style={{ left: `${lo}%`, width: `${Math.max(1, hi - lo)}%`, transformOrigin: `${origin}% 50%` }} />
        <span className={`ci-dot absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-card ${BAR[tone]}`}
          style={{ left: `${seen ? after.pct : from}%` }} />
      </div>
      <div className="mt-1 flex justify-between gap-2 font-mono text-[0.66rem] text-muted">
        <span>0%</span>
        <span className="text-center">95% CI {lo}–{hi}%{before?.ci ? ` · without ${before.ci[0]}–${before.ci[1]}%` : ''}</span>
        <span>100%</span>
      </div>
    </div>
  )
}

/** Headline rate WITH AgentShield: the big number eases from the WITHOUT value to the WITH value. */
function ShiftStat({ label, before, after, icon: Icon, tone, index }: { label: string; before?: Rate; after?: Rate; icon: typeof Shield; tone: Tone; index: number }) {
  const [ref, seen] = useInView<HTMLDivElement>(0.4)
  const delta = before?.pct != null && after?.pct != null ? after.pct - before.pct : null
  const ring = tone === 'ok' ? 'border-ok/50 text-ok-ink bg-ok/10' : 'border-accent2/55 text-soft bg-accent/10'
  return (
    <div ref={ref} style={{ ['--i' as string]: index }} className="spring-in">
      <div className={`glass spotlight h-full p-4 sm:p-5 ${tone === 'ok' ? 'border-ok/35!' : ''}`}>
        <div className="relative flex items-start gap-4">
          <span className={`inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full border ${ring}`}><Icon size={19} aria-hidden /></span>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="text-sm font-bold">{label} <span className="block text-xs font-normal text-muted">(WITH AgentShield)</span></div>
              {delta !== null && (
                <span className={`bm-delta rounded-full border px-2 py-0.5 font-mono text-[0.7rem] font-bold tabular-nums ${seen ? 'is-in' : ''} ${
                  delta < 0 ? 'border-ok/40 bg-ok/10 text-ok-ink' : delta > 0 ? 'border-warn/40 bg-warn/10 text-warn-ink' : 'border-fg/12 bg-fg/[0.04] text-muted'
                }`}>
                  {delta === 0 ? 'unchanged' : `${delta > 0 ? '+' : '−'}${Math.abs(delta)} pts`}
                </span>
              )}
            </div>
            <div className="mt-1 font-display text-[2.4rem] leading-none font-semibold tracking-[-0.03em] tabular-nums">
              {after?.pct != null ? <Tween from={before?.pct ?? 0} to={after.pct} run={seen} delay={index * 120 + 150} format={(n) => `${Math.round(n)}%`} /> : '–'}
            </div>
            <div className="mt-1.5 text-xs text-muted">
              {after?.hits != null ? `${after.hits}/${after.total} overall` : ''}
              {before?.pct != null && <> · without <span className="line-through decoration-fg/40">{before.pct}%</span> ({before.hits}/{before.total})</>}
            </div>
          </div>
        </div>
        <CiStrip before={before} after={after} tone={tone} seen={seen} />
      </div>
    </div>
  )
}

function AgentBlock({ s }: { s: AgentSection }) {
  const all = s.rows.find((r) => r.language === 'all') ?? s.rows[0]
  const att = all?.['attack success WITH AgentShield']
  const attBefore = all?.['attack success WITHOUT AgentShield']
  const ben = all?.['benign task done WITH']
  const benBefore = all?.['benign task done WITHOUT']
  const real = s.provider !== 'mock'
  return (
    <section className="flex flex-col gap-4">
      <SectionBanner icon={Bot} title={s.title}>
        <Pill icon={FileText}>Source: {s.source}</Pill>
        <Pill icon={Laptop} tone={real ? 'real' : 'sim'}>Provider: {s.provider}{s.note ? ` (${s.note})` : ''}</Pill>
        <Pill icon={Shield}>Detector: {s.detector}</Pill>
        <Pill icon={RefreshCw}>Runs per item: {s.runs}</Pill>
      </SectionBanner>

      <div className="grid gap-4 xl:grid-cols-[minmax(260px,0.8fr)_2fr]">
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-1">
          <ShiftStat index={0} label="Attack Success" before={attBefore} after={att} icon={ShieldCheck} tone="ok" />
          <ShiftStat index={1} label="Benign Success" before={benBefore} after={ben} icon={Check} tone="mark" />
        </div>
        <TableCard hint="Swipe table horizontally for 95% CI & all columns">
          <table className="w-full min-w-[620px] border-collapse text-[0.83rem]">
            <thead>
              <tr>
                <th className={th}>Language</th>
                <th className={th}>Attack success<br />WITHOUT AgentShield</th>
                <th className={th}>Attack success<br />WITH AgentShield</th>
                <th className={th}>Benign task done<br />WITHOUT</th>
                <th className={th}>Benign task done<br />WITH</th>
              </tr>
            </thead>
            <tbody>
              {s.rows.map((r, i) => (
                <tr key={r.language} className="bm-row transition-colors hover:bg-accent/5" style={stagger(i)}>
                  <td className={`${td} font-bold`}>{r.label}</td>
                  <td className={td}><RateCell rate={r['attack success WITHOUT AgentShield']} tone="bad" row={i} /></td>
                  <td className={td}><RateCell rate={r['attack success WITH AgentShield']} tone="ok" pill row={i} /></td>
                  <td className={td}><RateCell rate={r['benign task done WITHOUT']} tone="mark" row={i} /></td>
                  <td className={td}><RateCell rate={r['benign task done WITH']} tone="mark" row={i} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableCard>
      </div>

      {s.outcome_totals.length > 0 && (
        <>
          <div className="flex flex-wrap items-baseline gap-2">
            <h3 className="flex items-center gap-2 font-bold"><Workflow size={18} className="text-soft" aria-hidden /> How each case ended with AgentShield</h3>
            <span className="text-sm text-muted">(held for approval = one human click, not a block)</span>
          </div>
          <div className="grid gap-4 xl:grid-cols-[minmax(310px,1fr)_1.58fr]">
            <Card>
              <Donut
                centerLabel="Total Cases"
                slices={s.outcome_totals.map((o) => ({ label: o.outcome[0].toUpperCase() + o.outcome.slice(1), value: o.count, color: OUTCOME_COLORS[o.outcome] ?? 'var(--color-mark)' }))}
              />
            </Card>
            <TableCard hint="Swipe table horizontally for full outcomes">
              <table className="w-full min-w-[520px] border-collapse text-[0.83rem]">
                <thead>
                  <tr><th className={th}>Language</th><th className={th}>Item</th><th className={th}>Outcomes with AgentShield</th></tr>
                </thead>
                <tbody>
                  {s.outcomes.map((o, i) => (
                    <tr key={`${o.language}-${o.item}`} className="bm-row transition-colors hover:bg-accent/5" style={stagger(i)}>
                      <td className={`${td} font-bold`}>{o.language.length <= 2 ? o.language.toUpperCase() : o.language[0].toUpperCase() + o.language.slice(1)}</td>
                      <td className={td}>
                        <span className="inline-flex items-center gap-2 font-semibold">
                          <span className={`inline-flex h-6 w-6 items-center justify-center rounded-md border ${o.item === 'attack' ? 'border-bad/40 bg-bad/15 text-bad-ink' : 'border-ok/40 bg-ok/15 text-ok-ink'}`}>
                            {o.item === 'attack' ? <Bug size={13} aria-hidden /> : <Check size={13} aria-hidden />}
                          </span>
                          {o.item}
                        </span>
                      </td>
                      <td className={td}>{o['outcomes with AgentShield']}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </TableCard>
          </div>
        </>
      )}
    </section>
  )
}

function DetectionChart({ s }: { s: DetectionSection }) {
  const rows = s.rows.filter((r) => r.language !== 'all' && r.attacks_flagged.pct != null)
  const detectors = [...new Set(rows.map((r) => r.detector))].sort((a, b) => detectorMeta(a).order - detectorMeta(b).order)
  // same order as the tables: banglish, bn, en
  const languages = [...new Set([...rows].sort((x, y) => x.language.localeCompare(y.language)).map((r) => r.label))]
  const data = languages.map((label) => {
    const point: Record<string, string | number> = { label }
    for (const r of rows.filter((x) => x.label === label)) point[r.detector] = exactPct(r.attacks_flagged)
    return point
  })
  const max = Math.max(10, ...rows.map((r) => exactPct(r.attacks_flagged)))
  // mount the chart when it scrolls into view, so its bars grow while someone is looking
  const [chartRef, seen] = useInView<HTMLDivElement>(0.25)
  const [focus, setFocus] = useState<string | null>(null)
  const animate = !reducedMotion()
  if (!data.length) return null
  return (
    <Card>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-accent2/40 bg-accent/15 text-soft"><ChartColumn size={19} aria-hidden /></span>
          <div>
            <div className="font-bold">Attack Detection by Language</div>
            <div className="text-[0.8rem] text-muted">Comparison of attack detection performance across languages and detectors.</div>
          </div>
        </div>
        <div className="flex flex-wrap gap-1 rounded-lg border border-line bg-bg/70 p-1" onMouseLeave={() => setFocus(null)}>
          {detectors.map((d, i) => (
            <button key={d} type="button" aria-pressed={focus === d}
              onMouseEnter={() => setFocus(d)} onClick={() => setFocus((x) => (x === d ? null : d))}
              style={stagger(i)}
              className={`stagger-item inline-flex min-h-8 items-center gap-1.5 rounded-md px-2 text-[0.78rem] font-semibold transition-[opacity,background-color] duration-300 ${
                focus && focus !== d ? 'opacity-40' : 'opacity-100'
              } ${focus === d ? 'bg-fg/[0.06]' : ''}`}>
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: detectorMeta(d).color, boxShadow: `0 0 8px color-mix(in srgb, ${detectorMeta(d).color} 53%, transparent)` }} aria-hidden />
              {detectorMeta(d).label}
            </button>
          ))}
        </div>
      </div>
      <div ref={chartRef} style={{ height: languages.length * (detectors.length * 22 + 26) + 50 }}>
        {seen && <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, bottom: 18, left: 4 }} barGap={2} barCategoryGap={14}>
            <CartesianGrid horizontal={false} stroke="var(--color-line2)" strokeDasharray="3 4" />
            <XAxis type="number" domain={[0, Math.ceil(max / 10) * 10]} tickFormatter={(v) => `${v}%`} tick={{ fill: 'var(--color-muted)', fontSize: 12 }} axisLine={false} tickLine={false}
              label={{ value: 'Attacks Flagged (%)', position: 'insideBottom', offset: -10, fill: 'var(--color-muted)', fontSize: 12 }} />
            <YAxis type="category" dataKey="label" width={70} tick={{ fill: 'var(--color-ink)', fontSize: 13, fontWeight: 700 }} axisLine={false} tickLine={false} />
            {detectors.map((d, i) => (
              <Bar key={d} dataKey={d} name={detectorMeta(d).label} fill={detectorMeta(d).color} radius={[0, 5, 5, 0]} barSize={18} minPointSize={3}
                fillOpacity={focus && focus !== d ? 0.18 : 1} className="bm-chart-bar"
                onMouseEnter={() => setFocus(d)} onMouseLeave={() => setFocus(null)}
                isAnimationActive={animate} animationBegin={i * 160} animationDuration={1000} animationEasing="ease-out">
                <LabelList dataKey={d} position="right" formatter={(v: unknown) => `${Number(v)}%`} fill="var(--color-body)" fontSize={12} fontWeight={600}
                  opacity={focus && focus !== d ? 0.25 : 1} />
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>}
      </div>
    </Card>
  )
}

function DetectionBlock({ s }: { s: DetectionSection }) {
  return (
    <section className="flex flex-col gap-4">
      <SectionBanner icon={ShieldCheck} title={s.title}>
        <Pill icon={FileText}>Source: {s.source}</Pill>
        <Pill icon={Database}>Dataset: {s.dataset}</Pill>
        <Pill icon={Activity}>{s.note}</Pill>
      </SectionBanner>
      <TableCard hint="Swipe table horizontally for all detector metrics">
        <table className="w-full min-w-[620px] border-collapse text-[0.83rem]">
          <thead>
            <tr><th className={th}>Detector</th><th className={th}>Language</th><th className={th}>Attacks Flagged</th><th className={th}>Benign Flagged (False Positive)</th></tr>
          </thead>
          <tbody>
            {s.rows.map((r, i) => (
              <tr key={`${r.detector}-${r.language}`} className="bm-row transition-colors hover:bg-accent/5" style={stagger(i)}>
                <td className={td}><code className="font-mono text-[0.78rem] whitespace-nowrap text-soft">{r.detector}</code></td>
                <td className={td}>{r.label}</td>
                <td className={td}><RateCell rate={r.attacks_flagged} tone="mark" pill row={i} /></td>
                <td className={td}><RateCell rate={r.benign_flagged} tone="warn" row={i} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </TableCard>
      <DetectionChart s={s} />
    </section>
  )
}

export default function Benchmarks() {
  const { data, error, isPending } = useQuery({ queryKey: ['benchmarks'], queryFn: api.benchmarks })
  const [docOpen, setDocOpen] = useState(false)
  const doc = useQuery({ queryKey: ['doc', 'results'], queryFn: () => api.doc('results'), enabled: docOpen })

  return (
    <>
      <PageHeader
        icon={ChartColumn}
        title="Benchmarks"
        sub="Numbers come only from saved runs in benchmark/results/. Small samples: read the 95% intervals. Full write-up with caveats: docs/results.md."
        right={
          <button type="button" onClick={() => setDocOpen(true)} className="inline-flex min-h-11 w-full items-center justify-center gap-2 rounded-xl border border-line2 bg-card2/80 px-4 text-sm font-semibold hover:bg-accent/12 sm:w-auto">
            <FileText size={16} aria-hidden /> docs/results.md
          </button>
        }
      />
      {isPending && <PageSkeleton cards={2} />}
      {error && <ErrorNote error={error} />}
      <div className="flex flex-col gap-10">
        {data?.sections.map((s) => (
          <Reveal key={s.title}>{s.kind === 'agent' ? <AgentBlock s={s} /> : <DetectionBlock s={s} />}</Reveal>
        ))}
      </div>
      {docOpen && (
        <Modal title="docs/results.md" onClose={() => setDocOpen(false)} wide>
          {doc.isPending && <Spinner />}
          {doc.error && <ErrorNote error={doc.error} />}
          {doc.data && <Markdown text={doc.data.markdown} />}
        </Modal>
      )}
    </>
  )
}
