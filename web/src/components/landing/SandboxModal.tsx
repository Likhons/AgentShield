import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { ArrowRight, Loader2 } from 'lucide-react'
import { Fragment, useEffect, useMemo, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { api, type Decision, type SandboxInput, type SandboxSource } from '../../lib/api'
import Modal from '../Modal'

// Visitors type a request, the text the agent read, and the payment the agent wants to make; the demo server
// checks that one send_money call with the real engine (offline intent judge, nothing logged) as they type.

const LANG: Record<string, ReactNode> = { bn: <span lang="bn">বাংলা</span>, banglish: 'Banglish', en: 'English' }
const DECISION: Record<Decision, { word: string; bn: string; ink: string; pin: string }> = {
  allow: { word: 'Allow', bn: 'অনুমোদিত', ink: 'text-ok-ink', pin: 'bg-ok' },
  ask_human: { word: 'Ask the user', bn: 'অনুমতি দরকার', ink: 'text-warn-ink', pin: 'bg-warn' },
  block: { word: 'Block', bn: 'আটকানো', ink: 'text-bad-ink', pin: 'bg-bad' },
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

const field = 'w-full rounded-xl border border-tile-line bg-well/25 px-3.5 py-2.5 text-[0.92rem] outline-none transition-colors focus:border-line2'
/** Inputs inside the send_money(...) line: no box, just an underline, so the line still reads as one call. */
const inline = 'border-0 border-b border-dashed border-fg/25 bg-transparent px-1 py-0.5 font-mono text-[0.95rem] text-ink outline-none transition-colors focus:border-solid focus:border-mark'

/** One step of the story on the left rail: a dot on the line, a label, then the field. */
function Step({ dot, label, aside, htmlFor, children }: { dot: string; label: ReactNode; aside?: ReactNode; htmlFor?: string; children: ReactNode }) {
  return (
    <li className="relative">
      <span className={`absolute top-[0.32rem] -left-[1.62rem] h-3 w-3 rounded-full ring-4 ring-card ${dot}`} aria-hidden />
      <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
        <label htmlFor={htmlFor} className="text-[0.88rem] font-semibold text-ink">{label}</label>
        {aside}
      </div>
      {children}
    </li>
  )
}

/** The short reason: the decision plus the sentence that says why (two sentences; Bangla ends them with the
 *  danda). The rest sits behind "Full reason". */
const firstSentence = (text: string, bangla = false) => {
  const mark = bangla ? '।' : '. '
  const first = text.indexOf(mark)
  const second = first === -1 ? -1 : text.indexOf(mark, first + 1)
  return second === -1 ? text : text.slice(0, second + 1)
}

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
  // real bills first, then the fake ones, so the control reads: real | fake (three languages) | blank
  const ordered = presets.data ? [...presets.data.presets].sort((a, b) => Number(a.kind !== 'normal') - Number(b.kind !== 'normal')) : []
  const fakes = ordered.filter((p) => p.kind !== 'normal')
  const fakePicked = fakes.some((p) => p.id === picked)

  return (
    <Modal
      title="Try it on your own text"
      onClose={onClose}
      wide
      footer={
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
          <p className="font-mono text-[0.72rem] text-muted">real engine · offline judge, no LLM call · nothing saved · fake demo data</p>
          <Link to="/playground" className="btn-primary lift inline-flex min-h-11 shrink-0 items-center justify-center gap-2 rounded-xl px-5 text-sm font-bold">
            Try it with a real agent <ArrowRight size={15} aria-hidden />
          </Link>
        </div>
      }
    >
      {presets.isError ? (
        <p className="text-sm text-bad-pale">The demo server did not answer. It may be waking up (about a minute on the free plan); close and try again.</p>
      ) : !input ? (
        <p className="flex items-center gap-2 text-sm text-muted">
          <Loader2 size={16} className="animate-spin" aria-hidden /> Waking the demo server. The first request can take about a minute.
        </p>
      ) : (
        <div className="grid gap-6 lg:grid-cols-[1.15fr_1fr] lg:gap-8">
          {/* phones: the verdict panel sits under the form, so a slim live summary stays pinned at the top */}
          {v && d && (
            <button
              type="button"
              onClick={() => document.getElementById('sandbox-verdict')?.scrollIntoView({ behavior: 'smooth', block: 'start' })}
              className="sticky -top-4 z-10 -mx-4 -mt-4 flex items-center justify-between gap-3 border-b border-line bg-card/95 px-4 py-2.5 backdrop-blur sm:-mx-5 sm:px-5 lg:hidden"
            >
              <span className="flex items-baseline gap-2">
                <span className={`font-display text-[1.15rem] font-semibold ${d.ink}`}>{d.word}</span>
                <span className="font-mono text-[0.78rem] text-muted tabular-nums">risk {v.risk_score.toFixed(2)}</span>
              </span>
              <span className="text-[0.78rem] text-muted">why ↓</span>
            </button>
          )}
          <div className="flex min-w-0 flex-col gap-6">
            {/* examples: one quiet segmented control instead of a cloud of pills */}
            <div className="min-w-0">
              <span className="mb-2 block text-[0.8rem] text-muted">Start from an example</span>
              <div role="group" aria-label="Examples" className="flex max-w-full gap-1 overflow-x-auto rounded-xl border border-tile-line bg-fg/[0.025] p-1 [mask-image:linear-gradient(90deg,#000_82%,transparent)] [scrollbar-width:none] sm:[mask-image:none]">
                {ordered.map((p, i) => (
                  <Fragment key={p.id}>
                    {/* fake bills share one label, so each button only names its language */}
                    {p.kind !== 'normal' && (i === 0 || ordered[i - 1].kind === 'normal') && (
                      <>
                        {i > 0 && <span className="my-1.5 w-px shrink-0 bg-line2" aria-hidden />}
                        {/* the group name is a button too: it picks the Bangla fake bill (the one from the recorded run) */}
                        <button
                          type="button"
                          onClick={() => applyPreset((fakes.find((x) => x.language === 'bn') ?? fakes[0]).id)}
                          aria-label="Fake bill (Bangla)"
                          className={`flex min-h-9 shrink-0 items-center gap-1 rounded-lg pr-1 pl-2 text-[0.78rem] transition-colors duration-300 hover:text-ink ${
                            fakePicked ? 'text-ink' : 'text-muted'
                          }`}
                        >
                          Fake bill <span className="text-muted" aria-hidden>›</span>
                        </button>
                      </>
                    )}
                    <button
                      type="button"
                      onClick={() => applyPreset(p.id)}
                      aria-pressed={picked === p.id}
                      aria-label={`${p.kind === 'normal' ? 'Real rent bill' : 'Fake bill'}, ${p.language}`}
                      className={`min-h-9 shrink-0 rounded-lg px-3 text-[0.82rem] font-semibold whitespace-nowrap transition-colors duration-300 ${
                        picked === p.id ? 'bg-fg/[0.09] text-ink shadow-[inset_0_0_0_1px_var(--color-line2)]' : 'text-body hover:bg-fg/[0.04]'
                      }`}
                    >
                      {p.kind === 'normal' ? 'Real rent' : (LANG[p.language] ?? p.language)}
                    </button>
                  </Fragment>
                ))}
                <span className="my-1.5 w-px shrink-0 bg-line2" aria-hidden />
                <button
                  type="button"
                  onClick={() => { setPicked(''); set({ content: '', to: '', amount: 1000 }) }}
                  aria-pressed={picked === ''}
                  className={`min-h-9 shrink-0 rounded-lg px-3 text-[0.82rem] font-semibold whitespace-nowrap transition-colors duration-300 ${
                    picked === '' ? 'bg-fg/[0.09] text-ink shadow-[inset_0_0_0_1px_var(--color-line2)]' : 'text-body hover:bg-fg/[0.04]'
                  }`}
                >
                  Blank
                </button>
              </div>
            </div>

            {/* the story, top to bottom on one rail: what the user said, what the agent read, what it wants to do */}
            <ol className="relative flex flex-col gap-6 pl-7">
              <span className="absolute top-2 bottom-3 left-[0.47rem] w-px bg-gradient-to-b from-fg/25 via-warn/40 to-mark/50" aria-hidden />
              <Step dot="bg-fg/60" label="The user asks" htmlFor="sandbox-request">
                <input id="sandbox-request" className={field} value={input.user_request} maxLength={600} onChange={(e) => set({ user_request: e.target.value })} />
              </Step>

              <Step
                dot="bg-warn"
                htmlFor="sandbox-content"
                label="The agent reads"
                aside={
                  <select
                    aria-label="Where the text came from"
                    className="min-h-8 rounded-lg border border-transparent bg-transparent px-1.5 text-[0.8rem] text-muted hover:border-tile-line focus:border-line2"
                    value={input.source}
                    onChange={(e) => set({ source: e.target.value as SandboxSource })}
                  >
                    {SOURCES.map((s) => <option key={s.value} value={s.value}>from {s.label}</option>)}
                  </select>
                }
              >
                <textarea
                  id="sandbox-content"
                  data-lenis-prevent
                  placeholder="Paste an email, web page or file text, in English, Bangla or Banglish"
                  className={`${field} max-h-60 min-h-36 resize-y text-[0.88rem] leading-relaxed`}
                  value={input.content}
                  maxLength={4000}
                  onChange={(e) => { setPicked(''); set({ content: e.target.value }) }}
                />
                {check.data?.found_order && (check.data.found_order.to !== input.to || check.data.found_order.amount !== input.amount) && (
                  <button
                    type="button"
                    onClick={() => set({ to: check.data!.found_order!.to, amount: check.data!.found_order!.amount })}
                    className="mt-2 inline-flex items-center gap-1.5 rounded-lg border border-tile-line px-2.5 py-1 text-[0.78rem] text-body hover:border-line2"
                  >
                    The text asks for {check.data.found_order.amount} to {check.data.found_order.to}: use it <ArrowRight size={12} aria-hidden />
                  </button>
                )}
              </Step>

              <Step dot="bg-mark" label="The agent wants to run">
                <div className="flex flex-wrap items-baseline gap-x-1 gap-y-2 rounded-xl border border-tile-line bg-well/25 px-3.5 py-3 font-mono text-[0.95rem]">
                  <span className="text-soft">send_money(</span>
                  <input aria-label="Recipient number" inputMode="numeric" className={`${inline} w-[8.5rem]`} value={input.to} maxLength={20}
                    onChange={(e) => set({ to: e.target.value })} />
                  <span className="text-muted">,</span>
                  <input aria-label="Amount in taka" type="number" min={1} className={`${inline} w-[5.5rem]`} value={input.amount || ''}
                    onChange={(e) => set({ amount: Math.max(0, Math.floor(Number(e.target.value))) })} />
                  <span className="text-soft">)</span>
                </div>
                <p className="mt-2 text-[0.78rem] text-muted">
                  Saved contacts: {Object.entries(presets.data!.contacts).map(([n, num]) => `${n} ${num}`).join(' · ')}
                </p>
              </Step>
            </ol>
          </div>

          {/* the verdict stays in view while the form scrolls */}
          <div id="sandbox-verdict" className="min-w-0 scroll-mt-14 lg:sticky lg:top-0 lg:self-start" aria-live="polite">
            <div className="rounded-2xl border border-tile-line bg-well/20 p-5 sm:p-6">
              {check.isError && !check.data ? (
                <p className="text-sm text-bad-pale">{(check.error as Error).message}</p>
              ) : !v || !d ? (
                <p className="text-sm text-muted">{waking ? 'Checking… the first request can take about a minute while the server wakes.' : 'Fill in the three steps on the left.'}</p>
              ) : (
                <>
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="text-[0.8rem] text-muted">AgentShield would</div>
                      <div key={v.decision} className={`verdict-in font-display text-[2.4rem] leading-[1.05] font-semibold tracking-[-0.035em] ${d.ink}`}>{d.word}</div>
                      <div lang="bn" className={`text-[0.95rem] ${d.ink} opacity-80`}>{d.bn}</div>
                    </div>
                    <div className="shrink-0 text-right font-mono text-[0.72rem] text-muted tabular-nums">
                      {check.isFetching ? <Loader2 size={14} className="ml-auto animate-spin" aria-label="Checking" /> : <>checked in<br /><span className="text-body">{v.total_latency_ms < 10 ? v.total_latency_ms.toFixed(1) : Math.round(v.total_latency_ms)} ms</span></>}
                    </div>
                  </div>

                  {/* risk on a track split into the three bands; the pin slides to the score */}
                  {t && (
                    <div className="mt-6">
                      <div className="mb-2 flex items-baseline justify-between font-mono text-[0.72rem] text-muted">
                        <span>risk</span>
                        <span className={`text-[0.95rem] font-semibold tabular-nums ${d.ink}`}>{v.risk_score.toFixed(2)}</span>
                      </div>
                      <div className="relative" role="img" aria-label={`Risk ${v.risk_score.toFixed(2)} of 1; ask from ${t.ask_human_at}, block from ${t.block_at}`}>
                        <div className="flex h-1.5 gap-[3px]">
                          <span className="rounded-full bg-ok/30" style={{ width: `${t.ask_human_at * 100}%` }} />
                          <span className="rounded-full bg-warn/30" style={{ width: `${(t.block_at - t.ask_human_at) * 100}%` }} />
                          <span className="flex-1 rounded-full bg-bad/30" />
                        </div>
                        <span className={`gauge-pin absolute top-1/2 h-3.5 w-3.5 -translate-x-1/2 -translate-y-1/2 rounded-full ring-4 ring-card ${d.pin}`} style={{ left: `${v.risk_score * 100}%` }} />
                      </div>
                      <div className="relative mt-2 h-4 font-mono text-[0.66rem] text-muted">
                        <span className="absolute left-0">allow</span>
                        <span className="absolute -translate-x-1/2" style={{ left: `${((t.ask_human_at + t.block_at) / 2) * 100}%` }}>ask</span>
                        <span className="absolute right-0">block</span>
                      </div>
                    </div>
                  )}

                  {/* the four checks as a quiet ledger: a dot turns red only when a check flags */}
                  <dl className="mt-5 grid grid-cols-2 gap-x-6 border-t border-line pt-4">
                    {v.checks.map((c) => (
                      <div key={c.check} className="flex items-center justify-between gap-2 py-1.5 text-[0.86rem]">
                        <dt className="flex items-center gap-2 capitalize">
                          <span className={`h-1.5 w-1.5 rounded-full ${c.skipped ? 'bg-fg/20' : c.flagged ? 'bg-bad' : 'bg-ok'}`} aria-hidden />
                          {c.check}
                        </dt>
                        <dd className={`font-mono text-[0.78rem] tabular-nums ${c.skipped ? 'text-muted' : c.flagged ? 'text-bad-ink' : 'text-body'}`}>
                          {c.skipped ? 'not needed' : c.risk_score.toFixed(2)}
                        </dd>
                      </div>
                    ))}
                  </dl>

                  <div className="mt-4 border-t border-line pt-4">
                    <p lang="bn" className="text-[0.98rem] leading-relaxed">{firstSentence(v.reason_bn, true)}</p>
                    <p className="mt-1.5 text-[0.84rem] leading-relaxed text-muted">{firstSentence(v.reason_en)}</p>
                    <details className="group mt-3">
                      <summary className="cursor-pointer list-none text-[0.8rem] text-muted underline decoration-fg/25 underline-offset-4 hover:text-ink [&::-webkit-details-marker]:hidden">
                        <span className="group-open:hidden">Full reason</span><span className="hidden group-open:inline">Hide full reason</span>
                      </summary>
                      <p lang="bn" className="mt-2 text-sm text-body">{v.reason_bn}</p>
                      <p className="mt-1.5 text-[0.82rem] leading-relaxed text-muted">{v.reason_en}</p>
                    </details>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}
    </Modal>
  )
}
