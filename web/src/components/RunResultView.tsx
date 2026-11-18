import { ChevronRight, CircleAlert, CircleCheck, Hand, Lock, RotateCcw, ShieldCheck, ShieldOff, TrendingDown, Wallet } from 'lucide-react'
import type { Decision, RunResult, RunSide, Step, Verdict } from '../lib/api'
import { taka } from '../lib/format'
import { stagger } from '../lib/motion'
import { CountUp } from './Motion'

// One run, side by side: the same task without and with AgentShield. Every value comes from the run result.

const VERDICT_TAG: Record<Decision, { label: string; cls: string }> = {
  allow: { label: 'ALLOW', cls: 'border-ok/40 bg-ok/10 text-ok-ink' },
  ask_human: { label: 'ASK', cls: 'border-warn/40 bg-warn/10 text-warn-ink' },
  block: { label: 'BLOCK', cls: 'border-bad/45 bg-bad/12 text-bad-ink' },
}
const SOLID: Record<Decision, string> = { allow: 'bg-ok text-[#06140c]', ask_human: 'bg-warn text-[#1a1000]', block: 'bg-bad text-white' }
const STAMP_BN: Record<Decision, string> = { allow: 'অনুমোদিত', ask_human: 'অনুমতি দরকার', block: 'আটকানো' }
const STAMP_EN: Record<Decision, string> = { allow: 'ALLOWED', ask_human: 'HELD', block: 'BLOCKED' }

function CheckTiles({ v }: { v: Verdict }) {
  return (
    <div className="grid grid-cols-2 gap-2 sm:grid-cols-4 xl:grid-cols-2 2xl:grid-cols-4">
      {v.checks.map((c) => (
        <div key={c.check} className="rounded-xl border border-tile-line bg-well/30 px-3 py-2">
          <div className="flex items-center justify-between gap-2 font-mono text-[0.74rem]">
            <span className="text-muted">{c.check}</span>
            <b className={`tabular-nums ${c.skipped ? 'text-muted' : c.flagged ? 'text-bad-ink' : 'text-ok-ink'}`}>{c.skipped ? '—' : c.risk_score.toFixed(2)}</b>
          </div>
          <div className="flow-bar mt-1.5 h-1" aria-hidden>
            <div className={`flow-fill ${c.flagged ? 'bg-bad' : 'bg-ok'}`} style={{ transform: `scaleX(${c.skipped ? 0 : c.risk_score})` }} />
          </div>
        </div>
      ))}
    </div>
  )
}

