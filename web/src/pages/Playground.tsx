import { keepPreviousData, useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { CircleCheck, CircleHelp, Hourglass, MailWarning, ShieldCheck, ShieldX, Zap, type LucideIcon } from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import AuditDrawer from '../components/AuditDrawer'
import { AnimatedValue } from '../components/Motion'
import RunResultView from '../components/RunResultView'
import { DecisionBadge, ErrorNote, PageHeader, Skeleton, StatRail } from '../components/ui'
import {
  api, type AuditPage, type AuditRecord, type CheckResult, type Decision, type RunMode, type RunResult, type Scenario, type Step,
  type Thresholds, type Verdict,
} from '../lib/api'
import { short, taka } from '../lib/format'
import { reducedMotion, smoothScrollTo } from '../lib/motion'
import { useToast } from '../lib/toast'

// Every number on this page comes from the API: /api/overview, /api/audit, and the run itself.

const DECISION_TONE: Record<Decision, { bar: string; text: string; glow: string; label: string }> = {
  allow: { bar: 'bg-ok', text: 'text-ok-ink', glow: 'rgb(95 207 142 / 0.45)', label: 'ALLOW' },
  ask_human: { bar: 'bg-warn', text: 'text-warn-ink', glow: 'rgb(242 181 68 / 0.45)', label: 'ASK HUMAN' },
  block: { bar: 'bg-bad', text: 'text-bad-ink', glow: 'rgb(242 104 90 / 0.5)', label: 'BLOCK' },
}

/** A bar that loads: fills to `value` (0..1) with a flowing light; `busy` shows a scanning pulse instead. */
function FlowBar({ value, tone, busy = false, className = 'h-1.5' }: { value: number; tone: string; busy?: boolean; className?: string }) {
  return (
    <div className={`flow-bar ${busy ? 'is-busy' : ''} ${className}`} aria-hidden>
      {!busy && <div className={`flow-fill ${tone}`} style={{ transform: `scaleX(${Math.max(0, Math.min(1, value))})` }} />}
    </div>
  )
}

// ---------------------------------------------------------------------------
// hero

// ---------------------------------------------------------------------------
// key numbers

const todayUtc = () => `${new Date().toISOString().slice(0, 10)}T00:00:00+00:00`

function PlaygroundStats() {
  const { data } = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  // BLOCK decisions in the audit log since 00:00 UTC (runs on this page add to it)
  const blocked = useQuery({ queryKey: ['audit', 'blocked-today'], queryFn: () => api.audit({ decision: 'block', since: todayUtc(), limit: 1 }) })
  if (!data) return <Skeleton className="h-[118px]" />
  const real = data.real_llm
  const langs = Object.keys(data.attack_samples.by_language).length
  const blockedTotal = blocked.data?.stats.block
  return (
    <StatRail
      label="Key numbers"
      items={[
        {
          label: 'Blocked today',
          value: blocked.data ? <AnimatedValue value={String(blocked.data.total)} /> : '–',
          tone: 'var(--color-bad-ink)',
          note: blockedTotal !== undefined ? `since 00:00 UTC · ${blockedTotal} in the whole log` : 'from the audit log',
        },
        {
          label: 'Money sent to attackers, real model',
          value: real ? <><AnimatedValue value={String(real.with.hits)} /><span className="text-muted">/{real.with.total}</span></> : '–',
          tone: 'var(--color-ok-ink)',
          note: real ? `with AgentShield · ${real.without.hits}/${real.without.total} without` : 'no real-model run yet',
        },
        {
          label: 'Checks before each tool call',
          value: <AnimatedValue value={String(data.checks.length)} />,
          note: data.checks.join(' · '),
        },
        { label: 'Languages', value: <AnimatedValue value={String(langs)} />, note: 'Bangla · Banglish · English' },
      ]}
    />
  )
}

// ---------------------------------------------------------------------------
// shared bits for the studio (runner, how it works, pipeline, recent evaluations)

const MODES: { id: RunMode; label: string; caption: string }[] = [
  { id: 'mock', label: 'Offline', caption: 'Simulated naive agent. Works offline.' },
  { id: 'groq', label: 'Live (Groq)', caption: 'Real model via Groq, same tools. Can take up to a minute.' },
  { id: 'recorded', label: 'Recorded run', caption: 'Instant replay of a saved real run.' },
]

const DECISION_BN: Record<Decision, string> = { allow: 'অনুমোদিত', ask_human: 'অনুমতি দরকার', block: 'আটকানো' }
const DECISION_WORD: Record<Decision, string> = { allow: 'ALLOWED', ask_human: 'ASK HUMAN', block: 'BLOCKED' }
const SOURCE_LABEL: Record<string, string> = { 'tool:email': 'email', 'tool:web': 'web page', 'tool:file': 'file' }

/** Score colour by the engine's own bands (ask from 0.4, block from 0.75, sent by the API). */
function scoreTone(score: number | null, t: Thresholds) {
  if (score === null) return { badge: 'border-fg/10 bg-fg/5 text-muted', bar: 'bg-muted', card: 'border-tile-line' }
  if (score >= t.block_at) return { badge: 'border-bad/40 bg-bad/12 text-bad-ink', bar: 'bg-bad', card: 'border-bad/35' }
  if (score >= t.ask_human_at) return { badge: 'border-warn/40 bg-warn/12 text-warn-ink', bar: 'bg-warn', card: 'border-warn/35' }
  return { badge: 'border-ok/40 bg-ok/12 text-ok-ink', bar: 'bg-ok', card: 'border-ok/30' }
}

const DEFAULT_T: Thresholds = { ask_human_at: 0.4, block_at: 0.75 }

/** "send_money(01000000666, 4500)" from a tool name and its arguments. */
const callText = (tool: string, args: Record<string, unknown>) =>
  `${tool}(${Object.values(args).map((v) => (typeof v === 'string' || typeof v === 'number' ? String(v) : JSON.stringify(v))).join(', ')})`

/** HH:MM:SS in UTC. */
const clock = (iso: string) => new Date(iso).toISOString().slice(11, 19)


// ---------------------------------------------------------------------------
// scenario runner

function RunCard({ scenarios, scenario, setName, mode, setMode, approve, setApprove, liveAvailable, scanning, onRun }: {
  scenarios: Scenario[]
  scenario: Scenario | undefined
  setName: (n: string) => void
  mode: RunMode
  setMode: (m: RunMode) => void
  approve: boolean
  setApprove: (a: boolean) => void
  liveAvailable: boolean
  scanning: boolean
  onRun: () => void
}) {
  // only three scenarios were recorded with a real model; "Recorded run" stays clickable and moves to one of them
  const recorded = scenarios.filter((s) => s.has_recording)
  const disabled = (m: RunMode) => (m === 'groq' && !liveAvailable) || (m === 'recorded' && recorded.length === 0)
  const [note, setNote] = useState('')
  const caption = MODES.find((m) => m.id === mode)?.caption
  const pickMode = (id: RunMode) => {
    setNote('')
    if (id === 'recorded' && !scenario?.has_recording && recorded.length) {
      const target = recorded.find((s) => s.name === 'attack_bill_bn') ?? recorded[0]
      setName(target.name)
      setNote(`Switched to “${target.description.split('. ')[0].replace(/\.$/, '')}”: only ${recorded.length} scenarios have a recorded real run (marked “recorded” in the list).`)
    }
    setMode(id)
  }
  const pickScenario = (name: string) => {
    setNote('')
    setName(name)
    const next = scenarios.find((s) => s.name === name)
    if (mode === 'recorded' && next && !next.has_recording) {
      setMode('mock')
      setNote('That scenario has no recorded run, so it runs offline.')
    }
  }
  const untrusted = scenario?.untrusted ?? [] // older API servers do not send these fields yet
  // the injected item first; the ordinary ones collapse into "+N more"
  const attacks = untrusted.filter((u) => u.kind === 'attack')
  const shown = attacks.length ? attacks.slice(0, 2) : untrusted.slice(0, 2)
  const firstSource = untrusted[0]?.source
  const asked = scenario?.requests?.find((r) => r.kind === 'attack') ?? scenario?.requests?.[0]

  return (
    <section id="run-scenario" className="glass spotlight flex scroll-mt-20 flex-col gap-5 overflow-hidden p-5 sm:p-7" aria-busy={scanning}>
      {scanning && <span className="laser" aria-hidden />}
      <div className="relative">
        <h2 className="text-[1.3rem] font-semibold tracking-[-0.02em]">Run a scenario</h2>
        <p className="mt-1 text-sm text-muted">Pick who runs it, pick a story, run.</p>
        <div role="radiogroup" aria-label="Agent mode" className="mt-4 inline-flex max-w-full gap-1 rounded-xl border border-tile-line bg-fg/[0.03] p-1">
          {MODES.map(({ id, label }) => {
            const off = disabled(id)
            const active = mode === id
            return (
              <button
                key={id}
                type="button"
                role="radio"
                aria-checked={active}
                disabled={off}
                title={off ? (id === 'groq' ? 'Off on this server (no API key).' : 'No recorded runs on this server.') : undefined}
                onClick={() => pickMode(id)}
                className={`min-h-9 rounded-lg px-3 font-mono text-[0.8rem] whitespace-nowrap transition-colors duration-300 sm:px-4 ${
                  active ? 'bg-accent font-bold text-accent-ink' : 'text-body hover:bg-fg/5'
                } ${off ? 'cursor-not-allowed opacity-40' : ''}`}
              >
                {label}
              </button>
            )
          })}
        </div>
        <p className="mt-1.5 text-xs text-muted">{caption}</p>
        {note && <p className="mt-1 text-xs text-soft" role="status">{note}</p>}
      </div>

      <div className="relative border-t border-line pt-5">
        <label htmlFor="scenario" className="mb-2 block text-sm font-semibold">Scenario</label>
        <select
          id="scenario"
          value={scenario?.name}
          onChange={(e) => pickScenario(e.target.value)}
          className="min-h-12 w-full rounded-xl border border-accent/45 bg-card2 px-4 text-[0.95rem] font-semibold text-ink"
        >
          {scenarios.map((s, i) => (
            <option key={s.name} value={s.name}>
              {i + 1}. {s.description.split('. ')[0].replace(/\.$/, '')} ({s.kind === 'attack' ? 'Attack' : 'Normal'}){s.has_recording ? ' · recorded' : ''}
            </option>
          ))}
        </select>
      </div>

      {/* what the agent will be given */}
      <div className="relative rounded-2xl border border-tile-line bg-well/25 p-4">
        <div className="mb-3 flex flex-wrap items-center justify-between gap-2">
          <span className="text-sm font-semibold">What the agent will read</span>
          <span className={`rounded-md border px-2 py-0.5 font-mono text-[0.72rem] ${firstSource ? 'border-bad/40 bg-bad/10 text-bad-ink' : 'border-ok/35 bg-ok/10 text-ok-ink'}`}>
            {firstSource ? `untrusted: ${firstSource}` : 'trusted: user only'}
          </span>
        </div>
        <div className="rounded-xl border border-tile-line bg-tile px-3.5 py-2.5 text-sm">
          <span className="font-mono text-[0.78rem] text-muted">user_prompt:</span> <b>“{scenario?.user_task}”</b>
        </div>
        {untrusted.length === 0 ? (
          <p className="mt-2 px-1 text-[0.8rem] text-muted">No untrusted content: the agent works only from the user’s request and the bank.</p>
        ) : (
          <ul className="mt-2 flex flex-col gap-2">
            {shown.map((u) => (
              <li key={`${u.origin}-${u.title}`} className={`rounded-xl border px-3.5 py-2.5 ${u.kind === 'attack' ? 'border-bad/30 bg-bad/[0.07]' : 'border-tile-line bg-tile'}`}>
                <div className={`font-mono text-[0.72rem] ${u.kind === 'attack' ? 'text-bad-soft' : 'text-muted'}`}>
                  untrusted_content · {SOURCE_LABEL[u.source] ?? u.source} · {short(u.origin, 40)}
                </div>
                <p className="mt-1 line-clamp-2 text-[0.92rem] font-medium">{u.text}</p>
              </li>
            ))}
            {untrusted.length > shown.length && (
              <li className="px-1 font-mono text-[0.72rem] text-muted">
                +{untrusted.length - shown.length} more {untrusted.length - shown.length === 1 ? 'item' : 'items'} the agent also reads
              </li>
            )}
          </ul>
        )}
      </div>

      <label className={`relative flex cursor-pointer items-start gap-3 rounded-xl border border-tile-line bg-tile px-4 py-3 ${mode === 'recorded' ? 'cursor-not-allowed opacity-45' : ''}`}>
        <input
          type="checkbox"
          checked={approve}
          disabled={mode === 'recorded'}
          onChange={(e) => setApprove(e.target.checked)}
          className="mt-0.5 h-4.5 w-4.5 shrink-0 accent-[var(--color-mark)]"
        />
        <span>
          <b className="block text-sm">Simulated human approval</b>
          <span className="text-xs text-muted">Approve actions that ask for approval. Unticked = the user says no. BLOCK is never sent to the user.</span>
        </span>
      </label>

      <div className="relative flex flex-col gap-3 border-t border-line pt-5 sm:flex-row sm:items-center sm:justify-between">
        <p className="min-w-0 font-mono text-[0.8rem] text-muted">
          {asked ? (
            <>The {SOURCE_LABEL[untrusted.find((u) => u.origin === asked.origin)?.source ?? ''] ?? 'text'} asks for: <span className="text-warn-ink">send_money({asked.to}, {asked.amount})</span></>
          ) : (
            <>No payment request in the content</>
          )}
        </p>
        <button
          type="button"
          disabled={scanning || !scenario}
          onClick={onRun}
          className="btn-primary btn-shimmer lift inline-flex min-h-12 shrink-0 items-center justify-center gap-2 rounded-xl px-7 font-bold disabled:opacity-70"
        >
          {scanning ? (
            <><span className="h-4 w-4 animate-spin rounded-full border-2 border-accent-ink/30 border-t-accent-ink" aria-hidden /> Agent is working…</>
          ) : (
            <><Zap size={16} fill="currentColor" aria-hidden /> Run scenario</>
          )}
        </button>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// how it works: input -> gateway -> decision, live for the selected scenario and the last run

function FlowLink({ flowing, delay = 0 }: { flowing: boolean; delay?: number }) {
  return (
    <div className={`flex justify-center py-0.5 ${flowing ? 'is-flowing' : ''}`} aria-hidden>
      <div className="connector-y h-10 w-3" style={{ ['--d' as string]: `${delay}s` }}>
        <span className="packet-y" />
        <span className="packet-y" />
        <span className="packet-y" />
      </div>
    </div>
  )
}

function FlowNode({ icon: Icon, iconCls, title, sub, tag, tagCls, cls, bn }: {
  icon: LucideIcon; iconCls: string; title: string; sub: ReactNode; tag: string; tagCls: string; cls: string; bn?: string
}) {
  return (
    <div className={`ignite flex items-center gap-3.5 rounded-2xl border px-4 py-3.5 ${cls}`}>
      <span className={`inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-xl border ${iconCls}`}><Icon size={19} aria-hidden /></span>
      <div className="min-w-0 flex-1">
        <b className="block text-[1rem]">{title}</b>
        <span className="block font-mono text-[0.76rem] text-muted">{sub}</span>
        {bn && <span lang="bn" className="block text-[0.82rem] text-body">{bn}</span>}
      </div>
      <span className={`shrink-0 rounded-md border px-2 py-0.5 font-mono text-[0.72rem] font-bold tracking-wide ${tagCls}`}>{tag}</span>
    </div>
  )
}

function HowItWorks({ scenario, scanning, decided, thresholds }: {
  scenario: Scenario | undefined
  scanning: boolean
  decided: PipelineData | null
  thresholds: Thresholds
}) {
  const hasUntrusted = (scenario?.untrusted?.length ?? 0) > 0
  const status = scanning ? 'Inspecting' : decided ? 'Decided' : 'Standing by'
  const d = decided?.decision
  const dTone = d === 'block' ? 'border-bad/45 bg-bad/[0.1]' : d === 'ask_human' ? 'border-warn/45 bg-warn/[0.08]' : d === 'allow' ? 'border-ok/40 bg-ok/[0.08]' : 'border-tile-line bg-tile'
  const dTag = d === 'block' ? 'border-bad/45 bg-bad/12 text-bad-ink' : d === 'ask_human' ? 'border-warn/45 bg-warn/12 text-warn-ink' : d === 'allow' ? 'border-ok/40 bg-ok/12 text-ok-ink' : 'border-fg/10 text-muted'
  const t = thresholds
  return (
    <section className="glass spotlight flex h-full flex-col p-5 sm:p-7">
      <div className="relative flex items-start justify-between gap-3 border-b border-line pb-5">
        <div>
          <h2 className="text-[1.3rem] font-semibold tracking-[-0.02em]">How it decides</h2>
          <p className="mt-1 text-sm text-muted">Every tool call is intercepted and checked before it runs.</p>
        </div>
        <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-3 py-1 font-mono text-[0.74rem] ${scanning ? 'border-line2 bg-accent/10 text-soft' : 'border-ok/35 bg-ok/10 text-ok-ink'}`}>
          {scanning && <span className="pulse-dot h-1.5 w-1.5 rounded-full bg-mark" aria-hidden />} {status}
        </span>
      </div>
      <div className="relative mt-5 flex-1">
        <FlowNode
          icon={MailWarning} iconCls="border-warn/40 bg-warn/10 text-warn-ink" title="Untrusted input" sub="Email · Web Page · Document"
          tag={hasUntrusted ? 'TAINTED' : 'CLEAN'} tagCls={hasUntrusted ? 'border-warn/45 bg-warn/12 text-warn-ink' : 'border-ok/40 bg-ok/12 text-ok-ink'}
          cls="border-tile-line bg-tile"
        />
        <FlowLink flowing={scanning} />
        <FlowNode
          icon={ShieldCheck} iconCls="border-accent/40 bg-accent/12 text-soft" title="AgentShield gateway"
          sub={decided ? `4 checks · ${decided.latency < 10 ? decided.latency.toFixed(1) : Math.round(decided.latency)} ms` : '4 checks before every tool call'}
          tag="INSPECT" tagCls="border-accent/45 bg-accent/12 text-soft" cls={`border-accent/30 bg-accent/[0.05] ${scanning ? 'is-lit' : ''}`}
        />
        <FlowLink flowing={scanning} delay={0.9} />
        <FlowNode
          icon={scanning || !d ? Hourglass : d === 'allow' ? CircleCheck : d === 'ask_human' ? CircleHelp : ShieldX}
          iconCls={scanning || !d ? 'border-fg/10 bg-fg/5 text-muted' : d === 'allow' ? 'border-ok/40 bg-ok/10 text-ok-ink' : d === 'ask_human' ? 'border-warn/40 bg-warn/10 text-warn-ink' : 'border-bad/40 bg-bad/10 text-bad-ink'}
          title={scanning ? 'Decision: …' : d ? `Decision: ${DECISION_WORD[d]}` : 'Decision: waiting'}
          sub={!scanning && decided ? `risk ${decided.risk.toFixed(2)}` : scanning ? 'checking' : 'run a scenario'}
          bn={!scanning && d ? DECISION_BN[d] : undefined}
          tag={!scanning && d ? DECISION_TONE[d].label : '—'} tagCls={scanning ? 'border-fg/10 text-muted' : dTag} cls={scanning ? 'border-tile-line bg-tile' : dTone}
        />
      </div>
      <div className="relative mt-5 grid grid-cols-3 gap-2 border-t border-line pt-5 font-mono text-[0.72rem] sm:text-[0.78rem]">
        <span className="rounded-lg border border-ok/35 bg-ok/8 px-2 py-2 text-center text-ok-ink">ALLOW &lt; {t.ask_human_at.toFixed(2)}</span>
        <span className="rounded-lg border border-warn/35 bg-warn/8 px-2 py-2 text-center text-warn-ink">ASK {t.ask_human_at.toFixed(2)}–{t.block_at.toFixed(2)}</span>
        <span className="rounded-lg border border-bad/35 bg-bad/8 px-2 py-2 text-center text-bad-ink">BLOCK ≥ {t.block_at.toFixed(2)}</span>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// evaluation pipeline

interface PipelineData {
  checks: CheckResult[]
  decision: Decision
  risk: number
  latency: number
  call: string
  from: 'run' | 'audit'
}

/** The call to show from a run: the first one AgentShield stopped, else the last money transfer, else the last checked call. */
function fromRun(result: RunResult | undefined): PipelineData | null {
  const steps = (result?.with.steps ?? []).filter((s): s is Step & { verdict: Verdict } => s.verdict !== null)
  const s = steps.find((x) => x.verdict.decision !== 'allow') ?? steps.filter((x) => x.tool === 'send_money').at(-1) ?? steps.at(-1)
  return s ? { checks: s.verdict.checks, decision: s.verdict.decision, risk: s.verdict.risk_score, latency: s.verdict.total_latency_ms, call: callText(s.tool, s.args), from: 'run' } : null
}

const fromAudit = (r: AuditRecord | undefined): PipelineData | null =>
  r ? { checks: r.checks, decision: r.decision, risk: r.risk_score, latency: r.total_latency_ms, call: callText(r.tool_name, r.arguments), from: 'audit' } : null

/** One line under each card title, from the check's own details. */
function checkNote(name: string, c: CheckResult | undefined): string {
  if (!c) return 'not run'
  if (c.skipped) return 'not needed for this call'
  const d = (c.details ?? {}) as Record<string, unknown>
  if (name === 'taint') {
    const args = Object.values((d.arguments ?? {}) as Record<string, { status?: string; source?: string }>)
    const ext = args.find((a) => a.status === 'tool_data')
    return ext ? `Source: ${SOURCE_LABEL[ext.source ?? ''] ?? ext.source ?? 'tool'} (untrusted)` : args.length ? 'Source: the user’s request' : 'No traced arguments'
  }
  if (name === 'classifier') {
    const top = d.top_item as { language?: string; signals?: string[] } | undefined
    const lang = top?.language ? ({ bn: 'Bangla', banglish: 'Banglish', en: 'English' } as Record<string, string>)[top.language] ?? top.language : null
    return top?.signals?.length ? `${lang ?? 'Text'} · ${top.signals.length} signal${top.signals.length > 1 ? 's' : ''}` : 'Multilingual BN / Banglish / EN'
  }
  if (name === 'policy') {
    const rule = (d.top_rule as string | undefined) ?? undefined
    return rule ? `Rule: ${rule.replaceAll('_', ' ')}` : 'No rule matched'
  }
  return ''
}

function Pipeline({ data, scanning, runKey, thresholds }: { data: PipelineData | null; scanning: boolean; runKey: string; thresholds: Thresholds }) {
  return <PipelineCards key={runKey} data={data} scanning={scanning} thresholds={thresholds} />
}

function PipelineCards({ data, scanning, thresholds }: { data: PipelineData | null; scanning: boolean; thresholds: Thresholds }) {
  // cards from a fresh run ignite one by one; the audit fallback shows at once
  const [lit, setLit] = useState(() => (reducedMotion() || data?.from !== 'run' ? 4 : 0))
  const isRun = data?.from === 'run'
  useEffect(() => {
    if (!isRun || reducedMotion()) return
    const timers = [1, 2, 3, 4].map((n) => window.setTimeout(() => setLit(n), n * 380))
    return () => timers.forEach(clearTimeout)
  }, [isRun])

  const c = (n: string) => data?.checks.find((x) => x.check === n)
  const val = (n: string) => { const x = c(n); return x && !x.skipped ? x.risk_score : null }
  const ip = Math.max(val('intent') ?? -1, val('policy') ?? -1)
  const cards = [
    { n: '01', key: 'TAINT', title: 'Taint Analysis', score: val('taint'), note: data ? checkNote('taint', c('taint')) : '' },
    { n: '02', key: 'CLASSIFIER', title: 'Injection Classifier', score: val('classifier'), note: data ? checkNote('classifier', c('classifier')) : '' },
    { n: '03', key: 'INTENT + POLICY', title: 'Intent + Policy', score: ip < 0 ? null : ip, note: data ? checkNote('policy', c('policy')) : '' },
    { n: '04', key: 'VERDICT', title: 'Agent Decision', score: data?.risk ?? null, note: data ? `${DECISION_WORD[data.decision]} / ${DECISION_BN[data.decision]}` : '' },
  ]

  return (
    <section className="glass spotlight p-5 sm:p-7">
      <div className="relative flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-[1.3rem] font-semibold tracking-[-0.02em]">The four checks</h2>
          <p className="mt-1 text-sm text-muted">Four checks run before every tool call; the stricter of score and policy wins.</p>
          {data && !scanning && (
            <p className="mt-1.5 font-mono text-[0.74rem] text-muted">
              {data.from === 'run' ? 'Last run, decisive call:' : 'Latest BLOCK in the audit log:'} <span className="text-warn-ink">{short(data.call, 48)}</span>
            </p>
          )}
        </div>
        {data && !scanning && (
          <span className="font-mono text-[0.8rem] text-muted">
            Total latency: <b className="text-ink tabular-nums">{data.latency < 10 ? data.latency.toFixed(2) : Math.round(data.latency)} ms</b>
          </span>
        )}
      </div>
      <ol className="relative mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
        {cards.map(({ n, key, title, score, note }, i) => {
          const on = !!data && !scanning && lit > i
          const tone = scoreTone(on ? score : null, thresholds)
          const verdict = i === 3 && on && data
          return (
            <li
              key={n}
              className={`ignite tilt relative flex flex-col gap-3 rounded-2xl border p-4 ${on ? tone.card : 'border-tile-line'} ${
                verdict ? (data.decision === 'block' ? 'bg-bad/[0.1]' : data.decision === 'ask_human' ? 'bg-warn/[0.08]' : 'bg-ok/[0.08]') : 'bg-tile'
              } ${on ? 'is-lit' : ''}`}
            >
              <div className="flex items-center justify-between gap-2">
                <span className="font-mono text-[0.72rem] tracking-[0.1em] text-muted">{n} · {key}</span>
                <span className={`rounded-md border px-2 py-0.5 font-mono text-[0.76rem] font-bold tabular-nums ${tone.badge}`}>
                  {scanning ? '…' : on && score !== null ? score.toFixed(2) : '—'}
                </span>
              </div>
              <div>
                <b className="block text-[1.02rem]">{title}</b>
                <span className={`block text-[0.82rem] ${verdict ? 'font-bold text-ink' : 'text-muted'}`} lang={verdict ? 'bn' : undefined}>
                  {scanning ? 'scanning…' : on ? note : data ? 'waiting' : 'no decision yet'}
                </span>
              </div>
              <FlowBar value={on && score !== null ? score : 0} tone={tone.bar} busy={scanning} />
            </li>
          )
        })}
      </ol>
    </section>
  )
}

// ---------------------------------------------------------------------------
// recent evaluations

type Filter = 'all' | 'block' | 'allow'

function useRecent(filter: Filter) {
  const queryClient = useQueryClient()
  return useQuery({
    queryKey: ['audit', 'recent', filter],
    // each fetch marks the rows the previous fetch did not have; those glow once
    queryFn: async () => {
      const prev = queryClient.getQueryData<AuditPage & { fresh: string[] }>(['audit', 'recent', filter])
      const next = await api.audit({ limit: 6, decision: filter === 'all' ? undefined : filter })
      const before = new Set(prev?.records.map((r) => r.id))
      return { ...next, fresh: prev ? next.records.filter((r) => !before.has(r.id)).map((r) => r.id) : [] }
    },
    placeholderData: keepPreviousData,
  })
}

function RecentEvaluations({ scanning }: { scanning: boolean }) {
  const [filter, setFilter] = useState<Filter>('all')
  const { data, error, isPending } = useRecent(filter)
  const [open, setOpen] = useState<AuditRecord | null>(null)
  const fresh = new Set(data?.fresh)
  const t = data?.thresholds ?? DEFAULT_T

  const Risk = ({ r }: { r: AuditRecord }) => (
    <div className="flex items-center gap-2.5">
      <FlowBar value={r.risk_score} tone={scoreTone(r.risk_score, t).bar} className="h-1.5 w-20" />
      <span className="font-mono text-[0.82rem] tabular-nums">{r.risk_score.toFixed(2)}</span>
    </div>
  )
  const Chip = ({ r }: { r: AuditRecord }) => (
    <code className="inline-block max-w-full truncate rounded-lg border border-fg/10 bg-well/30 px-2.5 py-1 font-mono text-[0.78rem] text-warn-ink">
      {short(callText(r.tool_name, r.arguments), 36)}
    </code>
  )

  return (
    <section className="glass spotlight p-5 sm:p-7">
      <div className="relative flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-[1.3rem] font-semibold tracking-[-0.02em]">Recent decisions</h2>
          <p className="mt-1 text-sm text-muted">Click any row to inspect the full JSON audit trace and taint lineage.</p>
        </div>
        <div role="tablist" aria-label="Filter by decision" className="inline-flex gap-1 rounded-xl border border-tile-line bg-fg/[0.03] p-1">
          {(['all', 'block', 'allow'] as const).map((f) => (
            <button
              key={f}
              type="button"
              role="tab"
              aria-selected={filter === f}
              onClick={() => setFilter(f)}
              className={`min-h-9 rounded-lg px-4 font-mono text-[0.8rem] transition-colors duration-300 ${filter === f ? 'bg-accent font-bold text-accent-ink' : 'text-body hover:bg-fg/5'}`}
            >
              {f === 'all' ? 'All' : f.toUpperCase()}
            </button>
          ))}
        </div>
      </div>

      <div className="relative mt-5">
        {isPending && <div className="flex flex-col gap-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-12" />)}</div>}
        {error && <ErrorNote error={error} />}
        {data && data.records.length === 0 && !scanning && <p className="py-3 text-sm text-muted">No decisions here yet. Run a scenario to see one.</p>}
        {data && (data.records.length > 0 || scanning) && (
          <>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full text-left text-sm">
                <thead>
                  <tr className="border-b border-line font-mono text-[0.7rem] tracking-[0.12em] text-muted uppercase">
                    <th className="py-3 pr-4 font-medium">Time (UTC)</th>
                    <th className="py-3 pr-4 font-medium">User request</th>
                    <th className="py-3 pr-4 font-medium">Tool call</th>
                    <th className="py-3 pr-4 font-medium">Risk score</th>
                    <th className="py-3 pr-4 font-medium">Verdict</th>
                    <th className="py-3 text-right font-medium">Action</th>
                  </tr>
                </thead>
                <tbody>
                  {scanning && (
                    <tr className="border-b border-line/60">
                      <td className="py-3.5 pr-4 font-mono text-[0.82rem] text-soft">now</td>
                      <td className="py-3.5 pr-4 text-muted" colSpan={2}>Evaluating the agent’s tool calls…</td>
                      <td className="py-3.5 pr-4"><FlowBar value={0} tone="bg-mark" busy className="h-1.5 w-20" /></td>
                      <td className="py-3.5 pr-4 font-mono text-xs text-muted" colSpan={2}>scanning</td>
                    </tr>
                  )}
                  {data.records.map((r) => (
                    <tr
                      key={r.id}
                      tabIndex={0}
                      onClick={() => setOpen(r)}
                      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), setOpen(r))}
                      aria-label={`Inspect ${r.decision} ${r.tool_name}`}
                      className={`group cursor-pointer border-b border-line/60 transition-colors hover:bg-fg/[0.03] focus-visible:bg-fg/[0.03] ${fresh.has(r.id) ? 'row-new' : ''}`}
                    >
                      <td className="py-3.5 pr-4 font-mono text-[0.82rem] whitespace-nowrap text-muted tabular-nums">{clock(r.timestamp)}</td>
                      <td className="py-3.5 pr-4 font-semibold">{short(r.user_request, 40)}</td>
                      <td className="max-w-[18rem] py-3.5 pr-4"><Chip r={r} /></td>
                      <td className="py-3.5 pr-4"><Risk r={r} /></td>
                      <td className="py-3.5 pr-4"><DecisionBadge decision={r.decision} /></td>
                      <td className="py-3.5 text-right font-mono text-[0.8rem] whitespace-nowrap text-muted group-hover:text-ink">Inspect ↗</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ul className="flex flex-col gap-2.5 md:hidden">
              {scanning && (
                <li className="flex flex-col gap-2 rounded-xl border border-line2 bg-tile px-3.5 py-3">
                  <span className="font-mono text-xs text-soft">now · evaluating…</span>
                  <FlowBar value={0} tone="bg-mark" busy />
                </li>
              )}
              {data.records.map((r) => (
                <li key={r.id}>
                  <button
                    type="button"
                    onClick={() => setOpen(r)}
                    className={`flex w-full flex-col gap-2 rounded-xl border border-tile-line bg-tile px-3.5 py-3 text-left ${fresh.has(r.id) ? 'row-new' : ''}`}
                  >
                    <span className="flex w-full items-center justify-between gap-2">
                      <span className="font-mono text-xs text-muted">{clock(r.timestamp)} UTC</span>
                      <DecisionBadge decision={r.decision} />
                    </span>
                    <span className="text-sm font-semibold">{short(r.user_request, 80)}</span>
                    <Chip r={r} />
                    <span className="flex w-full items-center justify-between gap-2">
                      <Risk r={r} />
                      <span className="font-mono text-xs text-muted">Inspect ↗</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
      {open && data && <AuditDrawer record={open} thresholds={t} onClose={() => setOpen(null)} />}
    </section>
  )
}

// ---------------------------------------------------------------------------
// page

const MIN_SCAN_MS = 1400 // offline runs finish in milliseconds: keep the scan visible long enough to read

export default function Playground() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const overview = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  const scenarios = useQuery({ queryKey: ['scenarios'], queryFn: api.scenarios, staleTime: Infinity })
  // until a run: the latest BLOCK from the audit log fills the pipeline
  const latestBlock = useQuery({ queryKey: ['audit', 'latest-block'], queryFn: () => api.audit({ decision: 'block', limit: 1 }) })
  const pipelineRef = useRef<HTMLDivElement>(null)
  const [runId, setRunId] = useState(0)
  const [scanning, setScanning] = useState(false)
  const started = useRef(0)
  const timer = useRef(0)
  useEffect(() => () => clearTimeout(timer.current), [])

  const scenarioList = useMemo(() => scenarios.data ?? [], [scenarios.data])
  const [picked, setPicked] = useState<string | null>(null)
  const scenario = scenarioList.find((s) => s.name === picked) ?? scenarioList.find((s) => s.name === 'attack_email_bn') ?? scenarioList[0]
  const [modePicked, setMode] = useState<RunMode>('mock')
  const [approve, setApprove] = useState(false)
  const liveAvailable = overview.data?.live_mode_available ?? false
  const mode: RunMode = (modePicked === 'groq' && !liveAvailable) || (modePicked === 'recorded' && !scenario?.has_recording) ? 'mock' : modePicked
  const thresholds = latestBlock.data?.thresholds ?? DEFAULT_T

  const run = useMutation<RunResult, Error, { name: string; mode: RunMode; approve: boolean }>({
    mutationFn: ({ name, mode, approve }) => api.run(name, mode, approve),
    onMutate: () => {
      started.current = performance.now()
      setScanning(true)
    },
    onSettled: (result) => {
      const wait = reducedMotion() ? 0 : Math.max(0, MIN_SCAN_MS - (performance.now() - started.current))
      timer.current = window.setTimeout(() => {
        setScanning(false)
        if (!result) return
        const saved = result.without.stolen - result.with.stolen
        toast(saved > 0 ? `Run finished: AgentShield kept ${taka(saved)} in the account` : 'Run finished')
        setRunId((n) => n + 1)
        void queryClient.invalidateQueries({ queryKey: ['audit'] })
        void queryClient.invalidateQueries({ queryKey: ['overview'] })
      }, wait)
    },
  })

  // bring the pipeline into view when the scan ends: the cards ignite there
  useEffect(() => {
    if (runId && pipelineRef.current) smoothScrollTo(pipelineRef.current, -24)
  }, [runId])

  const fromLastRun = runId > 0 ? fromRun(run.data) : null
  const pipelineData = fromLastRun ?? fromAudit(latestBlock.data?.records[0])

  return (
    <div className="flex flex-col gap-5">
      <div>
        <PageHeader
          title="Playground"
          sub="Give the same task to an unprotected agent and to one behind AgentShield, then compare what each one did with the money."
          right={<Link to="/audit" className="hidden min-h-11 items-center gap-1.5 rounded-xl border border-line2 px-4 text-sm font-semibold hover:bg-fg/5 sm:inline-flex">Audit log →</Link>}
        />
        <PlaygroundStats />
      </div>

      <div className="grid items-stretch gap-5 xl:grid-cols-[1.2fr_1fr]">
        {scenarios.error ? (
          <ErrorNote error={scenarios.error} />
        ) : scenarioList.length ? (
          <RunCard
            scenarios={scenarioList}
            scenario={scenario}
            setName={setPicked}
            mode={mode}
            setMode={setMode}
            approve={approve}
            setApprove={setApprove}
            liveAvailable={liveAvailable}
            scanning={scanning}
            onRun={() => scenario && run.mutate({ name: scenario.name, mode, approve })}
          />
        ) : (
          <Skeleton className="h-[560px]" />
        )}
        <HowItWorks scenario={scenario} scanning={scanning} decided={fromLastRun} thresholds={thresholds} />
      </div>

      <div ref={pipelineRef} className="scroll-mt-20 lg:scroll-mt-6">
        <Pipeline data={scanning ? null : pipelineData} scanning={scanning} runKey={`${runId}-${scanning}-${pipelineData?.from}`} thresholds={thresholds} />
      </div>

      <div aria-live="polite">
        {run.error && !scanning && <ErrorNote error={run.error} />}
        {run.data && !scanning && runId > 0 && (
          <RunResultView key={runId} result={run.data} rerunning={scanning} onRerun={() => run.variables && run.mutate(run.variables)} />
        )}
      </div>

      <RecentEvaluations scanning={scanning} />
    </div>
  )
}
