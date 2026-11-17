import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Activity, ArrowRight, Bug, ChartColumn, CircleCheck, CircleHelp, CircleX, ExternalLink, FileText, Layers, ListChecks,
  Mail, Play, PlayCircle, Radio, ShieldCheck, Target, Workflow, Zap, Bot, type LucideIcon,
} from 'lucide-react'
import { useEffect, useMemo, useRef, useState, type CSSProperties } from 'react'
import { Link } from 'react-router-dom'
import HeroArt from '../components/HeroArt'
import RunResultView from '../components/RunResultView'
import { AnimatedValue } from '../components/Motion'
import { Card, DecisionBadge, ErrorNote, PanelTitle, Skeleton } from '../components/ui'
import { api, type RunMode, type RunResult, type Scenario } from '../lib/api'
import { langLabel, short, taka, utcTime } from '../lib/format'
import { smoothScrollTo, stagger } from '../lib/motion'
import { useToast } from '../lib/toast'

// ---------------------------------------------------------------------------
function Hero() {
  return (
    <div className="grid items-center gap-4 xl:grid-cols-[1.15fr_1fr]">
      <div className="animate-rise">
        <span className="inline-flex items-center gap-1.5 rounded-full border border-line2 bg-accent/15 px-3 py-1 text-xs font-semibold text-soft">
          <Play size={10} fill="#D9FF8A" className="text-soft" aria-hidden /> Playground
        </span>
        <h1 className="mt-4 text-[clamp(1.62rem,6.2vw,2.05rem)] leading-[1.15] font-bold tracking-tight lg:text-[2.6rem]">
          <span className="block">Stop AI Agents from Acting&nbsp;on</span>
          <span className="grad-text">Hidden Instructions</span>
        </h1>
        <p className="mt-4 max-w-[560px] text-[0.94rem] leading-relaxed text-[#BCC8C0] lg:text-base">
          AgentShield checks every tool call before it runs, so an AI agent cannot be tricked into sending money by text
          hidden in emails, web pages or files, in Bangla, Banglish and English.
        </p>
        <div className="mt-5 flex flex-col gap-2.5 sm:flex-row">
          <a
            href="#run-scenario"
            className="inline-flex min-h-11 items-center justify-center gap-2 btn-primary rounded-xl px-5 font-bold transition hover:-translate-y-px"
          >
            <Play size={14} fill="currentColor" aria-hidden /> Try a Scenario
          </a>
          <Link
            to="/benchmarks"
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-line2 bg-card/70 px-5 font-bold transition hover:bg-accent/12"
          >
            <ChartColumn size={16} aria-hidden /> View Benchmarks
          </Link>
        </div>
      </div>
      <HeroArt />
    </div>
  )
}

// ---------------------------------------------------------------------------
function Kpi({ icon: Icon, tint, num, label, note }: { icon: LucideIcon; tint: string; num: string; label: string; note: string }) {
  return (
    <div className="card flex flex-col items-start gap-2 p-3.5 transition hover:-translate-y-0.5 hover:border-line2 sm:flex-row sm:items-center sm:gap-4 sm:p-5">
      <span
        className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl sm:h-12 sm:w-12"
        style={{ background: `${tint}1F`, border: `1px solid ${tint}48` }}
      >
        <Icon size={22} color={tint} aria-hidden />
      </span>
      <div className="min-w-0">
        <div className="text-[1.45rem] leading-none font-display font-bold tabular-nums sm:text-[1.7rem]"><AnimatedValue value={num} /></div>
        <div className="mt-1 text-[0.8rem] font-semibold sm:text-sm">{label}</div>
        <div className="mt-0.5 text-[0.72rem] text-muted sm:text-xs">{note}</div>
      </div>
    </div>
  )
}

