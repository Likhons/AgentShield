import {
  CircleCheck, CircleHelp, Clock, Copy, FileText, Layers, Mail, Shield, ShieldX, SquareTerminal, TriangleAlert, X,
  type LucideIcon,
} from 'lucide-react'
import { useState, type ReactNode } from 'react'
import type { AuditRecord, Decision, Thresholds } from '../lib/api'
import { useToast } from '../lib/toast'
import { riskLevel, utcFull } from '../lib/audit'

const BANNER: Record<Decision, { icon: LucideIcon; color: string; title: string; sub: string; cls: string }> = {
  block: { icon: ShieldX, color: '#FF526F', title: 'BLOCK', sub: 'Blocked policy or untrusted injection attempt', cls: 'border-bad/40 bg-bad/10' },
  ask_human: { icon: CircleHelp, color: '#FFB547', title: 'ASK HUMAN', sub: 'Held for explicit human approval', cls: 'border-warn/40 bg-warn/10' },
  allow: { icon: CircleCheck, color: '#00D6A0', title: 'ALLOW', sub: 'Verified safe to execute', cls: 'border-ok/40 bg-ok/10' },
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

export default function AuditDetail({ record, thresholds, onClose }: { record: AuditRecord; thresholds: Thresholds; onClose: () => void }) {
  const b = BANNER[record.decision]
  const risk = riskLevel(record.risk_score, thresholds)
  const args = JSON.stringify(record.arguments, null, 2)
  const time = utcFull(record.timestamp)

  return (
    <div className="flex flex-col gap-3.5">
      <div className="flex items-center justify-between gap-2">
        <h2 className="flex items-center gap-2 text-base font-bold">
          <FileText size={18} className="text-accent" aria-hidden /> Audit Details
        </h2>
        <button type="button" onClick={onClose} aria-label="Close details" className="inline-flex h-10 w-10 items-center justify-center rounded-lg border border-line hover:border-line2">
          <X size={17} aria-hidden />
        </button>
      </div>

      <div className={`flex items-center gap-3 rounded-xl border px-3.5 py-3 ${b.cls}`}>
        <b.icon size={20} color={b.color} aria-hidden />
        <div>
          <b style={{ color: b.color }}>{b.title}</b>
          <p className="text-[0.82rem] text-[#D6E0D9]">{b.sub}</p>
        </div>
      </div>

      <div>
        <Row icon={Clock} label="Time (UTC)">{time}</Row>
        <Row icon={SquareTerminal} label="Tool"><code className="font-mono text-[0.8rem] text-[#4BE0A8]">{record.tool_name}</code></Row>
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
        <h3 className="mb-1.5 flex items-center gap-2 text-sm font-bold"><SquareTerminal size={14} className="text-accent" aria-hidden /> Arguments</h3>
        <pre className="overflow-x-auto rounded-lg border border-line bg-bg px-3 py-2.5 font-mono text-[0.8rem] text-soft">{args}</pre>
      </section>

      <section>
        <h3 className="mb-1.5 flex items-center gap-2 text-sm font-bold"><FileText size={14} className="text-accent" aria-hidden /> Reason</h3>
        <div className="rounded-xl border border-line bg-card2/60 px-3.5 py-3">
          <p className="text-[0.98rem] leading-relaxed">{record.reason_bn}</p>
          <p className="mt-2 border-t border-line pt-2 text-[0.84rem] leading-relaxed text-muted">{record.reason_en}</p>
          {record.checks.length > 0 && (
            <div className="mt-2.5 flex flex-wrap gap-1.5">
              {record.checks.map((c) => (
                <span
                  key={c.check}
                  className={`rounded-md border px-2 py-0.5 font-mono text-[0.74rem] ${c.flagged ? 'border-bad/40 bg-bad/10 text-[#FDA4AF]' : 'border-line bg-bg text-soft'}`}
                >
                  {c.check}: {c.skipped ? 'skipped' : c.risk_score.toFixed(2)}
                  {c.flagged ? ' ⚑' : ''}
                </span>
              ))}
            </div>
          )}
        </div>
      </section>

      <div className="flex flex-wrap gap-2">
        <CopyButton text={JSON.stringify(record.arguments)} label="Copy arguments" />
        <CopyButton text={record.id} label="Copy event ID" />
      </div>
    </div>
  )
}
