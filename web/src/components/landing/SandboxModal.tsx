import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { ArrowRight, Loader2 } from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, type Decision, type SandboxInput, type SandboxSource } from '../../lib/api'
import Modal from '../Modal'

// Visitors type a request, the text the agent read, and the payment the agent wants to make; the demo server
// checks that one send_money call with the real engine (offline intent judge, nothing logged) as they type.

const LANG = { bn: 'Bangla', banglish: 'Banglish', en: 'English' } as Record<string, string>
const DECISION: Record<Decision, { label: string; cls: string; bar: string }> = {
  allow: { label: 'ALLOW', cls: 'border-ok/50 bg-ok/12 text-ok-ink', bar: 'bg-ok' },
  ask_human: { label: 'ASK HUMAN', cls: 'border-warn/50 bg-warn/12 text-warn', bar: 'bg-warn' },
  block: { label: 'BLOCK', cls: 'border-bad/60 bg-bad/15 text-bad-ink shadow-[0_0_40px_-12px_rgba(244,63,94,.7)]', bar: 'bg-bad' },
}
const SOURCES: { value: SandboxSource; label: string }[] = [
  { value: 'tool:email', label: 'an email' },
  { value: 'tool:web', label: 'a web page' },
  { value: 'tool:file', label: 'a file' },
]