function Kpis() {
  const { data } = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  if (!data)
    return (
      <div className="my-6 grid grid-cols-2 gap-2.5 sm:gap-4 xl:grid-cols-4" aria-hidden>
        {[0, 1, 2, 3].map((i) => <Skeleton key={i} className="h-[118px]" />)}
      </div>
    )
  const byLang = Object.entries(data.attack_samples.by_language).sort(([a], [b]) => a.localeCompare(b))
  const real = data.real_llm
  return (
    <div className="my-6 grid grid-cols-2 gap-2.5 sm:gap-4 xl:grid-cols-4">
      <Kpi icon={ShieldCheck} tint="#D4FF2A" num={String(data.checks.length)} label="Checks per Tool Call"
        note={data.checks.map((c) => c[0].toUpperCase() + c.slice(1)).join(' · ')} />
      <Kpi icon={ListChecks} tint="#38D6F5" num={String(data.policy_rules)} label="Policy Rules" note="Deterministic · default.yaml" />
      <Kpi icon={Bug} tint="#F04452" num={String(data.attack_samples.total)} label="Attack Samples"
        note={byLang.map(([k, v]) => `${langLabel(k)} ${v}`).join(' · ')} />
      <Kpi icon={ChartColumn} tint="#16C784" num={real ? `${real.with.hits}/${real.with.total}` : '–'} label="Attacks that Moved Money"
        note={real ? `Real LLM · ${real.without.hits}/${real.without.total} without AgentShield` : 'No real-LLM run yet'} />
    </div>
  )
}

// ---------------------------------------------------------------------------
const MODES: { id: RunMode; label: string; caption: string; icon: LucideIcon }[] = [
  { id: 'mock', label: 'Offline (simulated)', caption: 'Simulated naive agent. Works offline.', icon: Bot },
  { id: 'groq', label: 'Live (Groq)', caption: 'Real model via Groq, same tools. Can take up to a minute.', icon: Radio },
  { id: 'recorded', label: 'Recorded Run', caption: 'Instant replay of a saved real run.', icon: PlayCircle },
]

const scenarioLabel = (s: Scenario) => `${s.kind === 'attack' ? '⚠️ Attack' : '✅ Normal'}: ${s.description}`

function RunCard({
  scenarios, liveAvailable, running, onRun,
}: {
  scenarios: Scenario[]
  liveAvailable: boolean
  running: boolean
  onRun: (name: string, mode: RunMode, approve: boolean) => void
}) {
  const [name, setName] = useState(() => (scenarios.some((s) => s.name === 'attack_email_bn') ? 'attack_email_bn' : scenarios[0]?.name))
  const [mode, setMode] = useState<RunMode>('mock')
  const [approve, setApprove] = useState(false)
  const selected = scenarios.find((s) => s.name === name)
  const disabled = (m: RunMode) => (m === 'groq' && !liveAvailable) || (m === 'recorded' && !selected?.has_recording)
  const effectiveMode = disabled(mode) ? 'mock' : mode

  return (
    <section id="run-scenario" className="card flex scroll-mt-20 flex-col gap-4 border-line2 p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="flex items-start gap-2.5">
          <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-accent text-accent-ink">
            <Play size={17} fill="currentColor" aria-hidden />
          </span>
          <div>
            <h2 className="text-[1.15rem] font-bold">Run a Safety Scenario</h2>
            <p className="mt-0.5 text-sm text-muted">
              Test the same task on an unprotected agent and on an agent protected by AgentShield.
            </p>
          </div>
        </div>
        <span className="inline-flex shrink-0 items-center gap-1.5 rounded-full border border-ok/40 bg-ok/12 px-2.5 py-1 text-xs font-bold text-ok">
          <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-ok" aria-hidden /> Ready
        </span>
      </div>

      <label className="flex flex-col gap-1.5 text-sm font-semibold">
        Scenario
        <select
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="min-h-11 w-full rounded-xl border border-line bg-card2 px-3 text-[0.95rem] font-normal text-ink"
        >
          {scenarios.map((s) => (
            <option key={s.name} value={s.name}>
              {scenarioLabel(s)}
            </option>
          ))}
        </select>
      </label>

      <fieldset className="flex flex-col gap-1.5">
        <legend className="mb-1.5 text-sm font-semibold">Agent Mode</legend>
        <div className="grid gap-2 md:grid-cols-3">
          {MODES.map(({ id, label, caption, icon: Icon }) => {
            const off = disabled(id)
            const active = effectiveMode === id
            return (
              <label
                key={id}
                className={`relative flex min-h-[54px] cursor-pointer flex-col gap-0.5 rounded-xl border py-3 pr-9 pl-3.5 transition ${
                  active ? 'border-accent2/70 bg-accent/15 shadow-[0_0_0_1px_rgba(212,255,42,.17)]' : 'border-line bg-card2/60 hover:border-line2'
                } ${off ? 'cursor-not-allowed opacity-45' : ''}`}
              >
                <input type="radio" name="mode" value={id} checked={active} disabled={off} onChange={() => setMode(id)} className="sr-only" />
                <span className="flex items-center gap-2 text-sm font-bold">
                  <Icon size={15} aria-hidden /> {label}
                </span>
                <span className="text-[0.8rem] text-muted">
                  {id === 'groq' && !liveAvailable ? 'Off on this server (no API key).' : id === 'recorded' && off ? 'No recording for this scenario.' : caption}
                </span>
                {active && (
                  <span className="absolute top-2.5 right-2.5 inline-flex h-5 w-5 items-center justify-center rounded-full bg-accent text-[0.75rem] text-accent-ink" aria-hidden>
                    ✓
                  </span>
                )}
              </label>
            )
          })}
        </div>
      </fieldset>

      <label className={`flex items-start gap-2.5 text-sm ${effectiveMode === 'recorded' ? 'opacity-45' : ''}`}>
        <input
          type="checkbox"
          checked={approve}
          disabled={effectiveMode === 'recorded'}
          onChange={(e) => setApprove(e.target.checked)}
          className="mt-0.5 h-4.5 w-4.5 shrink-0 accent-[#D4FF2A]"
        />
        <span>
          I approve actions that ask for my approval (simulated human click)
          <span className="mt-0.5 block text-xs text-muted">
            Unticked = the user says no. BLOCK decisions are never sent to the user.
          </span>
        </span>
      </label>

      <button
        type="button"
        disabled={running || !name}
        onClick={() => name && onRun(name, effectiveMode, approve)}
        className="inline-flex min-h-12 items-center justify-center gap-2 btn-primary rounded-xl font-bold transition hover:-translate-y-px disabled:translate-y-0 disabled:opacity-60"
      >
        {running ? (
          <>
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" aria-hidden /> Agent is working…
          </>
        ) : (
          <>
            <Play size={15} fill="currentColor" aria-hidden /> Run Scenario
          </>
        )}
      </button>
    </section>
  )
}

