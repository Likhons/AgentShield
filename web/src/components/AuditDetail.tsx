import {
  Braces, CircleCheck, CircleHelp, Clock, Copy, FileText, GitBranch, Layers, Mail, Scale, Shield, ShieldX, SquareTerminal, TriangleAlert, X,
  type LucideIcon,
} from 'lucide-react'
import { useState, type ReactNode } from 'react'
import type { AuditRecord, Decision, Thresholds } from '../lib/api'
import { useToast } from '../lib/toast'
import { riskLevel, utcFull } from '../lib/audit'

const BANNER: Record<Decision, { icon: LucideIcon; color: string; title: string; sub: string; cls: string }> = {
  block: { icon: ShieldX, color: 'var(--color-bad)', title: 'BLOCK', sub: 'Blocked policy or untrusted injection attempt', cls: 'border-bad/40 bg-bad/10' },
  ask_human: { icon: CircleHelp, color: 'var(--color-warn)', title: 'ASK HUMAN', sub: 'Held for explicit human approval', cls: 'border-warn/40 bg-warn/10' },
  allow: { icon: CircleCheck, color: 'var(--color-ok)', title: 'ALLOW', sub: 'Verified safe to execute', cls: 'border-ok/40 bg-ok/10' },
}

function Row({ icon: Icon, label, children }: { icon: LucideIcon; label: string; children: ReactNode }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-line/70 py-2.5 text-sm">
      <span className="flex shrink-0 items-center gap-2 text-muted">
        <Icon size={14} aria-hidden /> {label}
      </span>
      <span className="min-w-0 text-right font-semibold break-words">{children}</span>
    </div>
  )
}

function CopyButton({ text, label }: { text: string; label: string }) {
  const [done, setDone] = useState(false)
  const toast = useToast()
  return (
    <button
      type="button"
      onClick={() => {
        void navigator.clipboard?.writeText(text).then(() => {
          toast(`${label.replace('Copy ', '')[0].toUpperCase()}${label.replace('Copy ', '').slice(1)} copied`)
          setDone(true)
          setTimeout(() => setDone(false), 1500)
        })
      }}
      className="inline-flex min-h-10 items-center gap-1.5 rounded-lg border border-line px-3 text-xs font-semibold hover:border-line2"
    >
      <Copy size={13} aria-hidden /> {done ? 'Copied' : label}
    </button>
  )
}

interface ArgTrace { status?: string; source?: string; origin?: string; value?: string }

/** Where each argument value came from, from the taint check's details. */
function lineage(record: AuditRecord): { arg: string; value: string; from: string; tainted: boolean }[] {
  const taint = record.checks.find((c) => c.check === 'taint')
  const args = (taint?.details?.arguments ?? {}) as Record<string, ArgTrace>
  return Object.entries(args).map(([arg, t]) => {
    const value = t.value ?? String(record.arguments[arg] ?? '')
    if (t.status === 'user') return { arg, value, from: 'the user’s request', tainted: false }
    if (t.status === 'tool_data') return { arg, value, from: `${t.source ?? 'a tool'}${t.origin ? ` (${t.origin})` : ''}`, tainted: true }
    return { arg, value, from: 'not traced (treated as untrusted)', tainted: true }
  })
}

/** The policy rules that matched, the strictest first, and what the rules forced. */
function policyInfo(record: AuditRecord): { rules: string[]; top?: string; forced?: string | null } | null {
  const policy = record.checks.find((c) => c.check === 'policy')
  if (!policy) return null
  const d = (policy.details ?? {}) as { matched_rules?: string[]; top_rule?: string }
  return { rules: d.matched_rules ?? [], top: d.top_rule, forced: policy.forced_decision }
}

