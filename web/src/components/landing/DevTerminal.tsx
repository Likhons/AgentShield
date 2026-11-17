import { Check, Copy, Play } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { api } from '../../lib/api'

const CURL = `curl -X POST https://<your-gateway>/v1/check \\
  -H "X-API-Key: $AGENTSHIELD_API_KEY" -H "Content-Type: application/json" \\
  -d '{
    "user_request": "Please pay my pending bills from my inbox.",
    "tool_call": {"tool_name": "send_money",
                  "arguments": {"to": "01000000666", "amount": 4500}},
    "context": [{"content": "<the email the agent read>",
                 "source": "tool:email", "origin": "email:e21"}],
    "known_recipients": ["01000000102"]
  }'
# returns {"decision": "block", "risk_score": 0.95, "reason_bn": "আটকানো হয়েছে। …", ...}`

// agentshield/sdk/session.py: wrap() returns the tool unchanged for the agent; a blocked call never runs and
// returns "[AgentShield] <reason>" instead.
const PYTHON = `from agentshield.core.engine import build_default_engine
from agentshield.sdk.session import ShieldSession

session = ShieldSession(
    build_default_engine(),
    user_request="Please pay my pending bills from my inbox.",
    known_recipients=["01000000102"],   # the user's saved contacts
)
read_email = session.wrap("read_email", read_email, source="tool:email")
send_money = session.wrap("send_money", send_money, source="tool:bank")

# give the wrapped tools to your agent
send_money(to="01000000666", amount=4500)
# -> "[AgentShield] Blocked. The transfer to 01000000666 was triggered by untrusted content, ..."`

const TABS = [
  { id: 'curl', label: 'cURL', code: CURL },
  { id: 'python', label: 'Python SDK', code: PYTHON },
] as const

// Shown when the demo server cannot be reached: the verdict of the real run (attack_bill_bn_with.json, 13 Nov 2026).
const RECORDED = {
  decision: 'block',
  risk_score: 0.95,
  reason_bn: 'আটকানো হয়েছে। 01000000666 নম্বরে টাকা পাঠানোর নির্দেশ …',
  checks: { taint: 0.9, classifier: 0.3, intent: 0.9, policy: 0.95 },
  total_latency_ms: 799.4,
}

type Response = { json: Record<string, unknown>; label: string }

const round = (n: number, d = 2) => Math.round(n * 10 ** d) / 10 ** d

function JsonLines({ json }: { json: Record<string, unknown> }) {
  const lines = JSON.stringify(json, null, 2).split('\n')
  return (
    <>
      {lines.map((line, i) => {
        const m = /^(\s*)"([^"]+)":\s?(.*)$/.exec(line)
        return (
          <span key={i} className="json-line block whitespace-pre" style={{ ['--i' as string]: i }}>
            {m ? (
              <>
                {m[1]}<span className="text-[#93C5FD]">"{m[2]}"</span>: <span className={/block/.test(m[3]) ? 'font-bold text-[#FB7185]' : 'text-soft'}>{m[3]}</span>
              </>
            ) : line}
          </span>
        )
      })}
    </>
  )
}