// ---------------------------------------------------------------------------
function HowItWorks() {
  const nodes = [
    { icon: Mail, color: '#FB7185', title: 'Untrusted input', sub: 'email · web · file', cls: 'border-bad/40 bg-bad/8' },
    { icon: ShieldCheck, color: '#EEFFC2', title: 'AgentShield', sub: 'checks each tool call', cls: 'border-accent2/70 bg-accent/18 shadow-[0_0_28px_rgba(212,255,42,.23)]' },
    { icon: CircleCheck, color: '#16C784', title: 'Decision', sub: 'allow · ask · block', cls: 'border-ok/40 bg-ok/8' },
  ]
  const decisions = [
    { icon: CircleCheck, color: '#16C784', title: 'ALLOW', sub: "Action follows from the user's request", cls: 'border-ok/40 bg-ok/8' },
    { icon: CircleHelp, color: '#F5A623', title: 'ASK', sub: 'Uncertain: the user approves or rejects', cls: 'border-warn/40 bg-warn/8' },
    { icon: CircleX, color: '#F04452', title: 'BLOCK', sub: 'Clear attack or policy violation', cls: 'border-bad/40 bg-bad/8' },
  ]
  return (
    <Card className="h-full">
      <PanelTitle icon={Workflow} title="How AgentShield Works" />
      <div className="flex flex-col items-stretch gap-1.5 md:flex-row md:items-center">
        {nodes.map(({ icon: Icon, color, title, sub, cls }, i) => (
          <div key={title} className="contents">
            {i > 0 && <ArrowRight size={20} className="mx-auto shrink-0 rotate-90 text-muted md:rotate-0" aria-hidden />}
            <div className={`flex flex-1 flex-col items-center gap-1 rounded-xl border px-3 py-4 text-center ${cls}`}>
              <span className="inline-flex h-9 w-9 items-center justify-center rounded-lg bg-white/5">
                <Icon size={20} color={color} aria-hidden />
              </span>
              <b className="text-[0.95rem]">{title}</b>
              <span className="text-xs text-muted">{sub}</span>
            </div>
          </div>
        ))}
      </div>
      <div className="mt-5">
        <PanelTitle icon={ChartColumn} title="Decision Types" />
        <div className="grid gap-2 md:grid-cols-3">
          {decisions.map(({ icon: Icon, color, title, sub, cls }) => (
            <div key={title} className={`rounded-xl border px-3.5 py-3 ${cls}`}>
              <div className="flex items-center gap-2 font-bold">
                <Icon size={19} color={color} aria-hidden /> {title}
              </div>
              <p className="mt-1 text-[0.8rem] text-muted">{sub}</p>
            </div>
          ))}
        </div>
      </div>
    </Card>
  )
}