export default function AuditDetail({ record, thresholds, onClose }: { record: AuditRecord; thresholds: Thresholds; onClose: () => void }) {
  const b = BANNER[record.decision]
  const risk = riskLevel(record.risk_score, thresholds)
  const args = JSON.stringify(record.arguments, null, 2)
  const time = utcFull(record.timestamp)
  const trace = lineage(record)
  const policy = policyInfo(record)
  const json = JSON.stringify(record, null, 2)

  return (
    <div className="flex flex-col gap-3.5">
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-base font-bold">
          <FileText size={18} className="text-soft" aria-hidden /> Audit Details
        </h2>
        <button type="button" onClick={onClose} aria-label="Close details" className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-line hover:border-line2">
          <X size={17} aria-hidden />
        </button>
      </div>

      <div className={`flex items-center gap-3 rounded-xl border px-3.5 py-3 ${b.cls}`}>
        <b.icon size={20} color={b.color} aria-hidden />
        <div>
          <b style={{ color: b.color }}>{b.title}</b>
          <p className="text-[0.82rem] text-body">{b.sub}</p>
        </div>
      </div>

      <div>
        <Row icon={Clock} label="Time (UTC)">{time}</Row>
        <Row icon={SquareTerminal} label="Tool"><code className="font-mono text-[0.8rem] text-ok-ink">{record.tool_name}</code></Row>
        <Row icon={TriangleAlert} label="Risk Score">
          <span className={`rounded-md border px-2 py-0.5 text-xs font-bold ${risk.cls}`}>
            {record.risk_score.toFixed(2)} · {risk.label}
          </span>
        </Row>
        <Row icon={Shield} label="Event ID"><code className="font-mono text-[0.78rem] text-soft">{record.id}</code></Row>
        <Row icon={Layers} label="Taint / Latency">
          {record.tainted ? 'Tainted' : 'Untainted'} · {record.total_latency_ms.toFixed(2)} ms
        </Row>
        <Row icon={Mail} label="User Request">{record.user_request}</Row>
      </div>

      <section>
        <h3 className="mb-1.5 flex items-center gap-2 text-sm font-bold"><SquareTerminal size={14} className="text-soft" aria-hidden /> Arguments</h3>
        <pre className="overflow-x-auto rounded-lg border border-line bg-bg px-3 py-2.5 font-mono text-[0.8rem] text-soft">{args}</pre>
      </section>

      <section>
        <h3 className="mb-1.5 flex items-center gap-2 text-sm font-bold"><FileText size={14} className="text-soft" aria-hidden /> Reason</h3>
        <div className="rounded-xl border border-line bg-card2/60 px-3.5 py-3">
          <p className="text-[0.98rem] leading-relaxed">{record.reason_bn}</p>
          <p className="mt-2 border-t border-line pt-2 text-[0.84rem] leading-relaxed text-muted">{record.reason_en}</p>
          {record.checks.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {record.checks.map((c) => (
                <span
                  key={c.check}
                  className={`rounded-md border px-2 py-0.5 font-mono text-[0.74rem] ${c.flagged ? 'border-bad/40 bg-bad/10 text-bad-soft' : 'border-line bg-bg text-soft'}`}
                >
                  {c.check}: {c.skipped ? 'skipped' : c.risk_score.toFixed(2)}
                  {c.flagged ? ' ⚑' : ''}
                </span>
              ))}
            </div>
          )}
        </div>
      </section>

      {trace.length > 0 && (
        <section>
          <h3 className="mb-1.5 flex items-center gap-2 text-sm font-bold"><GitBranch size={14} className="text-soft" aria-hidden /> Taint lineage</h3>
          <ul className="flex flex-col gap-1.5">
            {trace.map((t) => (
              <li key={t.arg} className={`flex flex-wrap items-center gap-x-2 gap-y-1 rounded-lg border px-3 py-2 text-[0.82rem] ${t.tainted ? 'border-bad/30 bg-bad/6' : 'border-ok/30 bg-ok/6'}`}>
                <code className="font-mono text-[0.78rem] text-soft">{t.arg}={t.value}</code>
                <span className="text-muted">came from</span>
                <span className={`font-semibold ${t.tainted ? 'text-bad-ink' : 'text-ok-ink'}`}>{t.from}</span>
              </li>
            ))}
          </ul>
        </section>
      )}

      {policy && (
        <section>
          <h3 className="mb-1.5 flex items-center gap-2 text-sm font-bold"><Scale size={14} className="text-soft" aria-hidden /> Policy rule</h3>
          {policy.rules.length === 0 ? (
            <p className="rounded-lg border border-line px-3 py-2 text-[0.82rem] text-muted">No rule matched; the score decided.</p>
          ) : (
            <div className="flex flex-wrap items-center gap-1.5">
              {policy.rules.map((r) => (
                <code key={r} className={`rounded-md border px-2 py-0.5 font-mono text-[0.76rem] ${r === policy.top ? 'border-bad/45 bg-bad/10 text-bad-ink' : 'border-line text-body'}`}>
                  {r}
                </code>
              ))}
              {policy.forced && (
                <p className="w-full text-[0.8rem] text-muted">
                  The rules forced: <b className="text-ink">{policy.forced.replace('_', ' ')}</b> (the strictest rule is highlighted)
                </p>
              )}
            </div>
          )}
        </section>
      )}

      <details className="group rounded-xl border border-line">
        <summary className="flex min-h-11 cursor-pointer list-none items-center justify-between gap-2 px-3.5 text-sm font-bold [&::-webkit-details-marker]:hidden">
          <span className="flex items-center gap-2"><Braces size={14} className="text-soft" aria-hidden /> JSON audit trace</span>
          <span className="text-xs font-normal text-muted group-open:hidden">show</span>
        </summary>
        <pre className="max-h-80 overflow-auto border-t border-line px-3 py-2.5 font-mono text-[0.74rem] leading-relaxed text-soft">{json}</pre>
      </details>

      <div className="flex flex-wrap gap-2">
        <CopyButton text={json} label="Copy JSON trace" />
        <CopyButton text={JSON.stringify(record.arguments)} label="Copy arguments" />
        <CopyButton text={record.id} label="Copy event ID" />
      </div>
    </div>
  )
}
