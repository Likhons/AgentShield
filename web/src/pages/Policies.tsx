import { useMutation, useQuery } from '@tanstack/react-query'
import { Braces, CircleHelp, Copy, Info, Layers, MessageSquare, Plus, Scale, Search, ShieldX, type LucideIcon } from 'lucide-react'
import { useMemo, useState } from 'react'
import Modal from '../components/Modal'
import { CountUp } from '../components/Motion'
import { DecisionBadge, ErrorNote, PageHeader, PageSkeleton } from '../components/ui'
import { api, type Decision, type PolicyRule } from '../lib/api'
import { stagger } from '../lib/motion'
import { useToast } from '../lib/toast'

type View = 'yaml' | 'inspect' | 'details'

function matches(rule: PolicyRule, q: string): boolean {
  if (!q.trim()) return true
  const hay = [rule.id, rule.description, (rule.tools ?? []).join(' '), JSON.stringify(rule.when ?? {}), rule.decision, rule.reason_en, rule.reason_bn]
    .join(' ')
    .toLowerCase()
  return hay.includes(q.trim().toLowerCase())
}

function Kpi({ icon: Icon, tint, value, label }: { icon: LucideIcon; tint: string; value: number; label: string }) {
  return (
    <div className="card flex flex-col items-start gap-2 p-3 transition hover:-translate-y-0.5 hover:border-line2 sm:flex-row sm:items-center sm:gap-3.5 sm:p-4">
      <span className="inline-flex h-9 w-9 shrink-0 items-center justify-center rounded-xl sm:h-11 sm:w-11" style={{ background: `${tint}1A`, border: `1px solid ${tint}4D` }}>
        <Icon size={20} color={tint} aria-hidden />
      </span>
      <div>
        <div className="text-[1.3rem] leading-none font-display font-bold tabular-nums sm:text-[1.75rem]"><CountUp to={value} /></div>
        <div className="mt-1 text-[0.74rem] text-muted sm:text-[0.83rem]">{label}</div>
      </div>
    </div>
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

function RuleCard({ rule, onOpen }: { rule: PolicyRule; onOpen: (v: View) => void }) {
  const accent = rule.decision === 'block' ? 'border-l-bad' : 'border-l-warn'
  const actions: { v: View; icon: LucideIcon; label: string }[] = [
    { v: 'inspect', icon: Braces, label: 'Inspect rule as JSON' },
    { v: 'yaml', icon: Copy, label: 'Copy rule as YAML' },
    { v: 'details', icon: Info, label: 'Rule details' },
  ]
  return (
    <article className={`card border-l-[3px] ${accent} flex flex-col gap-3 p-4 sm:p-5`}>
      <div className="flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
        <div className="min-w-0">
          <h2 className="font-mono text-[0.98rem] font-bold break-words">{rule.id}</h2>
          {rule.description && <p className="mt-1 text-sm text-muted">{rule.description}</p>}
        </div>
        <div className="flex items-center gap-2">
          <DecisionBadge decision={rule.decision} />
          {actions.map(({ v, icon: Icon, label }) => (
            <button key={v} type="button" onClick={() => onOpen(v)} aria-label={label} title={label}
              className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-line bg-card2/60 hover:border-line2">
              <Icon size={16} aria-hidden />
            </button>
          ))}
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-1.5 text-sm">
        <span className="mr-1 text-muted">Tools:</span>
        {(rule.tools ?? []).map((t) => (
          <code key={t} className="rounded-md border border-line2 bg-accent/15 px-2 py-0.5 font-mono text-[0.78rem] font-bold text-[#E9D5FF]">{t}</code>
        ))}
        {Object.entries(rule.when ?? {}).map(([k, v]) => (
          <code key={k} className="rounded-md border border-line bg-card2 px-2 py-0.5 font-mono text-[0.76rem] text-[#C9B6FF]">
            {k}: {JSON.stringify(v)}
          </code>
        ))}
      </div>
      {rule.reason_bn && (
        <p className="flex gap-2 border-t border-line pt-3 text-[0.95rem] leading-relaxed">
          <MessageSquare size={15} className="mt-1 shrink-0 text-muted" aria-hidden />
          <span><b>কারণ:</b> {rule.reason_bn}</span>
        </p>
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
        <code className="font-mono text-[#C9B6FF]">{file}</code> stays read-only at runtime. Check a rule against the PolicyRule schema and copy the YAML into the file.
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
          <input type="range" min={0.1} max={1} step={0.05} value={f.risk} onChange={(e) => set('risk', Number(e.target.value))} className="h-10 cursor-pointer accent-[#9147FF]" />
        </label>
        <label className="flex flex-col gap-1 text-sm font-semibold">Amount greater than (0 = none)
          <input type="number" min={0} step={1000} className={input} value={f.amountGt} onChange={(e) => set('amountGt', Math.max(0, Number(e.target.value)))} />
        </label>
        <label className="flex items-center gap-2 self-end text-sm font-semibold sm:min-h-10">
          <input type="checkbox" checked={f.tainted} onChange={(e) => set('tainted', e.target.checked)} className="h-4 w-4 accent-[#9147FF]" />
          Require tainted context
        </label>
        <label className="flex flex-col gap-1 text-sm font-semibold sm:col-span-2">Reason (Bangla)<input className={input} value={f.reason_bn} onChange={(e) => set('reason_bn', e.target.value)} /></label>
        <label className="flex flex-col gap-1 text-sm font-semibold sm:col-span-2">Reason (English)<input className={input} value={f.reason_en} onChange={(e) => set('reason_en', e.target.value)} /></label>
      </div>
      <button type="button" onClick={() => validate.mutate()} disabled={validate.isPending}
        className="min-h-11 rounded-xl bg-gradient-to-r from-accent to-accent2 font-bold text-white disabled:opacity-60">
        Validate & generate YAML
      </button>
      {validate.error && <ErrorNote error={validate.error} />}
      {validate.data?.valid === false && <div role="alert" className="rounded-xl border border-bad/40 bg-bad/10 px-4 py-3 text-sm text-[#FF8A94]">Validation error: {validate.data.error}</div>}
      {validate.data?.yaml && (
        <div className="flex flex-col gap-2">
          <div className="flex items-center justify-between">
            <span className="text-sm font-semibold text-ok">Valid PolicyRule schema.</span>
            <CopyText text={validate.data.yaml} />
          </div>
          <pre className="overflow-x-auto rounded-lg border border-line bg-bg p-3 font-mono text-[0.8rem] text-[#C9B6FF]">{validate.data.yaml}</pre>
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

  const rules = useMemo(() => data?.rules ?? [], [data])
  const matched = rules.filter((r) => matches(r, search))
  const shown = matched.filter((r) => decision === 'all' || r.decision === decision)
  const target = open ? rules.find((r) => r.id === open.id) : undefined

  return (
    <>
      <PageHeader icon={Scale} title="Policies" sub="Deterministic rules from default.yaml. If several match, the most severe decision wins (block > ask > allow)." />
      {isPending && <PageSkeleton cards={3} />}
      {error && <ErrorNote error={error} />}
      {data && (
        <>
          <div className="grid grid-cols-3 gap-2.5 sm:gap-4">
            <Kpi icon={Layers} tint="#9147FF" value={rules.length} label="Total Policies" />
            <Kpi icon={ShieldX} tint="#FF526F" value={rules.filter((r) => r.decision === 'block').length} label="Block Policies" />
            <Kpi icon={CircleHelp} tint="#FFB547" value={rules.filter((r) => r.decision === 'ask_human').length} label="Ask Policies" />
          </div>

          <div className="my-4 flex flex-col gap-2.5 lg:flex-row lg:items-center">
            <div role="radiogroup" aria-label="Decision filter" className="flex shrink-0 gap-1 rounded-xl border border-line bg-card/70 p-1">
              {([
                ['all', `All (${matched.length})`],
                ['block', `Block (${matched.filter((r) => r.decision === 'block').length})`],
                ['ask_human', `Ask (${matched.filter((r) => r.decision === 'ask_human').length})`],
              ] as const).map(([id, label]) => (
                <button key={id} type="button" role="radio" aria-checked={decision === id} onClick={() => setDecision(id)}
                  className={`min-h-10 rounded-lg px-3.5 text-sm font-semibold whitespace-nowrap ${decision === id ? 'bg-gradient-to-r from-accent to-accent2 text-white' : 'text-[#D5DCF6] hover:bg-white/5'}`}>
                  {label}
                </button>
              ))}
            </div>
            <div className="flex flex-1 flex-col gap-2.5 sm:flex-row">
            <label className="relative flex-1">
              <span className="sr-only">Search policies</span>
              <Search size={16} className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted" aria-hidden />
              <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search policies, tools, or description…"
                className="min-h-11 w-full rounded-xl border border-line bg-card2/80 pr-3 pl-9 text-sm placeholder:text-muted" />
            </label>
            <button type="button" onClick={() => setAdding(true)}
              className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-gradient-to-r from-accent to-accent2 px-5 text-sm font-bold text-white">
              <Plus size={16} aria-hidden /> Add Policy
            </button>
            </div>
          </div>

          {shown.length === 0 ? (
            <p className="card px-4 py-5 text-sm text-muted">No policy rules match your current search or filter.</p>
          ) : (
            <div className="flex flex-col gap-3">
              {shown.map((r, i) => (
                <div key={r.id} className="stagger-item" style={stagger(i)}>
                  <RuleCard rule={r} onOpen={(view) => setOpen({ id: r.id, view })} />
                </div>
              ))}
            </div>
          )}
        </>
      )}

      {target && open && data && (
        <Modal title={<>Rule <code className="font-mono">{target.id}</code> · {open.view === 'yaml' ? 'YAML' : open.view === 'inspect' ? 'JSON' : 'Details'}</>} onClose={() => setOpen(null)}>
          {open.view === 'details' ? (
            <ul className="flex flex-col gap-2 text-sm">
              <li><b>Decision:</b> <code className="font-mono text-[#C9B6FF]">{target.decision}</code> (risk <code className="font-mono">{target.risk ?? 0}</code>)</li>
              <li><b>Tools:</b> <code className="font-mono text-[#C9B6FF]">{(target.tools ?? []).join(', ')}</code></li>
              <li><b>English template:</b> {target.reason_en}</li>
              <li><b>Bangla template:</b> {target.reason_bn}</li>
            </ul>
          ) : (
            <div className="flex flex-col gap-2">
              <div className="flex justify-end">
                <CopyText text={open.view === 'yaml' ? data.yaml[target.id] : JSON.stringify(target, null, 2)} />
              </div>
              <pre className="overflow-x-auto rounded-lg border border-line bg-bg p-3 font-mono text-[0.8rem] text-[#C9B6FF]">
                {open.view === 'yaml' ? data.yaml[target.id] : JSON.stringify(target, null, 2)}
              </pre>
            </div>
          )}
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