function Pipeline() {
  const steps: { icon: LucideIcon; title: string; sub: string }[] = [
    { icon: Layers, title: 'Taint Analysis', sub: 'Where did each value come from?' },
    { icon: Target, title: 'Injection Classifier', sub: 'Instructions hidden in data?' },
    { icon: Activity, title: 'Intent + Policy', sub: 'Did the user ask? Fixed rules' },
    { icon: Zap, title: 'Agent Decision', sub: 'Allow / Ask / Block + reason (BN/EN)' },
  ]
  return (
    <Card>
      <PanelTitle icon={Layers} title="Evaluation Pipeline" sub="Four checks run on every tool call; the stricter of score and policy wins." />
      <ol className="grid gap-2 sm:grid-cols-2 2xl:grid-cols-4">
        {steps.map(({ icon: Icon, title, sub }, i) => (
          <li
            key={title}
            style={{ '--scan-delay': `${i * 0.7}s` } as CSSProperties}
            className="pipe-node relative flex items-center gap-3 rounded-xl border border-line2/60 bg-card2/60 px-3.5 py-3"
          >
            <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-lg border border-line bg-white/5">
              <Icon size={18} aria-hidden />
            </span>
            <span className="rounded-md bg-accent text-accent-ink px-1.5 py-0.5 font-mono text-[0.72rem] font-bold">
              0{i + 1}
            </span>
            <span className="min-w-0">
              <b className="block text-[0.92rem]">{title}</b>
              <span className="text-[0.78rem] text-muted">{sub}</span>
            </span>
          </li>
        ))}
      </ol>
    </Card>
  )
}