function useDebounced<T>(value: T, ms: number) {
  const [v, setV] = useState(value)
  useEffect(() => {
    const t = window.setTimeout(() => setV(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return v
}

const box = 'rounded-xl border border-fg/10 bg-well/30 px-3 py-2.5 text-sm outline-none transition-colors focus:border-line2'
const field = `w-full ${box}`

export default function SandboxModal({ onClose }: { onClose: () => void }) {
  const presets = useQuery({ queryKey: ['sandbox-presets'], queryFn: api.sandboxPresets, staleTime: Infinity })
  const [edited, setEdited] = useState<SandboxInput | null>(null)
  const [picked, setPicked] = useState<string>('e21')

  // until the visitor changes something: the fake Bangla bill from the recorded demo
  const start = useMemo<SandboxInput | null>(() => {
    if (!presets.data) return null
    const p = presets.data.presets.find((x) => x.id === 'e21') ?? presets.data.presets[0]
    return { user_request: presets.data.user_request, content: p.content, source: 'tool:email', to: p.to, amount: p.amount }
  }, [presets.data])
  const input = edited ?? start

  const set = (patch: Partial<SandboxInput>) => setEdited((cur) => {
    const base = cur ?? start
    return base ? { ...base, ...patch } : null
  })
  const applyPreset = (id: string) => {
    const p = presets.data?.presets.find((x) => x.id === id)
    if (!p) return
    setPicked(id)
    set({ content: p.content, to: p.to, amount: p.amount, source: 'tool:email' })
  }

  const debounced = useDebounced(input, 350)
  const valid = !!debounced && debounced.user_request.trim() !== '' && debounced.to.trim() !== '' && debounced.amount > 0
  const check = useQuery({
    queryKey: ['sandbox-check', debounced],
    queryFn: ({ signal }) => api.sandboxCheck(debounced!, signal),
    enabled: valid,
    placeholderData: keepPreviousData,
    retry: false,
    staleTime: Infinity,
  })

  const v = check.data?.verdict
  const d = v ? DECISION[v.decision] : null
  const t = check.data?.thresholds
  const waking = presets.isLoading || (check.isFetching && !check.data)

  return (
    <Modal title="Try AgentShield on your own text" onClose={onClose} wide>
      {presets.isError ? (
        <p className="text-sm text-bad-pale">The demo server did not answer. It may be waking up (about a minute on the free plan); close and try again.</p>
      ) : !input ? (
        <p className="flex items-center gap-2 text-sm text-muted">
          <Loader2 size={16} className="animate-spin" aria-hidden /> Waking the demo server. The first request can take about a minute.
        </p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.1fr_1fr]">
          <div className="flex min-w-0 flex-col gap-4">
            <div>
              <span className="mb-2 block text-xs font-semibold text-muted">Start from a demo email</span>
              <div className="flex flex-wrap gap-2">
                {presets.data!.presets.map((p) => (
                  <button
                    key={p.id}
                    type="button"
                    onClick={() => applyPreset(p.id)}
                    aria-pressed={picked === p.id}
                    className={`lift min-h-9 rounded-full border px-3 text-xs font-semibold ${
                      picked === p.id ? 'border-line2 bg-accent/12 text-soft' : 'border-fg/10 hover:border-line2'
                    }`}
                  >
                    {p.kind === 'normal' ? 'Real rent bill' : 'Fake bill'} · {LANG[p.language] ?? p.language}
                  </button>
                ))}
                <button
                  type="button"
                  onClick={() => { setPicked(''); set({ content: '', to: '', amount: 1000 }) }}
                  aria-pressed={picked === ''}
                  className={`lift min-h-9 rounded-full border px-3 text-xs font-semibold ${picked === '' ? 'border-line2 bg-accent/12 text-soft' : 'border-fg/10 hover:border-line2'}`}
                >
                  Write your own
                </button>
              </div>
            </div>
            <label className="block">
              <span className="mb-1.5 block text-xs font-semibold text-muted">What the user asked the agent</span>
              <input className={field} value={input.user_request} maxLength={600} onChange={(e) => set({ user_request: e.target.value })} />
            </label>
            <div>
              <div className="mb-1.5 flex flex-wrap items-center justify-between gap-2">
                <label htmlFor="sandbox-content" className="text-xs font-semibold text-muted">
                  What the agent read (English, Bangla or Banglish)
                </label>
                <select
                  aria-label="Where the text came from"
                  className="min-h-8 rounded-lg border border-fg/10 bg-well/40 px-2 text-xs"
                  value={input.source}
                  onChange={(e) => set({ source: e.target.value as SandboxSource })}
                >
                  {SOURCES.map((s) => <option key={s.value} value={s.value}>from {s.label}</option>)}
                </select>
              </div>
              <textarea
                id="sandbox-content"
                data-lenis-prevent
                className={`${field} min-h-40 resize-y leading-relaxed`}
                value={input.content}
                maxLength={4000}
                onChange={(e) => { setPicked(''); set({ content: e.target.value }) }}
              />
              {check.data?.found_order && (check.data.found_order.to !== input.to || check.data.found_order.amount !== input.amount) && (
                <button
                  type="button"
                  onClick={() => set({ to: check.data!.found_order!.to, amount: check.data!.found_order!.amount })}
                  className="mt-1.5 text-xs text-soft underline underline-offset-2"
                >
                  The text asks to send {check.data.found_order.amount} to {check.data.found_order.to}. Use that as the payment
                </button>
              )}
            </div>
            <fieldset>
              <legend className="mb-1.5 text-xs font-semibold text-muted">The payment the agent wants to make</legend>
              <div className="flex flex-wrap items-center gap-2 font-mono text-sm">
                <span className="text-soft">send_money(</span>
                <input aria-label="Recipient number" inputMode="numeric" className={`${box} w-40 font-mono`} value={input.to} maxLength={20}
                  onChange={(e) => set({ to: e.target.value })} />
                <input aria-label="Amount in taka" type="number" min={1} className={`${box} w-28 font-mono`} value={input.amount || ''}
                  onChange={(e) => set({ amount: Math.max(0, Math.floor(Number(e.target.value))) })} />
                <span className="text-soft">)</span>
              </div>
              <p className="mt-1.5 text-xs text-muted">
                Saved contacts: {Object.entries(presets.data!.contacts).map(([n, num]) => `${n} ${num}`).join(', ')}.
              </p>
            </fieldset>
          </div>

          <div className="min-w-0" aria-live="polite">
            <div className="glass p-4 sm:p-5">
              <div className="flex items-center justify-between gap-3">
                <span className="font-mono text-[0.72rem] tracking-[0.18em] text-muted uppercase">Decision</span>
                {check.isFetching && <Loader2 size={14} className="animate-spin text-muted" aria-label="Checking" />}
              </div>
              {check.isError && !check.data ? (
                <p className="mt-3 text-sm text-bad-pale">{(check.error as Error).message}</p>
              ) : !v || !d ? (
                <p className="mt-3 text-sm text-muted">{waking ? 'Checking… the first request can take about a minute while the server wakes.' : 'Fill in the request, the number and the amount.'}</p>
              ) : (
                <>
                  <div className="mt-3 flex flex-wrap items-center gap-3">
                    <span className={`inline-flex min-h-10 items-center rounded-xl border px-4 font-mono text-base font-bold tracking-wide transition-colors duration-500 ${d.cls}`}>
                      {d.label}
                    </span>
                    <span className="font-mono text-sm tabular-nums text-ink">risk {v.risk_score.toFixed(2)}</span>
                  </div>
                  {/* risk gauge with the two thresholds */}
                  <div className="relative mt-4 h-2 rounded-full bg-fg/[0.06]" role="img" aria-label={`Risk ${v.risk_score.toFixed(2)} of 1`}>
                    <div className={`fill-bar h-full rounded-full ${d.bar}`} style={{ transform: `scaleX(${Math.max(0.02, v.risk_score)})` }} />
                    {t && [t.ask_human_at, t.block_at].map((x) => (
                      <span key={x} className="absolute -top-1 h-4 w-px bg-fg/40" style={{ left: `${x * 100}%` }} aria-hidden />
                    ))}
                  </div>
                  {t && (
                    <div className="mt-1 flex justify-between font-mono text-[0.68rem] text-muted tabular-nums">
                      <span>0</span><span>ask ≥ {t.ask_human_at}</span><span>block ≥ {t.block_at}</span><span>1</span>
                    </div>
                  )}
                  <ul className="mt-4 flex flex-col gap-2.5">
                    {v.checks.map((c) => (
                      <li key={c.check} className="text-sm">
                        <div className="flex items-center justify-between gap-2">
                          <span className="font-semibold capitalize">{c.check}</span>
                          <span className={`font-mono text-xs tabular-nums ${c.skipped ? 'text-muted' : c.flagged ? 'text-bad-soft' : 'text-ok'}`}>
                            {c.skipped ? 'not needed' : `${c.risk_score.toFixed(2)} ${c.flagged ? 'flagged' : 'clear'}`}
                          </span>
                        </div>
                        <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-fg/[0.06]" aria-hidden>
                          <div className={`fill-bar h-full rounded-full ${c.flagged ? 'bg-bad' : 'bg-ok'}`} style={{ transform: `scaleX(${c.skipped ? 0 : c.risk_score})` }} />
                        </div>
                      </li>
                    ))}
                  </ul>
                  <p className="mt-4 text-sm leading-relaxed">{v.reason_en}</p>
                  <p lang="bn" className="mt-2 text-sm text-body">{v.reason_bn}</p>
                </>
              )}
            </div>
            <p className="mt-3 text-xs leading-relaxed text-muted">
              Runs the real AgentShield engine on the demo server. The intent check uses the offline keyword judge, so no
              LLM is called, and nothing you type is saved. Demo data is fake.
            </p>
            <Link to="/playground" className="mt-3 inline-flex min-h-11 items-center gap-2 text-sm font-bold text-soft hover:text-soft">
              Open the full playground with a real agent <ArrowRight size={15} aria-hidden />
            </Link>
          </div>
        </div>
      )}
    </Modal>
  )
}