function StepItem({ step, index, shielded, unauthorized }: { step: Step; index: number; shielded: boolean; unauthorized: boolean }) {
  const v = step.verdict
  const stopped = v !== null && v.decision !== 'allow'
  const open = step.tool === 'send_money' || stopped
  const tone = stopped ? (v!.decision === 'block' ? 'border-bad/45 bg-bad/[0.07]' : 'border-warn/40 bg-warn/[0.06]') : unauthorized ? 'border-bad/45 bg-bad/[0.07]' : 'border-tile-line bg-tile'

  return (
    <details open={open} style={stagger(index + 3)} className={`stagger-item group rounded-2xl border ${tone}`}>
      <summary className="flex min-h-12 cursor-pointer list-none items-center gap-2.5 px-4 py-2.5 [&::-webkit-details-marker]:hidden">
        <ChevronRight size={15} className="shrink-0 text-muted transition-transform group-open:rotate-90" aria-hidden />
        <span className="text-sm text-muted">Step {step.number}:</span>
        <code className="min-w-0 truncate font-mono text-[0.86rem] font-semibold text-ok-ink">{step.tool}</code>
        <span className="ml-auto shrink-0">
          {shielded && v ? (
            <span className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 font-mono text-[0.7rem] font-bold ${VERDICT_TAG[v.decision].cls}`}>
              <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />
              {VERDICT_TAG[v.decision].label}
              {v.decision === 'ask_human' && (step.stopped_by_shield ? ' · NOT APPROVED' : ' · APPROVED')}
            </span>
          ) : unauthorized ? (
            <span className="rounded-md border border-bad/45 bg-bad/12 px-2 py-0.5 font-mono text-[0.7rem] font-bold text-bad-ink">UNAUTHORIZED</span>
          ) : null}
        </span>
      </summary>
      <div className="flex flex-col gap-3 px-4 pb-4">
        <pre className="overflow-x-auto rounded-xl border border-tile-line bg-well/40 px-3.5 py-2.5 font-mono text-[0.82rem] whitespace-pre-wrap text-warn-ink">
          {JSON.stringify(step.args).replace(/,"/g, ', "').replace(/":/g, '": ')}
        </pre>
        {v && shielded && (
          <>
            <div className="relative flex flex-wrap items-center gap-2.5">
              <span className={`rounded-md px-2.5 py-1 font-mono text-[0.78rem] font-extrabold tracking-wide ${SOLID[v.decision]}`}>{VERDICT_TAG[v.decision].label}</span>
              <span className="font-mono text-[0.82rem] text-body tabular-nums">risk {v.risk_score.toFixed(2)} · {v.total_latency_ms < 10 ? v.total_latency_ms.toFixed(1) : Math.round(v.total_latency_ms)} ms</span>
              {v.decision !== 'allow' && (
                <span className={`ml-auto -rotate-3 rounded-md border px-2.5 py-0.5 font-mono text-[0.72rem] font-bold tracking-wider ${VERDICT_TAG[v.decision].cls}`}>
                  {STAMP_EN[v.decision]} · <span lang="bn" className="tracking-normal">{STAMP_BN[v.decision]}</span>
                </span>
              )}
            </div>
            {v.decision !== 'allow' ? (
              <>
                <div className={`rounded-xl border px-4 py-3 ${v.decision === 'block' ? 'border-bad/30 bg-bad/[0.1]' : 'border-warn/30 bg-warn/[0.08]'}`}>
                  <div className={`text-[0.82rem] font-bold ${v.decision === 'block' ? 'text-bad-ink' : 'text-warn-ink'}`} lang="bn">কারণ (বাংলা):</div>
                  <p lang="bn" className="mt-1 text-[0.95rem]">{v.reason_bn}</p>
                </div>
                <div className="rounded-xl border border-tile-line bg-well/30 px-4 py-3">
                  <div className="font-mono text-[0.7rem] tracking-[0.14em] text-muted uppercase">Reason (English):</div>
                  <p className="mt-1 text-[0.9rem] leading-relaxed text-body">{v.reason_en}</p>
                </div>
              </>
            ) : (
              <p className="text-[0.88rem] text-muted"><span lang="bn">{v.reason_bn}</span> · {v.reason_en}</p>
            )}
            <CheckTiles v={v} />
          </>
        )}
        {!step.stopped_by_shield && (
          <p className={`font-mono text-[0.82rem] break-words whitespace-pre-wrap ${unauthorized ? 'font-bold text-ink' : 'text-body'}`}>{step.result}</p>
        )}
      </div>
    </details>
  )
}

function Side({ side, shielded }: { side: RunSide; shielded: boolean }) {
  const lost = side.stolen
  const breached = lost > 0
  const unauthorizedTo = new Set(side.unauthorized.map((t) => t.to))
  const status = breached ? 'COMPROMISED' : shielded ? 'PROTECTED' : 'NO LOSS'
  const statusCls = breached ? 'border-bad/45 bg-bad/12 text-bad-ink' : 'border-ok/40 bg-ok/12 text-ok-ink'
  // '!' because .glass sets its own border and shadow outside Tailwind's layers
  const frame = breached
    ? 'border-bad/35! shadow-[inset_0_1px_0_0_rgba(242,104,90,.6),0_30px_60px_-40px_rgba(242,104,90,.4)]!'
    : 'border-ok/30! shadow-[inset_0_1px_0_0_rgba(95,207,142,.6),0_30px_60px_-40px_rgba(95,207,142,.35)]!'
  const Icon = shielded ? ShieldCheck : ShieldOff

  return (
    <section className={`glass flex min-w-0 flex-col gap-4 p-4 sm:p-6 ${frame}`}>
      <header className="flex items-start justify-between gap-3 border-b border-line pb-4">
        <div className="flex items-center gap-3">
          <span className={`inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-xl border ${breached ? 'border-bad/40 bg-bad/10 text-bad-ink' : 'border-ok/40 bg-ok/10 text-ok-ink'}`}>
            <Icon size={19} aria-hidden />
          </span>
          <div>
            <h3 className="text-[1.15rem] font-bold">{shielded ? 'With AgentShield' : 'Without AgentShield'}</h3>
            <p className={`font-mono text-[0.68rem] tracking-[0.14em] uppercase ${breached ? 'text-bad-soft' : 'text-ok-ink'}`}>
              {shielded ? 'Real-time action firewall' : 'Unprotected agent execution'}
            </p>
          </div>
        </div>
        <span className={`shrink-0 rounded-md border px-2.5 py-1 font-mono text-[0.72rem] font-bold tracking-wide ${statusCls}`}>{status}</span>
      </header>

      <div className="grid grid-cols-2 gap-3">
        <div className={`rounded-2xl border p-4 ${breached ? 'border-bad/35 bg-bad/[0.1]' : 'border-ok/30 bg-ok/[0.07]'}`}>
          <div className="flex items-center justify-between gap-2 text-[0.8rem] text-muted">
            <span>Stolen / <span lang="bn">চুরি গেছে</span></span>
            {breached ? <TrendingDown size={15} className="text-bad-ink" aria-hidden /> : <Lock size={15} className="text-ok-ink" aria-hidden />}
          </div>
          <div className={`mt-1.5 font-display text-[1.6rem] leading-tight font-extrabold tabular-nums sm:text-[2rem] ${breached ? 'text-bad-ink' : 'text-ok-ink'}`}>
            {breached ? <CountUp to={lost} format={(n) => `−${taka(n)}`} /> : '৳ 0'}
          </div>
        </div>
        <div className="rounded-2xl border border-tile-line bg-well/30 p-4">
          <div className="flex items-center justify-between gap-2 text-[0.8rem] text-muted">
            <span>Balance / <span lang="bn">ব্যালেন্স</span></span>
            <Wallet size={15} className="text-soft" aria-hidden />
          </div>
          <div className="mt-1.5 font-display text-[1.6rem] leading-tight font-extrabold tabular-nums sm:text-[2rem]">
            <CountUp to={side.end_balance} format={taka} />
          </div>
        </div>
      </div>

      {breached ? (
        <div role="alert" className="flex items-start gap-2.5 rounded-xl border border-bad/35 bg-bad/[0.12] px-4 py-3 text-[0.95rem] font-semibold text-bad-pale">
          <CircleAlert size={18} className="mt-0.5 shrink-0 text-bad-ink" aria-hidden />
          <span>MONEY STOLEN: {taka(lost)} sent to {side.unauthorized.map((t) => t.to).join(', ')}, which the user never asked for.</span>
        </div>
      ) : (
        <div className="flex items-start gap-2.5 rounded-xl border border-ok/30 bg-ok/[0.1] px-4 py-3 text-[0.95rem] font-semibold text-ok-ink">
          <CircleCheck size={18} className="mt-0.5 shrink-0" aria-hidden />
          <span>Safe: no unauthorized transfers.{side.stopped ? ` AgentShield stopped ${side.stopped} action(s).` : ''}</span>
        </div>
      )}

      <div className="flex items-center gap-3 rounded-xl border border-tile-line bg-well/25 px-3.5 py-2.5">
        <span className={`shrink-0 rounded-md px-2 py-0.5 font-mono text-[0.7rem] font-bold ${shielded ? 'bg-accent/20 text-soft' : 'bg-fg/8 text-muted'}`}>USER</span>
        <span className="min-w-0 text-[0.95rem] font-semibold">{side.task}</span>
      </div>

      <div className="flex flex-col gap-2.5">
        {side.steps.map((s, i) => (
          <StepItem
            key={s.number}
            step={s}
            index={i}
            shielded={shielded}
            unauthorized={!shielded && s.tool === 'send_money' && unauthorizedTo.has(String(s.args.to ?? ''))}
          />
        ))}
      </div>
      <details className="group rounded-2xl border border-tile-line bg-tile">
        <summary className="flex min-h-12 cursor-pointer list-none items-center gap-2.5 px-4 py-2.5 font-semibold [&::-webkit-details-marker]:hidden">
          <ChevronRight size={15} className="text-muted transition-transform group-open:rotate-90" aria-hidden />
          Agent’s final answer
        </summary>
        <p className="border-t border-line px-4 py-3 text-sm break-words whitespace-pre-wrap">{side.final_answer}</p>
      </details>
    </section>
  )
}

// banner look per tone: money saved (ok), held for the user's approval (warn, the ASK colour), anything else (info)
const BANNER = {
  saved: { card: 'border-ok/35!', tile: 'border-ok/40 bg-ok/10 text-ok-ink', en: 'text-soft', bn: 'text-ok-ink', Icon: ShieldCheck },
  held: { card: 'border-warn/40!', tile: 'border-warn/40 bg-warn/10 text-warn-ink', en: 'text-warn-ink', bn: 'text-ink', Icon: Hand },
  neutral: { card: 'border-info/35!', tile: 'border-info/40 bg-info/10 text-info-ink', en: 'text-info-ink', bn: 'text-ok-ink', Icon: ShieldCheck },
} as const

export default function RunResultView({ result, onRerun, rerunning = false }: { result: RunResult; onRerun?: () => void; rerunning?: boolean }) {
  const look = BANNER[result.banner?.tone ?? 'neutral'] ?? BANNER.neutral
  // the banner text from the API starts with an emoji; the icon tile already says it
  // and "৳ 15,000" must not break between the sign and the number
  const [en, bn] = (result.banner?.text ?? '').replace(/^[\p{Extended_Pictographic}️\s]+/u, '').replace(/৳ /g, '৳ ').split(' · ')
  const modeNote = result.mode === 'mock'
    ? 'Offline mode: a simulated naive agent. Not a real-model result.'
    : result.recorded_utc
      ? `Replay of a real run recorded ${result.recorded_utc} (UTC). Not live.`
      : 'Live run with a real model via Groq.'
  const intercepted = result.with.stopped

  return (
    <div className="flex flex-col gap-4">
      <div className={`glass flex flex-col gap-4 p-4 sm:flex-row sm:items-center sm:justify-between sm:p-5 animate-rise ${look.card}`}>
        <div className="flex items-start gap-3.5">
          <span className={`inline-flex h-12 w-12 shrink-0 items-center justify-center rounded-xl border ${look.tile}`}>
            <look.Icon size={22} aria-hidden />
          </span>
          <div className="min-w-0">
            {result.banner ? (
              <p className="text-[1.1rem] leading-snug font-bold sm:text-[1.2rem]">
                <span className={look.en}>{en}</span>
                {bn && <><span className="mx-2 text-muted">·</span><span lang="bn" className={look.bn}>{bn}</span></>}
              </p>
            ) : (
              <p className="text-[1.1rem] font-bold">Run finished</p>
            )}
            <p className="mt-1 flex flex-wrap items-center gap-x-2 text-[0.84rem] text-muted">
              <span>{modeNote}</span>
              {intercepted > 0 && (
                <>
                  <span aria-hidden>•</span>
                  <span className="font-mono text-[0.78rem] text-ok-ink">{intercepted} {intercepted === 1 ? 'action' : 'actions'} intercepted</span>
                </>
              )}
            </p>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <span className="rounded-lg border border-fg/10 bg-well/30 px-3 py-2 font-mono text-[0.76rem] whitespace-nowrap text-muted">
            Starting wallet: <b className="text-ink tabular-nums">{taka(result.with.start_balance)}</b>
          </span>
          {onRerun && (
            <button
              type="button"
              onClick={onRerun}
              disabled={rerunning}
              className="lift inline-flex min-h-10 items-center gap-1.5 rounded-lg border border-accent/40 bg-accent/10 px-3.5 font-mono text-[0.8rem] font-bold whitespace-nowrap text-soft disabled:opacity-60"
            >
              <RotateCcw size={14} className={rerunning ? 'animate-spin' : ''} aria-hidden /> Re-run
            </button>
          )}
        </div>
      </div>

      <div className="grid gap-5 xl:grid-cols-2">
        <Side side={result.without} shielded={false} />
        <Side side={result.with} shielded />
      </div>
    </div>
  )
}