function RecentEvaluations() {
  const { data, error, isPending } = useQuery({ queryKey: ['audit', 'recent'], queryFn: () => api.audit({ limit: 5 }) })
  const auditLink = (
    <Link to="/audit" className="inline-flex min-h-10 shrink-0 items-center rounded-xl border border-line2 bg-accent/18 px-3.5 text-sm font-semibold">
      View Audit Log →
    </Link>
  )
  return (
    <Card>
      <PanelTitle icon={FileText} title="Recent Evaluations" right={auditLink} />
      {isPending && <div className="flex flex-col gap-2">{[0, 1, 2].map((i) => <Skeleton key={i} className="h-12" />)}</div>}
      {error && <ErrorNote error={error} />}
      {data && data.records.length === 0 && (
        <p className="py-3 text-sm text-muted">No decisions yet. Run a scenario to see AgentShield's first verdict here.</p>
      )}
      {data && data.records.length > 0 && (
        <>
          <div className="hidden overflow-x-auto md:block">
            <table className="w-full text-left text-sm">
              <thead className="text-xs text-muted">
                <tr className="border-b border-line">
                  <th className="py-2 pr-3 font-medium">Time (UTC)</th>
                  <th className="py-2 pr-3 font-medium">User Request</th>
                  <th className="py-2 pr-3 font-medium">Tool</th>
                  <th className="py-2 pr-3 font-medium">Decision</th>
                  <th className="py-2 pr-3 font-medium">Reason</th>
                  <th className="py-2 font-medium" />
                </tr>
              </thead>
              <tbody>
                {data.records.map((r, i) => (
                  <tr key={r.id} style={stagger(i)} className="stagger-item border-b border-line/60 transition hover:bg-accent/6">
                    <td className="py-2.5 pr-3 whitespace-nowrap text-muted">{utcTime(r.timestamp)}</td>
                    <td className="py-2.5 pr-3">{short(r.user_request, 48)}</td>
                    <td className="py-2.5 pr-3"><code className="font-mono text-[0.8rem] text-[#4BE0A8]">{r.tool_name}</code></td>
                    <td className="py-2.5 pr-3"><DecisionBadge decision={r.decision} /></td>
                    <td className="py-2.5 pr-3 text-muted">{short(r.reason_en, 90)}</td>
                    <td className="py-2.5">
                      <Link to={`/audit?id=${r.id}`} aria-label="Open in Audit Log" className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-line hover:border-line2">
                        <ExternalLink size={13} aria-hidden />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <ul className="flex flex-col gap-2.5 md:hidden">
            {data.records.map((r, i) => (
              <li key={r.id} style={stagger(i)} className="stagger-item flex flex-col gap-1.5 rounded-xl border border-line2/50 bg-card2/50 px-3.5 py-3">
                <div className="flex items-center justify-between gap-2">
                  <span className="text-xs text-muted">{utcTime(r.timestamp)} UTC</span>
                  <DecisionBadge decision={r.decision} />
                </div>
                <p className="text-sm font-semibold">{short(r.user_request, 90)}</p>
                <p className="text-[0.8rem] text-muted">{short(r.reason_en, 110)}</p>
                <div className="flex items-center justify-between">
                  <code className="rounded-md border border-line bg-bg px-2 py-0.5 font-mono text-[0.78rem] text-[#4BE0A8]">{r.tool_name}</code>
                  <Link to={`/audit?id=${r.id}`} aria-label="Open in Audit Log" className="inline-flex h-10 w-11 items-center justify-center rounded-lg border border-line">
                    <ExternalLink size={15} aria-hidden />
                  </Link>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </Card>
  )
}

// ---------------------------------------------------------------------------
export default function Playground() {
  const queryClient = useQueryClient()
  const toast = useToast()
  const overview = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  const scenarios = useQuery({ queryKey: ['scenarios'], queryFn: api.scenarios, staleTime: Infinity })
  const resultsRef = useRef<HTMLDivElement>(null)
  const [runId, setRunId] = useState(0)

  const run = useMutation<RunResult, Error, { name: string; mode: RunMode; approve: boolean }>({
    mutationFn: ({ name, mode, approve }) => api.run(name, mode, approve),
    onSuccess: (result) => {
      const saved = result.without.stolen - result.with.stolen
      toast(saved > 0 ? `Run finished: AgentShield kept ${taka(saved)} in the account` : 'Run finished')
      setRunId((n) => n + 1)
      void queryClient.invalidateQueries({ queryKey: ['audit'] })
      void queryClient.invalidateQueries({ queryKey: ['overview'] })
    },
  })

  // bring the result into view: on a phone it would start below the fold
  useEffect(() => {
    if (!runId) return
    if (resultsRef.current) smoothScrollTo(resultsRef.current)
  }, [runId])

  const scenarioList = useMemo(() => scenarios.data ?? [], [scenarios.data])

  return (
    <div className="flex flex-col gap-5">
      <div>
        <Hero />
        <Kpis />
      </div>

      <div className="grid items-stretch gap-5 xl:grid-cols-[1.25fr_1fr]">
        {scenarios.error ? (
          <ErrorNote error={scenarios.error} />
        ) : scenarioList.length ? (
          <RunCard
            scenarios={scenarioList}
            liveAvailable={overview.data?.live_mode_available ?? false}
            running={run.isPending}
            onRun={(name, mode, approve) => run.mutate({ name, mode, approve })}
          />
        ) : (
          <Skeleton className="h-[420px]" />
        )}
        {/* beside the run card on wide screens; below the results once columns stack */}
        <div className="hidden xl:block">
          <HowItWorks />
        </div>
      </div>

      <div ref={resultsRef} className="scroll-mt-20 lg:scroll-mt-6" aria-live="polite">
        {run.error && <ErrorNote error={run.error} />}
        {run.data && <RunResultView key={runId} result={run.data} />}
      </div>

      <div className="xl:hidden">
        <HowItWorks />
      </div>
      <Pipeline />
      <RecentEvaluations />
    </div>
  )
}
