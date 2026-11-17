import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  ArrowRight, Bot, CircleCheck, CircleHelp, CircleX, FileText, Globe, Layers, Mail, Play, PlayCircle, Radio,
  ShieldCheck, ShieldX, Target, Activity, Workflow, Zap, Banknote, type LucideIcon,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import AuditDrawer from '../components/AuditDrawer'
import HeroArt from '../components/HeroArt'
import { AnimatedValue } from '../components/Motion'
import RunResultView from '../components/RunResultView'
import { DecisionBadge, ErrorNote, PanelTitle, Skeleton } from '../components/ui'
import { api, type AuditPage, type AuditRecord, type Decision, type RunMode, type RunResult, type Scenario, type Step, type Verdict } from '../lib/api'
import { short, taka, utcTime } from '../lib/format'
import { reducedMotion, smoothScrollTo } from '../lib/motion'
import { useToast } from '../lib/toast'

// Every number on this page comes from the API: /api/overview, /api/audit, and the run itself.

const DECISION_TONE: Record<Decision, { bar: string; text: string; glow: string; label: string }> = {
  allow: { bar: 'bg-ok', text: 'text-ok-ink', glow: 'rgb(16 185 129 / 0.7)', label: 'ALLOW' },
  ask_human: { bar: 'bg-warn', text: 'text-warn-ink', glow: 'rgb(245 158 11 / 0.7)', label: 'ASK HUMAN' },
  block: { bar: 'bg-bad', text: 'text-bad-ink', glow: 'rgb(244 63 94 / 0.75)', label: 'BLOCK' },
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

function Hero() {
  return (
    <div className="grid items-center gap-6 xl:grid-cols-[1.05fr_1fr]">
      <div className="spring-in">
        <span className="glass inline-flex items-center gap-2 rounded-full! px-3 py-1 text-xs font-semibold text-soft">
          <span className="h-1.5 w-1.5 rounded-full bg-ok shadow-[0_0_8px_var(--color-ok)]" aria-hidden /> AgentShield AI Safety Playground
        </span>
        <h1 className="mt-4 text-[clamp(1.75rem,6.2vw,2.2rem)] leading-[1.08] font-extrabold tracking-[-0.025em] lg:text-[2.75rem]">
          <span className="block">Stop AI Agents from Acting&nbsp;on</span>
          <span className="text-soft">Hidden Instructions</span>
        </h1>
        <p className="mt-4 max-w-[560px] text-[0.95rem] leading-relaxed text-body lg:text-base">
          AgentShield checks every tool call before it runs, so an AI agent cannot be tricked into sending money by text
          hidden in emails, web pages or files, in Bangla, Banglish and English.
        </p>
        <div className="mt-6 flex flex-col gap-2.5 sm:flex-row">
          <a href="#run-scenario" className="btn-primary btn-shimmer lift inline-flex min-h-12 items-center justify-center gap-2 rounded-xl px-6 font-bold">
            <Play size={14} fill="currentColor" aria-hidden /> Try a Scenario
          </a>
          <Link to="/audit" className="glass lift inline-flex min-h-12 items-center justify-center gap-2 rounded-xl! px-6 font-bold hover:border-line2!">
            <FileText size={16} aria-hidden /> View Audit Logs
          </Link>
        </div>
      </div>
      <HeroArt />
    </div>
  )
}

// ---------------------------------------------------------------------------
// KPI bento

function Kpi({ icon: Icon, tint, num, label, note, index }: { icon: LucideIcon; tint: string; num: string; label: string; note: string; index: number }) {
  return (
    <div style={{ ['--i' as string]: index }} className="spring-in">
      <div className="glass spotlight tilt flex h-full flex-col gap-3 p-4 sm:p-5">
        <div className="relative flex items-center justify-between gap-2">
          <span
            className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
            style={{ background: `color-mix(in srgb, ${tint} 12%, transparent)`, border: `1px solid color-mix(in srgb, ${tint} 30%, transparent)` }}
          >
            <Icon size={20} color={tint} aria-hidden />
          </span>
        </div>
        <div className="relative min-w-0">
          <div className="font-mono text-[1.7rem] leading-none font-bold tabular-nums sm:text-[2rem]"><AnimatedValue value={num} /></div>
          <div className="mt-1.5 text-[0.84rem] font-semibold sm:text-sm">{label}</div>
          <div className="mt-0.5 text-[0.72rem] text-muted sm:text-xs">{note}</div>
        </div>
      </div>
    </div>
  )
}

const todayUtc = () => `${new Date().toISOString().slice(0, 10)}T00:00:00+00:00`

function Kpis() {
  const { data } = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  // BLOCK decisions in the audit log since 00:00 UTC (runs on this page add to it)
  const blocked = useQuery({ queryKey: ['audit', 'blocked-today'], queryFn: () => api.audit({ decision: 'block', since: todayUtc(), limit: 1 }) })
  if (!data)
    return (
      <div className="my-6 grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4" aria-hidden>
        {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-[150px]" />)}
      </div>
    )
  const real = data.real_llm
  const langs = Object.keys(data.attack_samples.by_language).length
  const blockedTotal = blocked.data?.stats.block
  return (
    <div className="my-6 grid grid-cols-2 gap-3 sm:gap-4 xl:grid-cols-4">
      <Kpi index={0} icon={ShieldCheck} tint="var(--color-soft)" num={String(data.checks.length)} label="Active Security Layers"
        note={data.checks.map((c) => c[0].toUpperCase() + c.slice(1)).join(' · ')} />
      <Kpi index={1} icon={Globe} tint="var(--color-info)" num={String(langs)} label="Supported Languages" note="Bangla · Banglish · English" />
      <Kpi index={2} icon={ShieldX} tint="var(--color-bad)" num={blocked.data ? String(blocked.data.total) : '–'} label="Blocked Attacks Today"
        note={blockedTotal !== undefined ? `Since 00:00 UTC · ${blockedTotal} in the audit log` : 'From the audit log'} />
      <Kpi index={3} icon={Banknote} tint="var(--color-ok)" num={real ? `${real.with.hits}/${real.with.total}` : '–'} label="Unauthorized Transfers"
        note={real ? `Real LLM with AgentShield · ${real.without.hits}/${real.without.total} without` : 'No real-LLM run yet'} />
    </div>
  )
}

// ---------------------------------------------------------------------------
// scenario runner

const MODES: { id: RunMode; label: string; caption: string; icon: LucideIcon }[] = [
  { id: 'mock', label: 'Offline', caption: 'Simulated naive agent. Works offline.', icon: Bot },
  { id: 'groq', label: 'Live (Groq)', caption: 'Real model via Groq, same tools. Can take up to a minute.', icon: Radio },
  { id: 'recorded', label: 'Recorded Run', caption: 'Instant replay of a saved real run.', icon: PlayCircle },
]

const scenarioLabel = (s: Scenario) => `${s.kind === 'attack' ? '⚠️ Attack' : '✅ Normal'}: ${s.description}`

function RunCard({ scenarios, liveAvailable, scanning, onRun }: {
  scenarios: Scenario[]
  liveAvailable: boolean
  scanning: boolean
  onRun: (name: string, mode: RunMode, approve: boolean) => void
}) {
  const [name, setName] = useState(() => (scenarios.some((s) => s.name === 'attack_email_bn') ? 'attack_email_bn' : scenarios[0]?.name))
  const [mode, setMode] = useState<RunMode>('mock')
  const [approve, setApprove] = useState(false)
  const selected = scenarios.find((s) => s.name === name)
  const disabled = (m: RunMode) => (m === 'groq' && !liveAvailable) || (m === 'recorded' && !selected?.has_recording)
  const effectiveMode = disabled(mode) ? 'mock' : mode
  const modeInfo = MODES.find((m) => m.id === effectiveMode)!
  const offNote = (id: RunMode) => (id === 'groq' ? 'Off on this server (no API key).' : 'No recording for this scenario.')

  return (
    <section id="run-scenario" className="glass spotlight flex scroll-mt-20 flex-col gap-4 overflow-hidden p-4 sm:p-5" aria-busy={scanning}>
      {scanning && <span className="laser" aria-hidden />}
      <div className="relative flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-ink">
            <Play size={17} fill="currentColor" aria-hidden />
          </span>
          <div>
            <h2 className="text-[1.15rem] font-bold">Run a Safety Scenario</h2>
            <p className="mt-0.5 text-sm text-muted">Test the same task on an unprotected agent and on an agent protected by AgentShield.</p>
          </div>
        </div>
        <span className={`inline-flex shrink-0 items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-bold ${scanning ? 'border-line2 bg-accent/10 text-soft' : 'border-ok/40 bg-ok/12 text-ok-ink'}`}>
          <span className={`h-1.5 w-1.5 animate-pulse rounded-full ${scanning ? 'bg-mark' : 'bg-ok'}`} aria-hidden /> {scanning ? 'Scanning' : 'Ready'}
        </span>
      </div>

      <div className="relative">
        <span className="mb-1.5 block text-sm font-semibold" id="mode-label">Agent Mode</span>
        <div role="radiogroup" aria-labelledby="mode-label" className="flex gap-1 rounded-2xl border border-fg/8 bg-fg/[0.03] p-1 sm:gap-1.5">
          {MODES.map(({ id, label, icon: Icon }) => {
            const off = disabled(id)
            const active = effectiveMode === id
            return (
              <button
                key={id}
                type="button"
                role="radio"
                aria-checked={active}
                disabled={off}
                title={off ? offNote(id) : undefined}
                onClick={() => setMode(id)}
                className={`inline-flex min-h-10 min-w-0 flex-1 items-center justify-center gap-1.5 rounded-xl border px-1.5 text-[0.8rem] font-bold whitespace-nowrap transition-[background-color,border-color,color,box-shadow] duration-300 sm:px-3 sm:text-sm ${
                  active ? 'nav-pill-active' : 'border-transparent text-body hover:bg-fg/5'
                } ${off ? 'cursor-not-allowed opacity-40' : ''}`}
              >
                <Icon size={15} className="hidden shrink-0 sm:block" aria-hidden /> {label}
              </button>
            )
          })}
        </div>
        <p className="mt-1.5 text-[0.8rem] text-muted">
          {modeInfo.caption}
          {disabled('groq') && ' Live (Groq) is off on this server.'}
        </p>
      </div>

      <label className="relative flex flex-col gap-1.5 text-sm font-semibold">
        Scenario
        <select
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="min-h-11 w-full rounded-xl border border-fg/10 bg-card2 px-3 text-[0.95rem] font-normal text-ink"
        >
          {scenarios.map((s) => <option key={s.name} value={s.name}>{scenarioLabel(s)}</option>)}
        </select>
      </label>

      {/* what the button will send */}
      <div className="relative rounded-xl border border-fg/8 bg-well/30 px-3.5 py-3 font-mono text-[0.76rem] leading-relaxed">
        <div className="mb-1 flex items-center justify-between text-[0.68rem] tracking-[0.14em] text-muted uppercase">
          <span>Payload preview</span>
          <span className={`h-1.5 w-1.5 rounded-full ${scanning ? 'pulse-dot bg-mark' : 'bg-ok'}`} aria-hidden />
        </div>
        <div className="break-all"><span className="text-info-ink">POST</span> <span className="text-body">/api/scenarios/{name}/run</span></div>
        <div className="text-soft">{`{ "mode": "${effectiveMode}", "approve": ${effectiveMode === 'recorded' ? false : approve} }`}</div>
        {selected && <div className="mt-1 text-muted"># task: “{selected.user_task}”</div>}
      </div>

      <label className={`relative flex items-start gap-2.5 text-sm ${effectiveMode === 'recorded' ? 'opacity-45' : ''}`}>
        <input
          type="checkbox"
          checked={approve}
          disabled={effectiveMode === 'recorded'}
          onChange={(e) => setApprove(e.target.checked)}
          className="mt-0.5 h-4.5 w-4.5 shrink-0 accent-[var(--color-mark)]"
        />
        <span>
          I approve actions that ask for my approval (simulated human click)
          <span className="mt-0.5 block text-xs text-muted">Unticked = the user says no. BLOCK decisions are never sent to the user.</span>
        </span>
      </label>

      <button
        type="button"
        disabled={scanning || !name}
        onClick={() => name && onRun(name, effectiveMode, approve)}
        className="btn-primary lift relative inline-flex min-h-12 items-center justify-center gap-2 rounded-xl font-bold disabled:opacity-70"
      >
        {scanning ? (
          <><span className="h-4 w-4 animate-spin rounded-full border-2 border-accent-ink/30 border-t-accent-ink" aria-hidden /> Agent is working…</>
        ) : (
          <><Play size={15} fill="currentColor" aria-hidden /> Run Scenario</>
        )}
      </button>
    </section>
  )
}

// ---------------------------------------------------------------------------
// how it works: packets travel down the connectors while a scenario runs

function Connector({ flowing }: { flowing: boolean }) {
  return (
    <div className={`flex items-center justify-center ${flowing ? 'is-flowing' : ''}`} aria-hidden>
      <div className="connector h-7 w-[3px] md:h-[3px] md:w-11">
        <span className="packet left-1/2 -ml-1 md:top-1/2 md:left-0 md:-mt-1 md:ml-0" />
        <span className="packet left-1/2 -ml-1 md:top-1/2 md:left-0 md:-mt-1 md:ml-0" />
        <span className="packet left-1/2 -ml-1 md:top-1/2 md:left-0 md:-mt-1 md:ml-0" />
      </div>
      <ArrowRight size={16} className="hidden shrink-0 text-muted md:block" />
    </div>
  )
}

function HowItWorks({ flowing }: { flowing: boolean }) {
  const nodes = [
    { icon: Mail, color: 'var(--color-bad)', title: 'Untrusted input', sub: 'email · web · file', cls: 'border-bad/40 bg-bad/8' },
    { icon: ShieldCheck, color: 'var(--color-soft)', title: 'AgentShield', sub: 'checks each tool call', cls: 'border-accent2/60 bg-accent/12' },
    { icon: CircleCheck, color: 'var(--color-ok)', title: 'Decision', sub: 'allow · ask · block', cls: 'border-ok/40 bg-ok/8' },
  ]
  const decisions = [
    { icon: CircleCheck, color: 'var(--color-ok)', title: 'ALLOW', sub: "Action follows from the user's request", cls: 'border-ok/40 bg-ok/8' },
    { icon: CircleHelp, color: 'var(--color-warn)', title: 'ASK', sub: 'Uncertain: the user approves or rejects', cls: 'border-warn/40 bg-warn/8' },
    { icon: CircleX, color: 'var(--color-bad)', title: 'BLOCK', sub: 'Clear attack or policy violation', cls: 'border-bad/40 bg-bad/8' },
  ]
  return (
    <section className="glass spotlight h-full p-4 sm:p-5">
      <div className="relative">
        <PanelTitle icon={Workflow} title="How AgentShield Works" />
        <div className="flex flex-col items-stretch gap-1 md:flex-row md:items-center">
          {nodes.map(({ icon: Icon, color, title, sub, cls }, i) => (
            <div key={title} className="contents">
              {i > 0 && <Connector flowing={flowing} />}
              <div className={`ignite flex flex-1 flex-col items-center gap-1 rounded-xl border px-3 py-4 text-center ${cls} ${flowing && i === 1 ? 'is-lit' : ''}`}>
                <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-fg/5">
                  <Icon size={20} color={color} aria-hidden />
                </span>
                <b className="text-[0.95rem]">{title}</b>
                <span className="text-xs text-muted">{sub}</span>
              </div>
            </div>
          ))}
        </div>
        <div className="mt-5">
          <PanelTitle icon={Activity} title="Decision Types" />
          <div className="grid gap-2 md:grid-cols-3">
            {decisions.map(({ icon: Icon, color, title, sub, cls }) => (
              <div key={title} className={`rounded-xl border px-3.5 py-3 ${cls}`}>
                <div className="flex items-center gap-2 font-bold"><Icon size={19} color={color} aria-hidden /> {title}</div>
                <p className="mt-1 text-[0.8rem] text-muted">{sub}</p>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// evaluation pipeline: the four checks of the run's decisive tool call ignite one by one

/** The call to show: the first one AgentShield stopped, else the last money transfer, else the last checked call. */
function decisiveStep(result: RunResult | undefined): (Step & { verdict: Verdict }) | null {
  const steps = (result?.with.steps ?? []).filter((s): s is Step & { verdict: Verdict } => s.verdict !== null)
  return steps.find((s) => s.verdict.decision !== 'allow') ?? steps.filter((s) => s.tool === 'send_money').at(-1) ?? steps.at(-1) ?? null
}

function Pipeline({ result, scanning, runId }: { result: RunResult | undefined; scanning: boolean; runId: number }) {
  // keyed by run: each result mounts fresh cards, which then ignite one by one
  return <PipelineCards key={`${runId}-${scanning}`} result={result} scanning={scanning} runId={runId} />
}

function PipelineCards({ result, scanning, runId }: { result: RunResult | undefined; scanning: boolean; runId: number }) {
  const step = scanning ? null : decisiveStep(result)
  const v = step?.verdict
  const [lit, setLit] = useState(() => (reducedMotion() ? 4 : 0))

  useEffect(() => {
    if (!v || reducedMotion()) return
    const timers = [1, 2, 3, 4].map((n) => window.setTimeout(() => setLit(n), n * 380))
    return () => timers.forEach(clearTimeout)
  }, [v])

  const check = (name: string) => v?.checks.find((c) => c.check === name)
  const score = (name: string) => { const c = check(name); return c && !c.skipped ? c.risk_score : null }
  const fmt = (n: number | null) => (n === null ? 'skipped' : n.toFixed(2))
  const intent = score('intent')
  const policy = score('policy')
  const tone = v ? DECISION_TONE[v.decision] : null

  const cards: { icon: LucideIcon; n: string; title: string; sub: string; value: number | null; detail: string; flagged: boolean }[] = [
    { icon: Layers, n: '01', title: 'Taint', sub: 'Where did each value come from?', value: score('taint'), detail: fmt(score('taint')), flagged: !!check('taint')?.flagged },
    { icon: Target, n: '02', title: 'Classifier', sub: 'Instructions hidden in data?', value: score('classifier'), detail: fmt(score('classifier')), flagged: !!check('classifier')?.flagged },
    {
      icon: Activity, n: '03', title: 'Intent + Policy', sub: 'Did the user ask? Fixed rules',
      value: Math.max(intent ?? 0, policy ?? 0), detail: `intent ${fmt(intent)} · policy ${fmt(policy)}`,
      flagged: !!check('intent')?.flagged || !!check('policy')?.flagged,
    },
    { icon: Zap, n: '04', title: 'Verdict', sub: 'Allow / Ask / Block + reason (BN/EN)', value: v?.risk_score ?? null, detail: v ? `risk ${v.risk_score.toFixed(2)}` : '', flagged: v?.decision !== 'allow' },
  ]

  return (
    <section className="glass spotlight p-4 sm:p-5">
      <div className="relative">
        <PanelTitle
          icon={Layers}
          title="Evaluation Pipeline"
          sub={step ? `The decisive call of the last run: ${step.tool}(${Object.values(step.args).join(', ')})` : 'Four checks run on every tool call; the stricter of score and policy wins.'}
        />
        <ol className="grid gap-3 sm:grid-cols-2 2xl:grid-cols-4">
          {cards.map(({ icon: Icon, n, title, sub, value, detail, flagged }, i) => {
            const on = !!v && lit > i
            const isVerdict = i === 3
            const barTone = isVerdict && tone ? tone.bar : flagged ? 'bg-bad' : 'bg-ok'
            return (
              <li
                key={n}
                style={{ ['--glow' as string]: on ? (isVerdict && tone ? tone.glow : flagged ? 'rgb(244 63 94 / 0.6)' : 'rgb(16 185 129 / 0.55)') : undefined }}
                className={`ignite tilt relative flex flex-col gap-3 rounded-xl border bg-card2/60 px-3.5 py-3.5 ${on ? 'is-lit border-line2' : 'border-fg/8'} ${v && !on ? 'opacity-50' : ''}`}
              >
                <div className="flex items-center gap-3">
                  <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-fg/10 bg-fg/5"><Icon size={18} aria-hidden /></span>
                  <span className={`rounded-md px-1.5 py-0.5 font-mono text-[0.72rem] font-bold ${on ? 'bg-accent text-accent-ink' : 'bg-fg/8 text-muted'}`}>{n}</span>
                  <span className="min-w-0">
                    <b className="block text-[0.92rem]">{title}</b>
                    <span className="text-[0.76rem] text-muted">{sub}</span>
                  </span>
                </div>
                <FlowBar value={on && value !== null ? value : 0} tone={barTone} busy={scanning} />
                <div className="flex min-h-7 items-center justify-between gap-2 font-mono text-[0.74rem] tabular-nums">
                  <span className={on ? (flagged ? 'text-bad-soft' : 'text-ok-ink') : 'text-muted'}>
                    {scanning ? 'scanning…' : on ? detail : v ? 'waiting' : 'no run yet'}
                  </span>
                  {isVerdict && on && tone && v && (
                    <span key={runId} className={`slam rounded-md border-2 px-2 py-0.5 text-[0.78rem] font-extrabold tracking-wider ${tone.text}`} style={{ borderColor: 'currentColor' }}>
                      {tone.label}
                    </span>
                  )}
                </div>
              </li>
            )
          })}
        </ol>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// recent evaluations: new rows glow once; a row opens the audit drawer

function RecentEvaluations({ scanning }: { scanning: boolean }) {
  const queryClient = useQueryClient()
  // each fetch marks the rows the previous fetch did not have; those glow once
  const { data, error, isPending } = useQuery({
    queryKey: ['audit', 'recent'],
    queryFn: async () => {
      const prev = queryClient.getQueryData<AuditPage & { fresh: string[] }>(['audit', 'recent'])
      const next = await api.audit({ limit: 6 })
      const before = new Set(prev?.records.map((r) => r.id))
      return { ...next, fresh: prev ? next.records.filter((r) => !before.has(r.id)).map((r) => r.id) : [] }
    },
  })
  const [open, setOpen] = useState<AuditRecord | null>(null)
  const fresh = new Set(data?.fresh)

  const auditLink = (
    <Link to="/audit" className="lift inline-flex min-h-10 shrink-0 items-center rounded-xl border border-line2 bg-accent/12 px-3.5 text-sm font-semibold">
      View Audit Log →
    </Link>
  )
  const RiskCell = ({ r }: { r: AuditRecord }) => (
    <div className="flex items-center gap-2">
      <FlowBar value={r.risk_score} tone={DECISION_TONE[r.decision].bar} className="h-1.5 w-20" />
      <span className="font-mono text-[0.78rem] tabular-nums">{r.risk_score.toFixed(2)}</span>
    </div>
  )

  return (
    <section className="glass spotlight p-4 sm:p-5">
      <div className="relative">
        <PanelTitle icon={FileText} title="Recent Evaluations" sub="Click a row for the full audit trace." right={auditLink} />
        {isPending && <div className="flex flex-col gap-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-12" />)}</div>}
        {error && <ErrorNote error={error} />}
        {data && data.records.length === 0 && !scanning && (
          <p className="py-3 text-sm text-muted">No decisions yet. Run a scenario to see AgentShield's first verdict here.</p>
        )}
        {data && (data.records.length > 0 || scanning) && (
          <>
            <div className="hidden overflow-x-auto md:block">
              <table className="w-full text-left text-sm">
                <thead className="text-xs text-muted">
                  <tr className="border-b border-line">
                    <th className="py-2 pr-3 font-medium">Time (UTC)</th>
                    <th className="py-2 pr-3 font-medium">User Request</th>
                    <th className="py-2 pr-3 font-medium">Tool</th>
                    <th className="py-2 pr-3 font-medium">Risk</th>
                    <th className="py-2 pr-3 font-medium">Decision</th>
                    <th className="py-2 font-medium">Reason</th>
                  </tr>
                </thead>
                <tbody>
                  {scanning && (
                    <tr className="border-b border-line/60">
                      <td className="py-3 pr-3 font-mono text-[0.78rem] text-soft">now</td>
                      <td className="py-3 pr-3 text-muted" colSpan={2}>Evaluating the agent’s tool calls…</td>
                      <td className="py-3 pr-3"><FlowBar value={0} tone="bg-mark" busy className="h-1.5 w-20" /></td>
                      <td className="py-3 pr-3 font-mono text-xs text-muted" colSpan={2}>scanning</td>
                    </tr>
                  )}
                  {data.records.map((r) => (
                    <tr
                      key={r.id}
                      tabIndex={0}
                      onClick={() => setOpen(r)}
                      onKeyDown={(e) => (e.key === 'Enter' || e.key === ' ') && (e.preventDefault(), setOpen(r))}
                      aria-label={`Open audit details: ${r.decision} ${r.tool_name}`}
                      className={`cursor-pointer border-b border-line/60 transition-colors hover:bg-accent/6 focus-visible:bg-accent/6 ${fresh.has(r.id) ? 'row-new' : ''}`}
                    >
                      <td className="py-2.5 pr-3 font-mono text-[0.78rem] whitespace-nowrap text-muted tabular-nums">{utcTime(r.timestamp)}</td>
                      <td className="py-2.5 pr-3">{short(r.user_request, 44)}</td>
                      <td className="py-2.5 pr-3"><code className="font-mono text-[0.8rem] text-ok-ink">{r.tool_name}</code></td>
                      <td className="py-2.5 pr-3"><RiskCell r={r} /></td>
                      <td className="py-2.5 pr-3"><DecisionBadge decision={r.decision} /></td>
                      <td className="py-2.5 text-muted">{short(r.reason_en, 70)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <ul className="flex flex-col gap-2.5 md:hidden">
              {scanning && (
                <li className="flex flex-col gap-2 rounded-xl border border-line2 bg-card2/50 px-3.5 py-3">
                  <span className="font-mono text-xs text-soft">now · evaluating…</span>
                  <FlowBar value={0} tone="bg-mark" busy />
                </li>
              )}
              {data.records.map((r) => (
                <li key={r.id}>
                  <button
                    type="button"
                    onClick={() => setOpen(r)}
                    className={`flex w-full flex-col gap-1.5 rounded-xl border border-fg/8 bg-card2/50 px-3.5 py-3 text-left ${fresh.has(r.id) ? 'row-new' : ''}`}
                  >
                    <span className="flex w-full items-center justify-between gap-2">
                      <span className="font-mono text-xs text-muted">{utcTime(r.timestamp)} UTC</span>
                      <DecisionBadge decision={r.decision} />
                    </span>
                    <span className="text-sm font-semibold">{short(r.user_request, 90)}</span>
                    <span className="flex w-full items-center justify-between gap-2">
                      <code className="font-mono text-[0.78rem] text-ok-ink">{r.tool_name}</code>
                      <RiskCell r={r} />
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>
      {open && data && <AuditDrawer record={open} thresholds={data.thresholds} onClose={() => setOpen(null)} />}
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
  const pipelineRef = useRef<HTMLDivElement>(null)
  const [runId, setRunId] = useState(0)
  const [scanning, setScanning] = useState(false)
  const started = useRef(0)
  const timer = useRef(0)
  useEffect(() => () => clearTimeout(timer.current), [])

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

  const scenarioList = useMemo(() => scenarios.data ?? [], [scenarios.data])

  return (
    <div className="flex flex-col gap-5">
      <div>
        <Hero />
        <Kpis />
      </div>

      <div className="grid items-stretch gap-5 xl:grid-cols-[1.2fr_1fr]">
        {scenarios.error ? (
          <ErrorNote error={scenarios.error} />
        ) : scenarioList.length ? (
          <RunCard
            scenarios={scenarioList}
            liveAvailable={overview.data?.live_mode_available ?? false}
            scanning={scanning}
            onRun={(name, mode, approve) => run.mutate({ name, mode, approve })}
          />
        ) : (
          <Skeleton className="h-[460px]" />
        )}
        <HowItWorks flowing={scanning} />
      </div>

      <div ref={pipelineRef} className="scroll-mt-20 lg:scroll-mt-6">
        <Pipeline result={run.data} scanning={scanning} runId={runId} />
      </div>

      <div aria-live="polite">
        {run.error && !scanning && <ErrorNote error={run.error} />}
        {run.data && !scanning && runId > 0 && <RunResultView key={runId} result={run.data} />}
      </div>

      <RecentEvaluations scanning={scanning} />
    </div>
  )
}
