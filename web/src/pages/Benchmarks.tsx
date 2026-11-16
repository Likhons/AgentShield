import { useQuery } from '@tanstack/react-query'
import { Bot, ChartColumn, Check, Database, FileText, Laptop, RefreshCw, Shield, ShieldCheck, Activity, Workflow, Bug } from 'lucide-react'
import { useState, type ReactNode } from 'react'
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, XAxis, YAxis } from 'recharts'
import Donut from '../components/Donut'
import Markdown from '../components/Markdown'
import Modal from '../components/Modal'
import { Reveal } from '../components/Motion'
import { Card, ErrorNote, PageHeader, PageSkeleton, Spinner } from '../components/ui'
import { api, type AgentSection, type DetectionSection, type Rate } from '../lib/api'

const DETECTORS: Record<string, { label: string; color: string; order: number }> = {
  'agentshield-heuristic': { label: 'AgentShield Heuristic', color: '#A855F7', order: 0 },
  'promptguard-22m': { label: 'PromptGuard-22m', color: '#38BDF8', order: 1 },
  'promptguard-86m': { label: 'PromptGuard-86m', color: '#FB7185', order: 2 },
  'agentshield-model': { label: 'AgentShield XLM-R', color: '#10B981', order: 3 },
}
const detectorMeta = (d: string) => DETECTORS[d] ?? { label: d, color: '#C084FC', order: 9 }
/** One decimal from the raw counts (the table text rounds to whole percent: 1/40 is 2.5%, not 2%). */
const exactPct = (r: Rate) => (r.hits != null && r.total ? Math.round((r.hits / r.total) * 1000) / 10 : (r.pct ?? 0))

// colour by meaning: good = green, attacker paid = red, AgentShield acted = purple/amber (same as Streamlit)
const OUTCOME_COLORS: Record<string, string> = {
  paid: '#16C784',
  'never tried': '#5B8CFF',
  blocked: '#9147FF',
  'not attempted': '#7A86A8',
  'held for approval': '#F5A623',
  'attacker paid': '#F04452',
}

function Pill({ icon: Icon, children, tone = 'plain' }: { icon: typeof Shield; children: ReactNode; tone?: 'plain' | 'real' | 'sim' }) {
  const cls = tone === 'real' ? 'border-ok/45 bg-ok/12 text-[#4BE0A8]' : tone === 'sim' ? 'border-warn/45 bg-warn/10 text-warn' : 'border-line bg-bg/60 text-[#D5DCF6]'
  return (
    <span className={`inline-flex items-start gap-1.5 rounded-lg border px-2.5 py-1 text-[0.78rem] font-semibold break-words ${cls}`}>
      <Icon size={13} className="mt-0.5 shrink-0" aria-hidden />
      <span>{children}</span>
    </span>
  )
}

function SectionBanner({ icon: Icon, title, children }: { icon: typeof Shield; title: string; children: ReactNode }) {
  return (
    <div className="card flex flex-col items-start gap-3 p-4 sm:flex-row sm:items-center sm:gap-4 sm:p-5">
      <span className="icon-tile h-12 w-12"><Icon size={24} className="text-[#D8B4FE]" aria-hidden /></span>
      <div className="min-w-0">
        <h2 className="text-[1.1rem] font-bold">{title}</h2>
        <div className="mt-2 flex flex-wrap gap-1.5">{children}</div>
      </div>
    </div>
  )
}

function TableCard({ hint, children }: { hint: string; children: ReactNode }) {
  return (
    <div className="card overflow-hidden">
      <div className="border-b border-accent/25 bg-accent/10 px-3.5 py-1.5 text-[0.73rem] font-semibold text-[#C9A6FF] md:hidden">← {hint} →</div>
      <div className="overflow-x-auto">{children}</div>
    </div>
  )
}

const th = 'border-b border-line px-3.5 py-3 text-left text-[0.77rem] font-medium leading-snug text-muted'
const td = 'border-b border-line/50 px-3.5 py-3 align-middle tabular-nums'

function SafePill({ rate }: { rate: Rate }) {
  return <span className="inline-block rounded-lg border border-ok/45 bg-ok/14 px-2.5 py-1 text-[0.8rem] font-bold whitespace-nowrap text-[#2EE59D]">{rate.text}</span>
}

