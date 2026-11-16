import { ChevronRight, CircleX, ShieldCheck } from 'lucide-react'
import type { RunResult, RunSide, Step, Verdict } from '../lib/api'
import { taka } from '../lib/format'
import { stagger } from '../lib/motion'
import { CountUp } from './Motion'
import { DecisionBadge } from './ui'

const STEP_BADGE = { allow: '✅ ALLOW', ask_human: '✋ ASK HUMAN', block: '🛑 BLOCK' } as const

function checkLine(v: Verdict): string {
  return v.checks
    .map((c) => `${c.check} ${c.skipped ? 'skipped' : c.risk_score.toFixed(2)}${c.flagged ? ' ⚑' : ''}`)
    .join(' · ')
}

function StepItem({ step, index }: { step: Step; index: number }) {
  const v = step.verdict
  const isMoney = step.tool === 'send_money'
  const stopped = v !== null && v.decision !== 'allow'
  let badge = v ? ` · ${STEP_BADGE[v.decision]}` : ''
  if (v?.decision === 'ask_human') badge += step.stopped_by_shield ? ' → not approved' : ' → 👍 approved'

  return (
    <details open={isMoney || stopped} style={stagger(index + 3)} className="stagger-item group rounded-xl border border-line bg-card">
      <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 px-3.5 py-2 text-sm font-semibold [&::-webkit-details-marker]:hidden">
        <ChevronRight size={15} className="shrink-0 transition-transform group-open:rotate-90" aria-hidden />
        <span>{isMoney ? '💸' : '🔧'} Step {step.number}:</span>
        <code className="font-mono text-[0.8rem] text-[#4BE0A8]">{step.tool}</code>
        <span className="text-[0.82rem]">{badge}</span>
      </summary>
      <div className="flex flex-col gap-2.5 border-t border-line px-3.5 pt-3 pb-3.5">
        <div className="rounded-lg border border-line bg-bg px-3 py-2.5 font-mono text-[0.82rem] break-words whitespace-pre-wrap text-soft">
          {JSON.stringify(step.args)}
        </div>
        {v && (
          <>
            <div className="flex items-center gap-2 text-sm">
              <DecisionBadge decision={v.decision} />
              <span>
                risk {v.risk_score.toFixed(2)} · {Math.round(v.total_latency_ms)} ms
              </span>
            </div>
            <p className="text-[0.98rem] leading-relaxed">
              <b>কারণ:</b> {v.reason_bn}
            </p>
            <p className="text-[0.84rem] leading-relaxed text-muted">Reason: {v.reason_en}</p>
            <p className="text-[0.8rem] text-muted">Checks: {checkLine(v)}</p>
          </>
        )}
        {!step.stopped_by_shield && <p className="text-sm break-words whitespace-pre-wrap text-[#D6E0D9]">{step.result}</p>}
      </div>
    </details>
  )
}

function Side({ side, title, safe }: { side: RunSide; title: string; safe: boolean }) {
  const lost = side.stolen
  return (
    <div className="flex min-w-0 flex-col gap-3">
      <div
        className={`flex items-center gap-2 rounded-xl border px-4 py-2.5 text-[1.05rem] font-bold animate-rise ${
          safe ? 'border-ok/40 bg-ok/10 text-[#4BE0A8]' : 'border-bad/40 bg-bad/10 text-[#FF8A94]'
        }`}
      >
        {safe ? <ShieldCheck size={20} aria-hidden /> : <CircleX size={20} aria-hidden />}
        {title}
      </div>
      <div className="grid grid-cols-2 gap-3">
        <div>
          <div className="text-xs text-muted">Stolen / চুরি হয়েছে</div>
          <div className={`text-[1.55rem] leading-tight font-display font-bold tabular-nums sm:text-[2.1rem] ${lost ? 'text-[#FF6B78]' : 'text-ok'}`}>
            {lost ? <CountUp to={lost} format={(n) => `−${taka(n)}`} /> : '৳ 0'}
          </div>
        </div>
        <div>
          <div className="text-xs text-muted">Balance / ব্যালান্স</div>
          <div className="text-[1.55rem] leading-tight font-display font-bold tabular-nums sm:text-[2.1rem]"><CountUp to={side.end_balance} format={taka} /></div>
        </div>
      </div>
      {lost ? (
        <div role="alert" className="rounded-xl border border-bad/30 bg-bad/15 px-4 py-3 text-[0.95rem] text-[#FF8A94]">
          MONEY STOLEN: {taka(lost)} sent to {side.unauthorized.map((t) => t.to).join(', ')}, which the user never asked for.
        </div>
      ) : (
        <div className="rounded-xl border border-ok/30 bg-ok/12 px-4 py-3 text-[0.95rem] text-[#4BE0A8]">
          Safe: no unauthorized transfers.{side.stopped ? ` AgentShield stopped ${side.stopped} action(s).` : ''}
        </div>
      )}
      <div className="rounded-r-xl border-l-[3px] border-accent bg-card2 px-3.5 py-2.5">
        <b>User:</b> {side.task}
      </div>
      <div className="flex flex-col gap-2">
        {side.steps.map((s, i) => (
          <StepItem key={s.number} step={s} index={i} />
        ))}
      </div>
      <details className="group rounded-xl border border-line bg-card">
        <summary className="flex min-h-11 cursor-pointer list-none items-center gap-2 px-3.5 py-2 text-sm font-semibold [&::-webkit-details-marker]:hidden">
          <ChevronRight size={15} className="transition-transform group-open:rotate-90" aria-hidden />
          Agent's final answer
        </summary>
        <p className="border-t border-line px-3.5 py-3 text-sm break-words whitespace-pre-wrap">{side.final_answer}</p>
      </details>
    </div>
  )
}

export default function RunResultView({ result }: { result: RunResult }) {
  return (
    <div className="flex flex-col gap-3">
      {result.banner && (
        <div
          className={`relative overflow-hidden rounded-card border px-5 py-4 text-[1.1rem] font-bold animate-rise ${
            result.banner.tone === 'saved'
              ? 'border-ok/45 bg-ok/10 text-ok'
              : 'border-[#38D6F5]/45 bg-[#38D6F5]/10 text-[#8BEBFF]'
          }`}
        >
          {result.banner.text}
        </div>
      )}
      {result.mode === 'mock' && <p className="text-sm text-muted">Offline mode: a simulated naive agent. Not a real-model result.</p>}
      {result.recorded_utc && (
        <p className="text-sm text-muted">Replay of a real run recorded {result.recorded_utc} (UTC). Not live.</p>
      )}
      <div className="grid gap-6 xl:grid-cols-2">
        <Side side={result.without} title="Without AgentShield" safe={false} />
        <Side side={result.with} title="With AgentShield" safe />
      </div>
    </div>
  )
}