export default function DevTerminal() {
  const [tab, setTab] = useState<(typeof TABS)[number]['id']>('curl')
  const [copied, setCopied] = useState(false)
  const [busy, setBusy] = useState(false)
  const [response, setResponse] = useState<Response | null>(null)
  const [runs, setRuns] = useState(0)
  const timer = useRef(0)
  useEffect(() => () => clearTimeout(timer.current), [])
  const code = TABS.find((t) => t.id === tab)!.code

  const copy = async () => {
    try {
      await navigator.clipboard.writeText(code)
      setCopied(true)
      clearTimeout(timer.current)
      timer.current = window.setTimeout(() => setCopied(false), 1600)
    } catch {
      /* clipboard blocked: the code stays selectable */
    }
  }

  // Sends the fake-bill email from the demo data to the demo server's sandbox endpoint (same engine, offline
  // intent judge, nothing logged). Falls back to the recorded verdict when the server is asleep or unreachable.
  const test = async () => {
    setBusy(true)
    const abort = new AbortController()
    const timeout = window.setTimeout(() => abort.abort(), 12_000)
    try {
      const presets = await api.sandboxPresets()
      const fake = presets.presets.find((p) => p.id === 'e21')!
      const r = await api.sandboxCheck(
        { user_request: presets.user_request, content: fake.content, source: 'tool:email', to: fake.to, amount: fake.amount },
        abort.signal,
      )
      const v = r.verdict
      setResponse({
        label: `Live from the demo server: ${r.judge}`,
        json: {
          decision: v.decision,
          risk_score: round(v.risk_score),
          reason_bn: v.reason_bn.length > 48 ? `${v.reason_bn.slice(0, 48)} …` : v.reason_bn,
          checks: Object.fromEntries(v.checks.map((c) => [c.check, c.skipped ? 'skipped' : round(c.risk_score)])),
          total_latency_ms: round(v.total_latency_ms, 1),
        },
      })
    } catch {
      setResponse({ label: 'Demo server not reachable: verdict recorded from the real run, 13 Nov 2026', json: RECORDED })
    } finally {
      clearTimeout(timeout)
      setRuns((n) => n + 1)
      setBusy(false)
    }
  }

  return (
    <div className="glass spotlight overflow-hidden">
      <div className="relative flex flex-wrap items-center justify-between gap-2 border-b border-white/8 px-3 py-2 sm:px-4">
        <div className="flex items-center gap-3">
          <span className="hidden gap-1.5 sm:flex" aria-hidden>
            <span className="h-2.5 w-2.5 rounded-full bg-[#F43F5E]/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#FFB547]/70" />
            <span className="h-2.5 w-2.5 rounded-full bg-[#10B981]/70" />
          </span>
          <div role="tablist" aria-label="Code example" className="flex gap-1 rounded-lg bg-white/[0.03] p-1">
            {TABS.map((t) => (
              <button
                key={t.id}
                type="button"
                role="tab"
                aria-selected={tab === t.id}
                onClick={() => setTab(t.id)}
                className={`min-h-9 rounded-md px-3 font-mono text-xs transition-colors duration-300 ${
                  tab === t.id ? 'bg-accent/15 text-soft' : 'text-muted hover:text-ink'
                }`}
              >
                {t.label}
              </button>
            ))}
          </div>
        </div>
        <button
          type="button"
          onClick={copy}
          className="lift inline-flex min-h-9 items-center gap-1.5 rounded-lg border border-white/10 px-3 text-xs font-semibold hover:border-line2"
          aria-live="polite"
        >
          {copied ? <Check size={14} className="text-ok" aria-hidden /> : <Copy size={14} aria-hidden />}
          {copied ? 'Copied!' : 'Copy'}
        </button>
      </div>
      <pre role="tabpanel" className="relative overflow-x-auto p-4 font-mono text-[0.78rem] leading-relaxed text-soft sm:p-5">{code}</pre>
      <div className="relative border-t border-white/8 p-4 sm:px-5">
        <button
          type="button"
          onClick={test}
          disabled={busy}
          className="btn-primary lift inline-flex min-h-11 items-center gap-2 rounded-xl px-5 text-sm font-bold disabled:opacity-70"
        >
          <Play size={15} aria-hidden /> {busy ? 'Sending…' : 'Test Request'}
        </button>
        <div aria-live="polite">
          {response && (
            <div key={runs} className="mt-4 rounded-xl border border-bad/30 bg-black/40 p-3.5">
              <div className="mb-2 flex flex-wrap items-center justify-between gap-2 font-mono text-[0.7rem] text-muted">
                <span className="text-ok">200 OK</span>
                <span>{response.label}</span>
              </div>
              <pre className="overflow-x-auto font-mono text-[0.76rem] leading-relaxed text-ink">
                <JsonLines json={response.json} />
              </pre>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