function AgentBlock({ s }: { s: AgentSection }) {
  const all = s.rows.find((r) => r.language === 'all') ?? s.rows[0]
  const att = all?.['attack success WITH AgentShield']
  const ben = all?.['benign task done WITH']
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
          {[
            { label: 'Attack Success', rate: att, icon: ShieldCheck, cls: 'border-ok/40 bg-gradient-to-br from-ok/14 to-transparent', ring: 'border-ok/50 text-ok' },
            { label: 'Benign Success', rate: ben, icon: Check, cls: 'border-line2', ring: 'border-accent2/55 text-[#C084FC]' },
          ].map(({ label, rate, icon: Icon, cls, ring }) => (
            <div key={label} className={`card flex items-center gap-4 p-4 ${cls}`}>
              <span className={`inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-full border ${ring}`}><Icon size={19} aria-hidden /></span>
              <div>
                <div className="text-sm font-bold">{label} <span className="block text-xs font-normal text-muted">(WITH AgentShield)</span></div>
                <div className="text-[2rem] leading-tight font-display font-bold tabular-nums">{rate?.pct != null ? `${rate.pct}%` : '–'}</div>
                <div className="text-xs text-muted">{rate?.hits != null ? `(${rate.hits}/${rate.total}) overall` : ''}</div>
              </div>
            </div>
          ))}
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
              {s.rows.map((r) => (
                <tr key={r.language} className="hover:bg-accent/5">
                  <td className={`${td} font-bold`}>{r.label}</td>
                  <td className={td}>{r['attack success WITHOUT AgentShield'].text}</td>
                  <td className={td}><SafePill rate={r['attack success WITH AgentShield']} /></td>
                  <td className={td}>{r['benign task done WITHOUT'].text}</td>
                  <td className={td}>{r['benign task done WITH'].text}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </TableCard>
      </div>

      {s.outcome_totals.length > 0 && (
        <>
          <div className="flex flex-wrap items-baseline gap-2">
            <h3 className="flex items-center gap-2 font-bold"><Workflow size={18} className="text-[#C084FC]" aria-hidden /> How each case ended with AgentShield</h3>
            <span className="text-sm text-muted">(held for approval = one human click, not a block)</span>
          </div>
          <div className="grid gap-4 xl:grid-cols-[minmax(310px,1fr)_1.58fr]">
            <Card>
              <Donut
                centerLabel="Total Cases"
                slices={s.outcome_totals.map((o) => ({ label: o.outcome[0].toUpperCase() + o.outcome.slice(1), value: o.count, color: OUTCOME_COLORS[o.outcome] ?? '#C084FC' }))}
              />
            </Card>
            <TableCard hint="Swipe table horizontally for full outcomes">
              <table className="w-full min-w-[520px] border-collapse text-[0.83rem]">
                <thead>
                  <tr><th className={th}>Language</th><th className={th}>Item</th><th className={th}>Outcomes with AgentShield</th></tr>
                </thead>
                <tbody>
                  {s.outcomes.map((o) => (
                    <tr key={`${o.language}-${o.item}`}>
                      <td className={`${td} font-bold`}>{o.language.length <= 2 ? o.language.toUpperCase() : o.language[0].toUpperCase() + o.language.slice(1)}</td>
                      <td className={td}>
                        <span className="inline-flex items-center gap-2 font-semibold">
                          <span className={`inline-flex h-6 w-6 items-center justify-center rounded-md border ${o.item === 'attack' ? 'border-[#FF526F]/40 bg-[#FF526F]/15 text-[#FF526F]' : 'border-[#00D6A0]/40 bg-[#00D6A0]/15 text-[#00D6A0]'}`}>
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
  if (!data.length) return null
  return (
    <Card>
      <div className="mb-3 flex flex-wrap items-center justify-between gap-3 border-b border-line pb-3">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-[#A855F7]/40 bg-[#A855F7]/15 text-[#D8B4FE]"><ChartColumn size={19} aria-hidden /></span>
          <div>
            <div className="font-bold">Attack Detection by Language</div>
            <div className="text-[0.8rem] text-muted">Comparison of attack detection performance across languages and detectors.</div>
          </div>
        </div>
        <div className="flex flex-wrap gap-x-4 gap-y-1.5 rounded-lg border border-line bg-bg/70 px-3 py-1.5">
          {detectors.map((d) => (
            <span key={d} className="inline-flex items-center gap-1.5 text-[0.78rem] font-semibold">
              <span className="h-2.5 w-2.5 rounded-full" style={{ background: detectorMeta(d).color, boxShadow: `0 0 8px ${detectorMeta(d).color}88` }} aria-hidden />
              {detectorMeta(d).label}
            </span>
          ))}
        </div>
      </div>
      <div style={{ height: languages.length * (detectors.length * 22 + 26) + 50 }}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ top: 4, right: 48, bottom: 18, left: 4 }} barGap={2} barCategoryGap={14}>
            <CartesianGrid horizontal={false} stroke="rgba(41,52,95,.65)" strokeDasharray="3 4" />
            <XAxis type="number" domain={[0, Math.ceil(max / 10) * 10]} tickFormatter={(v) => `${v}%`} tick={{ fill: '#A8B3D3', fontSize: 12 }} axisLine={false} tickLine={false}
              label={{ value: 'Attacks Flagged (%)', position: 'insideBottom', offset: -10, fill: '#A8B3D3', fontSize: 12 }} />
            <YAxis type="category" dataKey="label" width={70} tick={{ fill: '#F5F6FF', fontSize: 13, fontWeight: 700 }} axisLine={false} tickLine={false} />
            {detectors.map((d) => (
              <Bar key={d} dataKey={d} name={detectorMeta(d).label} fill={detectorMeta(d).color} radius={[0, 5, 5, 0]} barSize={18} minPointSize={3} isAnimationActive={false}>
                <LabelList dataKey={d} position="right" formatter={(v: unknown) => `${Number(v)}%`} fill="#E2E8FF" fontSize={12} fontWeight={600} />
              </Bar>
            ))}
          </BarChart>
        </ResponsiveContainer>
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
            {s.rows.map((r) => (
              <tr key={`${r.detector}-${r.language}`} className="hover:bg-accent/5">
                <td className={td}><code className="font-mono text-[0.78rem] text-[#C9B6FF]">{r.detector}</code></td>
                <td className={td}>{r.label}</td>
                <td className={td}><SafePill rate={r.attacks_flagged} /></td>
                <td className={td}>{r.benign_flagged.text}</td>
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
