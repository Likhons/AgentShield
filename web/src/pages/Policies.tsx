import { useMutation, useQuery } from '@tanstack/react-query'
import { Braces, Check, CircleAlert, Copy, Languages, Plus, Search, Shield, ShieldBan, type LucideIcon } from 'lucide-react'
import { Fragment, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import Modal from '../components/Modal'
import { CountUp } from '../components/Motion'
import { ErrorNote, PageHeader, PageSkeleton } from '../components/ui'
import { api, type Decision, type PolicyRule } from '../lib/api'
import { stagger } from '../lib/motion'
import { useToast } from '../lib/toast'

type View = 'json' | 'yaml'

// Decision colours for the tags, the left bar and the reason box.
const TONE: Record<Decision, { label: string; tag: string; bar: string; box: string; ink: string }> = {
  block: {
    label: 'BLOCK',
    tag: 'border-bad/45 bg-bad/10 text-bad-ink shadow-[0_0_18px_-6px_var(--color-bad)]',
    bar: 'bg-bad shadow-[0_0_14px_var(--color-bad)]',
    box: 'border-bad/25 bg-bad/[0.07]',
    ink: 'text-bad-ink',
  },
  ask_human: {
    label: 'ASK',
    tag: 'border-warn/45 bg-warn/10 text-warn-ink shadow-[0_0_18px_-6px_var(--color-warn)]',
    bar: 'bg-warn shadow-[0_0_14px_var(--color-warn)]',
    box: 'border-warn/25 bg-warn/[0.06]',
    ink: 'text-warn-ink',
  },
  allow: {
    label: 'ALLOW',
    tag: 'border-ok/45 bg-ok/10 text-ok-ink shadow-[0_0_18px_-6px_var(--color-ok)]',
    bar: 'bg-ok shadow-[0_0_14px_var(--color-ok)]',
    box: 'border-ok/25 bg-ok/[0.06]',
    ink: 'text-ok-ink',
  },
}

function Tag({ decision, dot = false }: { decision: Decision; dot?: boolean }) {
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 font-mono text-[0.74rem] font-bold tracking-wide ${TONE[decision].tag}`}>
      {dot && <span className="h-1.5 w-1.5 rounded-full bg-current" aria-hidden />}
      {TONE[decision].label}
    </span>
  )
}

function Precedence() {
  const order: Decision[] = ['block', 'ask_human', 'allow']
  return (
    <div className="glass flex items-center gap-2 rounded-2xl! px-3 py-2 sm:px-4 sm:py-2.5" aria-label="Precedence: block, then ask, then allow">
      <span className="mr-1 hidden font-mono text-[0.7rem] tracking-[0.16em] text-muted uppercase sm:inline">Precedence</span>
      {order.map((d, i) => (
        <Fragment key={d}>
          {i > 0 && <span className="prec-arrow font-mono text-sm text-soft" style={{ ['--d' as string]: `${(i - 1) * 0.35}s` }} aria-hidden>&gt;</span>}
          <Tag decision={d} dot />
        </Fragment>
      ))}
    </div>
  )
}

function matches(rule: PolicyRule, q: string): boolean {
  if (!q.trim()) return true
  const hay = [rule.id, rule.description, (rule.tools ?? []).join(' '), JSON.stringify(rule.when ?? {}), rule.decision, rule.reason_en, rule.reason_bn]
    .join(' ')
    .toLowerCase()
  return hay.includes(q.trim().toLowerCase())
}

function Kpi({ icon: Icon, tint, value, label, index }: { icon: LucideIcon; tint: string; value: number; label: string; index: number }) {
  return (
    <div style={{ ['--i' as string]: index }} className="spring-in">
      <div className="glass spotlight flex h-full items-start justify-between gap-3 overflow-hidden rounded-[20px]! p-4 sm:p-6">
        {/* thin coloured edge on top, fading out to both sides */}
        <span className="pointer-events-none absolute inset-x-6 top-0 h-px" style={{ background: `linear-gradient(90deg, transparent, ${tint}, transparent)` }} aria-hidden />
        <div className="relative min-w-0">
          <div className="font-display text-[1.9rem] leading-none font-extrabold tabular-nums sm:text-[2.6rem]" style={{ color: tint }}>
            <CountUp to={value} />
          </div>
          <div className="mt-2 text-[0.78rem] text-body sm:mt-3 sm:text-[0.95rem]">{label}</div>
        </div>
        <span
          className="relative hidden h-11 w-11 shrink-0 items-center justify-center rounded-xl sm:inline-flex"
          style={{ background: `color-mix(in srgb, ${tint} 8%, transparent)`, border: `1px solid color-mix(in srgb, ${tint} 35%, transparent)` }}
        >
          <Icon size={19} color={tint} aria-hidden />
        </span>
      </div>
    </div>
  )
}

/** '{"argument":"to"}' -> '{"argument": "to"}' */
const pretty = (v: unknown) => JSON.stringify(v).replace(/":/g, '": ').replace(/,"/g, ', "')

const PLACEHOLDER = /(\{[a-z_]+\})/g

/** Template placeholders such as {recipient} in mono, the rest as plain text. */
function Template({ text }: { text: string }) {
  return (
    <>
      {text.split(PLACEHOLDER).map((part, i) =>
        i % 2 === 1 ? (
          <code key={i} className="rounded border border-fg/10 bg-well/30 px-1 font-mono text-[0.82em] text-soft">{part}</code>
        ) : (
          <Fragment key={i}>{part}</Fragment>
        ),
      )}
    </>
  )
}

function CopyText({ text }: { text: string }) {
  const [done, setDone] = useState(false)
  const toast = useToast()
  return (
    <button type="button" onClick={() => void navigator.clipboard?.writeText(text).then(() => { toast('Copied'); setDone(true); setTimeout(() => setDone(false), 1500) })}
      className="inline-flex min-h-10 items-center gap-1.5 rounded-lg border border-line px-3 text-xs font-semibold hover:border-line2">
      <Copy size={13} aria-hidden /> {done ? 'Copied' : 'Copy'}
    </button>
  )
}

function IconButton({ label, onClick, children }: { label: string; onClick: () => void; children: ReactNode }) {
  return (
    <button type="button" onClick={onClick} aria-label={label} title={label}
      className="lift inline-flex h-10 w-10 items-center justify-center rounded-xl border border-fg/10 bg-well/25 text-body hover:border-accent/40 hover:text-soft">
      {children}
    </button>
  )
}

function RuleCard({ rule, yaml, onInspect }: { rule: PolicyRule; yaml: string; onInspect: () => void }) {
  const tone = TONE[rule.decision]
  const toast = useToast()
  const [copied, setCopied] = useState(false)
  const copy = () =>
    void navigator.clipboard?.writeText(yaml).then(() => {
      toast(`Copied ${rule.id} as YAML`)
      setCopied(true)
      setTimeout(() => setCopied(false), 1500)
    })
  const chips: [string, string][] = [
    ['tools', (rule.tools ?? []).join(', ') || 'any'],
    ...Object.entries(rule.when ?? {}).map(([k, v]): [string, string] => [k, typeof v === 'string' ? v : pretty(v)]),
  ]

  return (
    <article className="glass spotlight flex flex-col gap-3.5 overflow-hidden rounded-[22px]! py-5 pr-4 pl-6 sm:py-6 sm:pr-6 sm:pl-10">
      <span className={`absolute inset-y-5 left-0 w-[3px] rounded-r-full ${tone.bar}`} aria-hidden />
      <div className="relative flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <div className="flex flex-wrap items-center gap-2.5">
            <h2 className="font-mono text-[1rem] font-bold break-all sm:text-[1.06rem]">{rule.id}</h2>
            {rule.risk !== undefined && (
              <span className="rounded-md border border-fg/10 bg-well/25 px-2 py-0.5 font-mono text-[0.72rem] text-muted tabular-nums">risk {rule.risk.toFixed(2)}</span>
            )}
          </div>
          {rule.description && <p className="mt-1.5 text-[0.95rem] text-body">{rule.description}</p>}
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <Tag decision={rule.decision} />
          <IconButton label="Inspect rule as JSON or YAML" onClick={onInspect}><Braces size={16} aria-hidden /></IconButton>
          <IconButton label={copied ? 'Copied' : 'Copy rule as YAML'} onClick={copy}>
            {copied ? <Check size={16} className="text-ok-ink" aria-hidden /> : <Copy size={16} aria-hidden />}
          </IconButton>
        </div>
      </div>

      <ul className="relative flex flex-wrap gap-2" aria-label="Conditions">
        {chips.map(([k, v]) => (
          // key and value wrap as whole pieces on narrow screens instead of splitting "to" mid-word
          <li key={k} className="flex min-w-0 flex-wrap gap-x-1.5 rounded-lg border border-fg/8 bg-well/35 px-2.5 py-1 font-mono text-[0.78rem]">
            <span className="text-muted">{k}:</span>
            <b className="min-w-0 break-words text-soft">{v}</b>
          </li>
        ))}
      </ul>

      {(rule.reason_bn || rule.reason_en) && (
        <div className={`relative flex gap-3 rounded-xl border px-4 py-3 ${tone.box}`}>
          <Languages size={17} className={`mt-1 shrink-0 ${tone.ink}`} aria-hidden />
          <div className="min-w-0">
            {rule.reason_bn && (
              <p lang="bn" className="text-[0.98rem] leading-relaxed">
                <b className={tone.ink}>কারণ:</b> <Template text={rule.reason_bn} />
              </p>
            )}
            {rule.reason_en && (
              <p className="mt-0.5 text-[0.84rem] leading-relaxed text-muted">
                <Template text={rule.reason_en} />
              </p>
            )}
          </div>
        </div>
      )}
    </article>
  )
}

const DEFAULT_FORM = {
  id: 'custom_transfer_rule',
  description: 'Require approval for transfers above threshold.',
  tools: 'send_money',
  decision: 'ask_human' as Exclude<Decision, 'allow'>,
  risk: 0.7,
  tainted: false,
  amountGt: 10000,
  reason_bn: '{limit} টাকার বেশি ট্রান্সফারে আপনার অনুমতি লাগবে।',
  reason_en: 'Transfers above {limit} BDT need your approval.',
}

function AddPolicy({ file }: { file: string }) {
  const [f, setF] = useState(DEFAULT_FORM)
  const set = <K extends keyof typeof f>(k: K, v: (typeof f)[K]) => setF((x) => ({ ...x, [k]: v }))
  const toast = useToast()
  const validate = useMutation({
    onSuccess: (r) => toast(r.valid ? 'Rule is valid: YAML ready to copy' : 'The rule has errors, see below', r.valid ? 'ok' : 'error'),
    mutationFn: () => {
      const when: Record<string, unknown> = {}
      if (f.tainted) when.tainted = true
      if (f.amountGt > 0) when.argument_gt = { argument: 'amount', value: Math.round(f.amountGt) }
      return api.validatePolicy({
        id: f.id.trim() || 'custom_rule',
        description: f.description.trim(),
        tools: f.tools.split(',').map((t) => t.trim()).filter(Boolean),
        when,
        decision: f.decision,
        risk: Math.round(f.risk * 100) / 100,
        reason_en: f.reason_en,
        reason_bn: f.reason_bn,
      })
    },
  })
  const input = 'min-h-10 w-full rounded-lg border border-line bg-card2 px-3 text-sm font-normal'
  return (
    <div className="flex flex-col gap-3">
      <p className="text-sm text-muted">
        <code className="font-mono text-soft">{file}</code> stays read-only at runtime. Check a rule against the PolicyRule schema and copy the YAML into the file.
      </p>
      <div className="grid gap-3 sm:grid-cols-2">
        <label className="flex flex-col gap-1 text-sm font-semibold">Rule ID<input className={input} value={f.id} onChange={(e) => set('id', e.target.value)} /></label>
        <label className="flex flex-col gap-1 text-sm font-semibold">Tools (comma-separated)<input className={input} value={f.tools} onChange={(e) => set('tools', e.target.value)} /></label>
        <label className="flex flex-col gap-1 text-sm font-semibold sm:col-span-2">Description<input className={input} value={f.description} onChange={(e) => set('description', e.target.value)} /></label>
        <label className="flex flex-col gap-1 text-sm font-semibold">Decision
          <select className={input} value={f.decision} onChange={(e) => set('decision', e.target.value as typeof f.decision)}>
            <option value="ask_human">ask_human</option>
            <option value="block">block</option>
          </select>
        </label>
        <label className="flex flex-col gap-1 text-sm font-semibold">Risk score: {f.risk.toFixed(2)}
          <input type="range" min={0.1} max={1} step={0.05} value={f.risk} onChange={(e) => set('risk', Number(e.target.value))} className="h-10 cursor-pointer accent-[var(--color-mark)]" />
        </label>
        <label className="flex flex-col gap-1 text-sm font-semibold">Amount greater than (0 = none)
          <input type="number" min={0} step={1000} className={input} value={f.amountGt} onChange={(e) => set('amountGt', Math.max(0, Number(e.target.value)))} />
        </label>
        <label className="flex items-center gap-2 self-end text-sm font-semibold sm:min-h-10">
          <input type="checkbox" checked={f.tainted} onChange={(e) => set('tainted', e.target.checked)} className="h-4 w-4 accent-[var(--color-mark)]" />
          Require tainted context
        </label>
        <label className="flex flex-col gap-1 text-sm font-semibold sm:col-span-2">Reason (Bangla)<input className={input} value={f.reason_bn} onChange={(e) => set('reason_bn', e.target.value)} /></label>
        <label className="flex flex-col gap-1 text-sm font-semibold sm:col-span-2">Reason (English)<input className={input} value={f.reason_en} onChange={(e) => set('reason_en', e.target.value)} /></label>
      </div>
      <button type="button" onClick={() => validate.mutate()} disabled={validate.isPending}
        className="min-h-11 btn-primary rounded-xl font-bold disabled:opacity-60">
        Validate & generate YAML
      </button>
      {validate.error && <ErrorNote error={validate.error} />}
      {validate.data?.valid === false && <div role="alert" className="rounded-xl border border-bad/40 bg-bad/10 px-4 py-3 text-sm text-bad-soft">Validation error: {validate.data.error}</div>}
      {validate.data?.yaml && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-ok">Valid PolicyRule schema.</span>
            <CopyText text={validate.data.yaml} />
          </div>
          <pre className="overflow-x-auto rounded-lg border border-line bg-bg p-3 font-mono text-[0.8rem] text-soft">{validate.data.yaml}</pre>
        </div>
      )}
    </div>
  )
}

export default function Policies() {
  const { data, error, isPending } = useQuery({ queryKey: ['policies'], queryFn: api.policies })
  const [decision, setDecision] = useState<'all' | 'block' | 'ask_human'>('all')
  const [search, setSearch] = useState('')
  const [open, setOpen] = useState<{ id: string; view: View } | null>(null)
  const [adding, setAdding] = useState(false)
  const searchRef = useRef<HTMLInputElement>(null)
  const isMac = typeof navigator !== 'undefined' && /Mac|iPhone|iPad/.test(navigator.platform)

  // Ctrl+K / Cmd+K jumps to the search field
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault()
        searchRef.current?.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [])

  const rules = useMemo(() => data?.rules ?? [], [data])
  const matched = rules.filter((r) => matches(r, search))
  const shown = matched.filter((r) => decision === 'all' || r.decision === decision)
  const target = open ? rules.find((r) => r.id === open.id) : undefined
  const sub = (
    <>
      Deterministic rules from{' '}
      <code className="rounded-md border border-fg/10 bg-well/30 px-1.5 py-0.5 font-mono text-[0.8rem] text-ink">default.yaml</code>. If several match, the most
      severe decision wins (<span className="font-mono text-bad-ink">block</span> &gt; <span className="font-mono text-warn-ink">ask</span> &gt;{' '}
      <span className="font-mono text-ok-ink">allow</span>).
    </>
  )

  return (
    <>
      <PageHeader title="Policies" sub={sub} right={<Precedence />} />
      {isPending && <PageSkeleton cards={3} />}
      {error && <ErrorNote error={error} />}
      {data && (
        <>
          <div className="grid grid-cols-3 gap-2.5 sm:gap-4">
            <Kpi index={0} icon={Shield} tint="var(--color-soft)" value={rules.length} label="Total Policies" />
            <Kpi index={1} icon={ShieldBan} tint="var(--color-bad)" value={rules.filter((r) => r.decision === 'block').length} label="Block Policies" />
            <Kpi index={2} icon={CircleAlert} tint="var(--color-warn)" value={rules.filter((r) => r.decision === 'ask_human').length} label="Ask Policies" />
          </div>

          <div className="my-5 flex flex-col gap-2.5 lg:flex-row lg:items-center lg:gap-4">
            <div role="radiogroup" aria-label="Decision filter" className="glass flex shrink-0 gap-1 rounded-2xl! p-1.5">
              {([
                ['all', `All (${matched.length})`],
                ['block', `Block (${matched.filter((r) => r.decision === 'block').length})`],
                ['ask_human', `Ask (${matched.filter((r) => r.decision === 'ask_human').length})`],
              ] as const).map(([id, label]) => (
                <button key={id} type="button" role="radio" aria-checked={decision === id} onClick={() => setDecision(id)}
                  className={`min-h-10 flex-1 rounded-xl px-4 text-sm font-semibold whitespace-nowrap transition-colors lg:flex-none ${decision === id ? 'btn-primary' : 'text-body hover:bg-fg/5'}`}>
                  {label}
                </button>
              ))}
            </div>
            <div className="flex flex-1 flex-col gap-2.5 sm:flex-row sm:items-center sm:gap-4">
              <label className="relative flex-1 lg:max-w-3xl">
                <span className="sr-only">Search policies</span>
                <Search size={17} className="pointer-events-none absolute top-1/2 left-4 z-10 -translate-y-1/2 text-muted" aria-hidden />
                <input ref={searchRef} type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search policies, tools, or description…"
                  className="glass min-h-12 w-full rounded-2xl! pr-16 pl-11 text-sm placeholder:text-muted" />
                <kbd className="pointer-events-none absolute top-1/2 right-3 hidden -translate-y-1/2 rounded-md border border-fg/12 bg-well/40 px-1.5 py-0.5 font-mono text-[0.7rem] text-muted sm:block">
                  {isMac ? '⌘K' : 'Ctrl K'}
                </kbd>
              </label>
              <button type="button" onClick={() => setAdding(true)}
                className="inline-flex min-h-12 items-center justify-center gap-2 btn-primary rounded-2xl px-6 text-[0.95rem] font-bold sm:ml-auto">
                <Plus size={18} aria-hidden /> Add Policy
              </button>
            </div>
          </div>

          {shown.length === 0 ? (
            <p className="glass px-5 py-6 text-sm text-muted">No policy rules match your current search or filter.</p>
          ) : (
            <div className="flex flex-col gap-4">
              {shown.map((r, i) => (
                <div key={r.id} className="stagger-item" style={stagger(i)}>
                  <RuleCard rule={r} yaml={data.yaml[r.id] ?? ''} onInspect={() => setOpen({ id: r.id, view: 'json' })} />
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {target && open && data && (
        <Modal title={<>Rule <code className="font-mono">{target.id}</code></>} onClose={() => setOpen(null)}>
          <div className="flex flex-col gap-2.5">
            <div className="flex items-center justify-between gap-2">
              <div role="tablist" aria-label="Format" className="flex gap-1 rounded-xl border border-line p-1">
                {(['json', 'yaml'] as const).map((v) => (
                  <button key={v} type="button" role="tab" aria-selected={open.view === v} onClick={() => setOpen({ ...open, view: v })}
                    className={`min-h-9 rounded-lg px-3.5 font-mono text-xs font-bold uppercase ${open.view === v ? 'btn-primary' : 'text-body hover:bg-fg/5'}`}>
                    {v}
                  </button>
                ))}
              </div>
              <CopyText text={open.view === 'yaml' ? data.yaml[target.id] : JSON.stringify(target, null, 2)} />
            </div>
            <pre className="overflow-x-auto rounded-lg border border-line bg-bg p-3 font-mono text-[0.8rem] text-soft">
              {open.view === 'yaml' ? data.yaml[target.id] : JSON.stringify(target, null, 2)}
            </pre>
          </div>
        </Modal>
      )}
      {adding && data && (
        <Modal title="Validate & Generate Policy Rule (YAML)" onClose={() => setAdding(false)}>
          <AddPolicy file={data.file} />
        </Modal>
      )}
    </>
  )
}
