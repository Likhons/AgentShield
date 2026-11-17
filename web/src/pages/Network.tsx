import { useQuery } from '@tanstack/react-query'
import { Fragment, useEffect, useRef, useState, type ReactNode } from 'react'
import { Reveal } from '../components/Motion'
import { DecisionBadge, ErrorNote, PageHeader, PageSkeleton, StatRail } from '../components/ui'
import { api, type NetAccount, type NetMember, type NetOutcome, type NetPayment, type NetRing, type NetworkReport } from '../lib/api'
import { taka } from '../lib/format'
import { stagger, useInView } from '../lib/motion'

// ---------------------------------------------------------------------------
// formatting
// ---------------------------------------------------------------------------

const TZ = 'Asia/Dhaka'
const ms = (iso: string) => new Date(iso).getTime()
const day = (iso: string) => new Date(iso).toLocaleString('en-GB', { weekday: 'short', day: 'numeric', month: 'short', timeZone: TZ })
const clock = (iso: string) => new Date(iso).toLocaleString('en-GB', { hour: '2-digit', minute: '2-digit', hour12: false, timeZone: TZ })
const when = (iso: string) => `${day(iso)}, ${clock(iso)}`
/** 01085280164 -> "010 8528 0164" */
const phone = (n: string) => `${n.slice(0, 3)} ${n.slice(3, 7)} ${n.slice(7)}`
const tail = (n: string) => `…${n.slice(-4)}`
const pct = (x: number) => `${Math.round(x * 100)}%`
const num = (n: number) => n.toLocaleString('en-US')
const NL = '\n'

function duration(fromIso: string, toIso: string): string {
  const min = Math.round((ms(toIso) - ms(fromIso)) / 60000)
  if (min < 60) return `${min} min`
  const h = Math.floor(min / 60)
  return min % 60 ? `${h} h ${min % 60} min` : `${h} h`
}

const SOURCE: Record<string, string> = { 'tool:email': 'email', 'tool:web': 'web page', 'tool:file': 'file', user: 'typed by the user' }

const OUTCOME: Record<NetOutcome, { label: string; color: string }> = {
  moved: { label: 'Money reached the scammer', color: 'var(--color-bad)' },
  agentshield: { label: 'Stopped by the per-call check', color: 'var(--color-mark)' },
  network: { label: 'Stopped by the network check', color: 'var(--color-info)' },
}

const PARTS: { key: keyof NetAccount['parts']; label: string; color: string }[] = [
  { key: 'fan_in', label: 'fan-in', color: 'var(--color-info)' },
  { key: 'pass_through', label: 'pass-through', color: 'var(--color-warn)' },
  { key: 'untrusted', label: 'untrusted source', color: 'var(--color-bad-soft)' },
  { key: 'linked', label: 'linked', color: 'var(--color-soft)' },
]

const TIER: Record<string, { label: string; cls: string }> = {
  flagged: { label: 'Flagged', cls: 'border-bad/35 bg-bad/12 text-bad-ink' },
  cashout: { label: 'Cash-out', cls: 'border-bad/35 bg-bad/12 text-bad-ink' },
  watch: { label: 'Watch', cls: 'border-warn/35 bg-warn/12 text-warn-ink' },
  clear: { label: 'Clear', cls: 'border-line2 bg-fg/[0.03] text-muted' },
}

function TierTag({ tier }: { tier: string }) {
  const t = TIER[tier] ?? TIER.clear
  return <span className={`inline-flex rounded-md border px-2 py-0.5 text-[0.72rem] font-bold tracking-wide whitespace-nowrap ${t.cls}`}>{t.label}</span>
}

// ---------------------------------------------------------------------------
// layout pieces
// ---------------------------------------------------------------------------

function Section({ n, title, sub, children }: { n: number; title: ReactNode; sub?: ReactNode; children: ReactNode }) {
  return (
    <section className="flex flex-col gap-4">
      <div className="flex flex-col gap-1.5 border-b border-line pb-4">
        <div className="flex items-baseline gap-3">
          <span className="font-mono text-[0.8rem] text-soft tabular-nums">{String(n).padStart(2, '0')}</span>
          <h2 className="text-[clamp(1.25rem,2vw,1.55rem)] font-semibold tracking-[-0.025em]">{title}</h2>
        </div>
        {sub && <p className="max-w-[76ch] text-[0.9rem] leading-relaxed text-body sm:pl-8">{sub}</p>}
      </div>
      {children}
    </section>
  )
}

function Eyebrow({ children }: { children: ReactNode }) {
  return <div className="font-mono text-[0.68rem] tracking-[0.18em] text-muted uppercase">{children}</div>
}

function Legend({ items }: { items: NetOutcome[] }) {
  return (
    <ul className="flex flex-wrap gap-x-4 gap-y-1.5 text-[0.76rem] text-muted">
      {items.map((o) => (
        <li key={o} className="inline-flex items-center gap-1.5">
          <span className="h-2 w-2 rounded-full" style={{ background: OUTCOME[o].color }} aria-hidden />
          {OUTCOME[o].label}
        </li>
      ))}
    </ul>
  )
}

// ---------------------------------------------------------------------------
// 01  one person vs the network
// ---------------------------------------------------------------------------

/** Width of an element in CSS pixels, kept current. */
function useWidth<T extends HTMLElement>(fallback: number) {
  const ref = useRef<T>(null)
  const [w, setW] = useState(fallback)
  useEffect(() => {
    const el = ref.current
    if (!el) return
    const ro = new ResizeObserver(([e]) => setW(Math.round(e.contentRect.width)))
    ro.observe(el)
    return () => ro.disconnect()
  }, [])
  return [ref, w] as const
}

/** Payments to one number as stacked dots in 10-minute columns, with the moment the network flagged it.
 *  Drawn at the box's real width, so the labels keep their size on a phone. */
function DotStrip({ s }: { s: NetworkReport['spotlight'] }) {
  const [ref, seen] = useInView<HTMLDivElement>(0.3)
  const [box, boxW] = useWidth<HTMLDivElement>(640)
  const t0 = ms(s.first_seen)
  const inDay = s.payments.filter((p) => ms(p.t) - t0 < 24 * 3600e3)
  const t1 = Math.max(...inDay.map((p) => ms(p.t)), ms(s.flagged_at)) + 15 * 60e3
  const W = Math.max(boxW, 280), H = 150, base = 112, padX = 10
  const bin = 10 * 60e3
  const bins = Math.ceil((t1 - t0) / bin)
  const colW = (W - padX * 2) / bins
  const dotR = Math.min(3.6, colW / 2 - 0.4)
  const narrow = W < 480
  const x = (t: number) => padX + ((t - t0) / (t1 - t0)) * (W - padX * 2)
  const heights = new Map<number, number>()
  const dots = inDay.map((p, i) => {
    const b = Math.floor((ms(p.t) - t0) / bin)
    const k = heights.get(b) ?? 0
    heights.set(b, k + 1)
    return { cx: padX + b * colW + colW / 2, cy: base - 6 - k * (dotR * 2 + 2.6), after: ms(p.t) >= ms(s.flagged_at), i }
  })
  const fx = x(ms(s.flagged_at))
  const hours: number[] = []
  const every = narrow ? 2 : 1
  for (let h = Math.ceil(t0 / 3600e3) * 3600e3; h <= t1; h += 3600e3 * every) hours.push(h)
  // the flag label sits right of the line, or left of it when there is no room
  const labelLeft = fx > W - 200
  return (
    <div ref={ref} className={`net-strip ${seen ? 'is-seen' : ''}`}>
      <div ref={box}>
      <svg viewBox={`0 0 ${W} ${H}`} className="block h-auto w-full" role="img"
        aria-label={`${inDay.length} payments to ${phone(s.number)} in the first day; flagged after ${s.flagged_after} people`}>
        <line x1={padX} x2={W - padX} y1={base} y2={base} stroke="var(--color-line2)" />
        {hours.map((h) => (
          <g key={h}>
            <line x1={x(h)} x2={x(h)} y1={base} y2={base + 5} stroke="var(--color-line2)" />
            <text x={x(h)} y={base + 19} textAnchor="middle" className="fill-muted font-mono" fontSize="10.5">{clock(new Date(h).toISOString())}</text>
          </g>
        ))}
        <rect x={fx} y={14} width={W - padX - fx} height={base - 14} fill="var(--color-mark)" opacity="0.05" />
        <line x1={fx} x2={fx} y1={10} y2={base} stroke="var(--color-mark)" strokeDasharray="3 3" />
        <text x={labelLeft ? fx - 7 : fx + 7} y={22} textAnchor={labelLeft ? 'end' : 'start'} className="fill-ink font-mono" fontSize="11" fontWeight="600">flagged · {s.flagged_after} people</text>
        <text x={labelLeft ? fx - 7 : fx + 7} y={36} textAnchor={labelLeft ? 'end' : 'start'} className="fill-muted font-mono" fontSize="10.5">{duration(s.first_seen, s.flagged_at)} after the first</text>
        {dots.map((d) => (
          <circle key={d.i} className="net-dot" cx={d.cx} cy={d.cy} r={dotR} style={{ ...stagger(d.i), ['--d' as string]: `${d.i * 22}ms` }}
            fill={d.after ? 'var(--color-mark)' : 'var(--color-ink)'} fillOpacity={d.after ? 0.95 : 0.5} />
        ))}
      </svg>
      </div>
    </div>
  )
}

function Contrast({ r }: { r: NetworkReport }) {
  const s = r.spotlight
  const f = s.first_payment
  const laterPeople = s.people - s.flagged_after
  return (
    <div className="grid gap-3 lg:grid-cols-[minmax(0,5fr)_minmax(0,8fr)] lg:gap-4">
      <div className="card flex flex-col gap-4 p-4 sm:p-5">
        <Eyebrow>One person's agent</Eyebrow>
        <div className="rounded-xl border border-line bg-well/25 p-3.5 font-mono text-[0.8rem]">
          <div className="flex items-center justify-between gap-3">
            <span className="text-muted">{when(f.t)}</span>
            <DecisionBadge decision={f.verdict} />
          </div>
          <div className="mt-2.5 leading-relaxed break-words">
            <span className="text-soft">send_money</span>
            <span className="text-muted">(</span>to=<span className="text-ink">{phone(s.number)}</span>, amount=<span className="text-ink">{num(f.amount)}</span>
            <span className="text-muted">)</span>
          </div>
          <div className="mt-2 text-[0.74rem] text-muted">
            from: {SOURCE[f.source] ?? f.source}{f.origin ? ` (${f.origin})` : ''}
            {f.rule && <><br />rule: {f.rule}</>}
          </div>
        </div>
        <p className="text-[0.9rem] leading-relaxed text-body">
          The per-call policy blocks it. For this person that is the whole story: one payment, one stranger, nothing to compare it with.
        </p>
      </div>

      <div className="card flex min-w-0 flex-col gap-3 p-4 sm:p-5">
        <div className="flex flex-wrap items-baseline justify-between gap-2">
          <Eyebrow>The wallet, across {num(r.world.users)} users</Eyebrow>
          <span className="font-mono text-[0.72rem] text-muted">{day(s.first_seen)} · first 24 h</span>
        </div>
        <DotStrip s={s} />
        <p className="text-[0.9rem] leading-relaxed text-body">
          The same number turns up in <b className="text-ink">{s.flagged_after} different people's payments</b> within {duration(s.first_seen, s.flagged_at)}.
          None of them had it saved. The network flags it, and {laterPeople} more people are sent to it before the week ends
          {s.sources.length > 1 ? `, first by ${SOURCE[s.sources[0]]} and later from a ${SOURCE[s.sources[1]]}` : ''}.
        </p>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 02  money
// ---------------------------------------------------------------------------

function MoneyBars({ r }: { r: NetworkReport }) {
  const [ref, seen] = useInView<HTMLDivElement>(0.3)
  const rows = [
    { label: 'Per-call checks only', m: r.per_call },
    { label: 'Per-call + network', m: r.with_network },
  ]
  const max = Math.max(r.per_call.scam_moved, 1)
  return (
    <div ref={ref} className={`card net-money flex flex-col gap-5 p-4 sm:p-6 ${seen ? 'is-seen' : ''}`}>
      <Eyebrow>Money that reached scammers in the simulated week</Eyebrow>
      {rows.map(({ label, m }, i) => (
        <div key={label} className="grid gap-2 sm:grid-cols-[11rem_minmax(0,1fr)] sm:items-center sm:gap-5">
          <div className="text-[0.88rem] font-semibold text-body">{label}</div>
          <div className="flex min-w-0 items-center gap-4">
            <div className="h-3 min-w-0 flex-1 overflow-hidden rounded-full bg-track">
              <div className="net-bar h-full rounded-full bg-bad" style={{ width: `${(m.scam_moved / max) * 100}%`, ...stagger(i) }} />
            </div>
            <div className="w-[8.5rem] shrink-0 text-right">
              <div className="font-display text-[1.35rem] leading-none font-semibold tracking-[-0.02em] tabular-nums sm:text-[1.6rem]">{taka(m.scam_moved)}</div>
              <div className="mt-1 text-[0.72rem] text-muted">{m.scam_moved_count} payments</div>
            </div>
          </div>
        </div>
      ))}
      <p className="border-t border-line pt-4 text-[0.88rem] leading-relaxed text-body">
        The per-call policy already stops {r.per_call.scam_stopped_agentshield} of {r.per_call.scam_attempts} scam payments: every one that came from an email or a web page.
        What gets through are phone scams. The victim types the number in the chat, so each single call looks like the user's own wish.
        Only the pattern across people gives them away.
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 03  rings
// ---------------------------------------------------------------------------

interface Pt { x: number; y: number }

/** Ring as a small graph: what links it in the middle (cash-out account or shared source), the numbers
 *  that collected money around it, and each payment to them as a dot on the outside, in time order. */
function Constellation({ ring }: { ring: NetRing }) {
  const [ref, seen] = useInView<HTMLDivElement>(0.25)
  const W = 440, H = 360, cx = W / 2, cy = H / 2
  const mules = ring.members.filter((m) => m.tier !== 'cashout')
  const cash = ring.members.filter((m) => m.tier === 'cashout')
  const hubs = cash.length
    ? cash.map((c) => ({ key: c.number, label: `cash-out ${tail(c.number)}`, kind: 'cash' as const }))
    : ring.origins.map((o) => ({ key: o, label: o, kind: 'origin' as const }))
  const n = Math.max(mules.length, 1)
  const R = 84
  const angle = (i: number) => -Math.PI / 2 + (i * 2 * Math.PI) / n + (n === 2 ? Math.PI / 2 : 0)
  const mulePos = new Map<string, Pt>(mules.map((m, i) => [m.number, { x: cx + R * Math.cos(angle(i)), y: cy + R * Math.sin(angle(i)) }]))
  // a cash-out account sits in the middle; a shared source sits between the numbers that appeared in it
  const hubPos = new Map<string, Pt>(hubs.map((h, i) => {
    if (h.kind === 'cash') return [h.key, { x: cx, y: cy + (i - (hubs.length - 1) / 2) * 36 }]
    const near = mules.filter((m) => m.origins.includes(h.key)).map((m) => mulePos.get(m.number)!)
    const mx = near.reduce((a, q) => a + q.x, 0) / Math.max(near.length, 1)
    const my = near.reduce((a, q) => a + q.y, 0) / Math.max(near.length, 1)
    return [h.key, { x: cx + (mx - cx) * 0.55, y: cy + (my - cy) * 0.55 }]
  }))
  // sources are lettered left to right, so the legend reads in the same order as the graph
  const origins = hubs.filter((h) => h.kind === 'origin').sort((a, b) => hubPos.get(a.key)!.x - hubPos.get(b.key)!.x)
  const letter = new Map(origins.map((h, i) => [h.key, String.fromCharCode(65 + i)]))

  const links = mules.flatMap((m) =>
    hubs
      .filter((h) => (h.kind === 'cash' ? ring.edges.some((e) => e.from === m.number && e.to === h.key) : m.origins.includes(h.key)))
      .map((h) => ({
        m: m.number, h: h.key,
        amount: ring.edges.filter((e) => e.from === m.number && e.to === h.key && !e.held).reduce((a, e) => a + e.amount, 0),
      })))
  const maxAmount = Math.max(...links.map((l) => l.amount), 1)

  // payment dots: rows of arcs on the outside of each number, earliest first
  const dots: { x: number; y: number; o: NetOutcome; key: string; i: number }[] = []
  let order = 0
  mules.forEach((m, i) => {
    const span = Math.min(((2 * Math.PI) / n) * 0.8, 2.4)
    const step = 8.6
    let r = R + 34
    let placed = 0
    const sorted = [...m.attempts].sort((a, b) => ms(a.t) - ms(b.t))
    while (placed < sorted.length) {
      const cap = Math.max(1, Math.floor((r * span) / step))
      const row = sorted.slice(placed, placed + cap)
      row.forEach((p, k) => {
        const a = angle(i) - span / 2 + (span * (k + 0.5)) / cap
        dots.push({ x: cx + r * Math.cos(a), y: cy + r * Math.sin(a), o: p.outcome, key: `${m.number}-${placed + k}`, i: order++ })
      })
      placed += row.length
      r += step
    }
  })

  return (
    <div ref={ref} className={`net-graph ${seen ? 'is-seen' : ''}`}>
      <svg viewBox={`0 0 ${W} ${H}`} className="mx-auto block h-auto w-full max-w-[440px]" role="img"
        aria-label={`${ring.name}: ${mules.length} collecting numbers, ${ring.people} people`}>
        <circle cx={cx} cy={cy} r={R} fill="none" stroke="var(--color-line)" strokeDasharray="2 5" />
        {links.map((l) => {
          const a = mulePos.get(l.m)!, b = hubPos.get(l.h)!
          const moved = l.amount > 0
          return (
            <line key={`${l.m}-${l.h}`} x1={a.x} y1={a.y} x2={b.x} y2={b.y}
              stroke={moved ? 'var(--color-bad)' : 'var(--color-muted)'} strokeOpacity={moved ? 0.55 : 0.55}
              strokeWidth={moved ? 1.2 + (l.amount / maxAmount) * 3.6 : 1.2} strokeDasharray={moved ? undefined : '4 4'} strokeLinecap="round" />
          )
        })}
        {dots.map((d) => (
          <circle key={d.key} className="net-dot" cx={d.x} cy={d.y} r={2.9} fill={OUTCOME[d.o].color} style={{ ['--d' as string]: `${Math.min(d.i * 9, 900)}ms` }} />
        ))}
        {hubs.map((h) => {
          const p = hubPos.get(h.key)!
          if (h.kind === 'origin')
            return (
              <g key={h.key}>
                <title>{h.key}</title>
                <rect x={p.x - 11} y={p.y - 11} width={22} height={22} rx={5} fill="var(--color-card2)" stroke="var(--color-muted)" strokeOpacity={0.8} />
                <text x={p.x} y={p.y + 4.3} textAnchor="middle" className="fill-ink font-mono" fontSize="12" fontWeight="700">{letter.get(h.key)}</text>
              </g>
            )
          const w = 112
          return (
            <g key={h.key}>
              <rect x={p.x - w / 2} y={p.y - 12.5} width={w} height={25} rx={7}
                fill="var(--color-card2)" stroke={h.kind === 'cash' ? 'var(--color-bad)' : 'var(--color-line2)'} strokeOpacity={h.kind === 'cash' ? 0.6 : 1} />
              <text x={p.x} y={p.y + 4.2} textAnchor="middle" className={`font-mono ${h.kind === 'cash' ? 'fill-bad-ink' : 'fill-body'}`} fontSize="12">{h.label}</text>
            </g>
          )
        })}
        {mules.map((m) => {
          const p = mulePos.get(m.number)!
          const watch = m.tier === 'watch'
          return (
            <g key={m.number}>
              <title>{`${phone(m.number)}: ${m.payers} people, flagged after ${m.flagged_after}`}</title>
              <circle cx={p.x} cy={p.y} r={10} fill="var(--color-card)" stroke={watch ? 'var(--color-warn)' : 'var(--color-bad)'} strokeWidth={1.6} />
              <circle cx={p.x} cy={p.y} r={3.4} fill={watch ? 'var(--color-warn)' : 'var(--color-bad)'} />
              <text x={p.x} y={p.y + (p.y > cy ? 28 : -17)} textAnchor="middle" className="fill-ink font-mono" fontSize="12.5" fontWeight="600">{tail(m.number)}</text>
            </g>
          )
        })}
      </svg>
      {origins.length > 0 && (
        <ul className="mt-1 mb-4 flex flex-wrap justify-center gap-x-4 gap-y-1 font-mono text-[0.74rem] text-muted">
          {origins.map((h) => (
            <li key={h.key}><span className="mr-1.5 inline-flex h-[18px] w-[18px] items-center justify-center rounded border border-muted/60 text-[0.68rem] font-bold text-ink">{letter.get(h.key)}</span>{h.key}</li>
          ))}
        </ul>
      )}
    </div>
  )
}

/** Every payment to one number on the ring's own time axis, with the moment it was flagged. */
function Track({ m, from, to }: { m: NetMember; from: number; to: number }) {
  const at = (t: number) => `${((t - from) / Math.max(to - from, 1)) * 100}%`
  return (
    <div className="relative h-5 min-w-0" aria-hidden>
      <span className="absolute inset-x-0 top-1/2 h-px bg-line2" />
      {m.attempts.map((p: NetPayment, i) => (
        <span key={i} className="absolute top-1/2 h-[7px] w-[7px] -translate-x-1/2 -translate-y-1/2 rounded-full"
          style={{ left: at(ms(p.t)), background: OUTCOME[p.outcome].color, opacity: 0.9 }} />
      ))}
      {m.flagged_at && (
        <span className="absolute -top-0.5 -bottom-0.5 w-[2px] -translate-x-1/2 rounded-full bg-ink shadow-[0_0_0_2px_var(--color-card)]" style={{ left: at(ms(m.flagged_at)) }} />
      )}
    </div>
  )
}

/** Says what the "caught after" sequence shows, without claiming more than the numbers do. */
function caughtNote(caught: NetMember[], viaMoney: boolean): string {
  const first = caught[0].flagged_after!
  const last = caught[caught.length - 1].flagged_after!
  const how = viaMoney ? 'it sent money to the cash-out account the graph already knew' : 'it showed up in a source the graph had already tied to a flagged number'
  if (last >= first) return 'Later numbers were not caught faster here.'
  return `The last number needed ${last === 1 ? 'only one person' : `only ${last} people`}: ${how}.`
}

function RingCard({ ring }: { ring: NetRing }) {
  const mules = ring.members.filter((m) => m.tier !== 'cashout')
  const cash = ring.members.filter((m) => m.tier === 'cashout')
  const caught = mules.filter((m) => m.flagged_after != null).sort((a, b) => ms(a.flagged_at!) - ms(b.flagged_at!))
  const from = ms(ring.first) - 30 * 60e3
  const to = ms(ring.last) + 30 * 60e3
  const linkedBy = cash.length
    ? `${mules.length} numbers send their money on to the same cash-out account.`
    : `${mules.length} numbers appear in the same ${ring.origins.length > 1 ? `${ring.origins.length} sources` : 'source'}; one number is reused across them.`
  const sources = ring.sources.map((s) => SOURCE[s] ?? s).join(' + ')
  const saved = ring.moved_per_call - ring.moved_with_network

  return (
    <article className="card flex min-w-0 flex-col p-4 sm:p-5">
      <header className="flex flex-col gap-1">
        <div className="flex flex-wrap items-baseline justify-between gap-x-4 gap-y-1">
          <h3 className="text-[1.2rem] font-semibold tracking-[-0.02em]">{ring.name}</h3>
          <span className="font-mono text-[0.72rem] text-muted">{day(ring.first)} – {day(ring.last)}</span>
        </div>
        <p className="text-[0.86rem] leading-relaxed text-body">{linkedBy}</p>
        <p className="font-mono text-[0.74rem] text-muted">{ring.people} people · {ring.attempts} payments · {sources}</p>
      </header>

      <Constellation ring={ring} />

      <div className="mt-1 flex flex-col">
        <div className="mb-2 flex items-baseline justify-between gap-3 text-[0.74rem] text-muted">
          <span>Each number, on the ring's own time axis</span>
          <span>flagged after</span>
        </div>
        <ol className="flex flex-col divide-y divide-line">
          {caught.map((m) => (
            <li key={m.number} className="grid grid-cols-[6.6rem_minmax(0,1fr)_4.6rem] items-center gap-3 py-2.5">
              <span className="font-mono text-[0.78rem] text-ink">{phone(m.number)}</span>
              <Track m={m} from={from} to={to} />
              <span className="text-right">
                <span className="font-display text-[1.15rem] font-semibold tabular-nums">{m.flagged_after}</span>
                <span className="ml-1 text-[0.72rem] text-muted">{m.flagged_after === 1 ? 'person' : 'people'}</span>
              </span>
            </li>
          ))}
          {cash.map((c) => (
            <li key={c.number} className="flex flex-col gap-1.5 py-3">
              <div className="flex items-center justify-between gap-3">
                <span className="font-mono text-[0.78rem] text-bad-ink">{phone(c.number)}</span>
                <TierTag tier="cashout" />
              </div>
              <p className="text-[0.8rem] leading-relaxed text-body">
                Most of its money came from flagged numbers, so it is marked as the ring's cash-out ({day(c.flagged_at!)}, {clock(c.flagged_at!)}).
                Nobody paid it directly: only the graph finds it.
              </p>
            </li>
          ))}
        </ol>
        {caught.length > 1 && (
          <p className="mt-3 rounded-xl border border-line bg-tile px-3.5 py-2.5 text-[0.84rem] leading-relaxed text-body">
            Caught after <span className="font-mono text-ink">{caught.map((m) => m.flagged_after).join(' → ')}</span> people.
            {' '}{caughtNote(caught, cash.length > 0)}
          </p>
        )}
      </div>

      {ring.moved_per_call === 0 ? (
        <footer className="mt-4 border-t border-line pt-4">
          <p className="text-[0.86rem] leading-relaxed text-body">
            <span className="font-display font-semibold text-ink">{taka(0)}</span> reached this ring, with or without the network check: every payment was
            triggered by untrusted content ({sources}), and the per-call policy blocked each one. Here the network's job is to name the numbers.
          </p>
          <div className="mt-2 text-[0.72rem] text-muted">Simulation truth: {ring.truth.join('; ')}</div>
        </footer>
      ) : (
      <footer className="mt-4 grid grid-cols-2 gap-3 border-t border-line pt-4">
        <div>
          <div className="text-[0.74rem] text-muted">Reached the ring, per-call only</div>
          <div className="mt-1 font-display text-[1.2rem] font-semibold tabular-nums">{taka(ring.moved_per_call)}</div>
        </div>
        <div>
          <div className="text-[0.74rem] text-muted">With the network check</div>
          <div className="mt-1 font-display text-[1.2rem] font-semibold tabular-nums">
            {taka(ring.moved_with_network)}
            {saved > 0 && <span className="ml-2 align-middle text-[0.74rem] font-semibold text-ok-ink">−{taka(saved)}</span>}
          </div>
        </div>
        <div className="col-span-2 text-[0.72rem] text-muted">Simulation truth: {ring.truth.join('; ')}</div>
      </footer>
      )}
    </article>
  )
}

// ---------------------------------------------------------------------------
// 04  close calls
// ---------------------------------------------------------------------------

function ScoreBar({ a, p, className = 'w-full max-w-[11rem]' }: { a: NetAccount; p: NetworkReport['params']; className?: string }) {
  return (
    <div className={`relative ${className}`}>
      <div className="flex h-2 w-full overflow-hidden rounded-full bg-track">
        {PARTS.map(({ key, color }) => (
          <span key={key} className="h-full" style={{ width: `${Math.min(a.parts[key], 1) * 100}%`, background: color }} />
        ))}
      </div>
      {[p.watch_at, p.flag_at].map((t) => (
        <span key={t} className="absolute -top-1 -bottom-1 w-px bg-ink/50" style={{ left: `${t * 100}%` }} aria-hidden />
      ))}
    </div>
  )
}

function why(a: NetAccount): string {
  const bits: string[] = []
  if (a.strangers) bits.push(`${a.strangers} strangers paid it within 24 h`)
  else bits.push('everyone who paid it had it saved')
  bits.push(a.pass_through ? `it sent on ${pct(a.pass_through)} of what it received` : 'it kept the money')
  if (a.untrusted) bits.push(`${pct(a.untrusted)} of the payments came from untrusted sources`)
  return bits.join(', ') + '.'
}

function CloseCall({ a, p }: { a: NetAccount; p: NetworkReport['params'] }) {
  const legit = a.truth === 'legit'
  const verdict =
    a.tier === 'watch'
      ? legit
        ? 'Not blocked, which is right. Its new customers get one extra confirmation.'
        : 'Not blocked: too few people to be sure, so this is a miss.'
      : legit
        ? 'Clear, which is right.'
        : 'Clear: missed.'
  return (
    <div className="card flex min-w-0 flex-col gap-3 p-4 sm:p-5">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <div className="text-[1rem] font-semibold">{a.known_as}</div>
          <div className="font-mono text-[0.76rem] text-muted">{phone(a.number)} · {a.payers} people paid it</div>
        </div>
        <TierTag tier={a.tier} />
      </div>
      <div className="flex items-center gap-3">
        <ScoreBar a={a} p={p} />
        <span className="font-mono text-[0.8rem] tabular-nums text-ink">{a.score.toFixed(2)}</span>
      </div>
      <p className="text-[0.86rem] leading-relaxed text-body">{why(a)}</p>
      <p className={`mt-auto border-t border-line pt-3 text-[0.82rem] leading-relaxed ${legit ? 'text-ok-ink' : 'text-warn-ink'}`}>
        <span className="text-muted">Simulation truth: {legit ? 'a real ' + a.known_as.toLowerCase() : 'a scam number'}. </span>
        {verdict}
      </p>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 05  every scored account
// ---------------------------------------------------------------------------

const th = 'border-b border-line px-3.5 py-3 text-left text-[0.76rem] font-medium leading-snug text-muted whitespace-nowrap'
const td = 'border-b border-line/50 px-3.5 py-3 align-middle tabular-nums'

function AccountsTable({ r }: { r: NetworkReport }) {
  return (
    <div className="card overflow-hidden">
      <div className="border-b border-line px-4 py-2.5 md:hidden">
        <span className="text-[0.74rem] text-muted">Swipe sideways for all columns</span>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[860px] border-collapse text-[0.83rem]">
          <thead>
            <tr>
              <th className={th}>Number</th><th className={th}>Known to the wallet as</th><th className={th}>Score</th>
              <th className={th}>Strangers / 24 h</th><th className={th}>Sent on</th><th className={th}>Untrusted</th>
              <th className={th}>Linked</th><th className={th}>Result</th><th className={th}>Simulation truth</th>
            </tr>
          </thead>
          <tbody>
            {r.accounts.map((a) => (
              <tr key={a.number} className="transition-colors hover:bg-fg/[0.025]">
                <td className={td}><span className="font-mono text-[0.78rem] whitespace-nowrap">{phone(a.number)}</span></td>
                <td className={`${td} whitespace-nowrap text-body`}>{a.known_as}</td>
                <td className={td}>
                  <div className="flex items-center gap-2.5">
                    <ScoreBar a={a} p={r.params} className="w-28 shrink-0" />
                    <span className="font-mono text-[0.76rem]">{a.score.toFixed(2)}</span>
                  </div>
                </td>
                <td className={td}>{a.strangers}</td>
                <td className={td}>{a.pass_through ? pct(a.pass_through) : '–'}</td>
                <td className={td}>{a.untrusted ? pct(a.untrusted) : '–'}</td>
                <td className={td}>{a.linked ? 'yes' : '–'}</td>
                <td className={td}><TierTag tier={a.tier} /></td>
                <td className={`${td} whitespace-nowrap ${a.truth === 'legit' ? 'text-body' : 'text-bad-ink'}`}>
                  {a.truth === 'legit' ? `legit (${a.truth_role})` : a.truth}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="flex flex-wrap gap-x-4 gap-y-1.5 border-t border-line px-4 py-3 text-[0.74rem] text-muted">
        {PARTS.map((p) => (
          <span key={p.key} className="inline-flex items-center gap-1.5">
            <span className="h-2 w-3 rounded-sm" style={{ background: p.color }} aria-hidden />{p.label}
          </span>
        ))}
        <span className="inline-flex items-center gap-1.5"><span className="h-3 w-px bg-ink/50" aria-hidden />watch {r.params.watch_at} · flag {r.params.flag_at}</span>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// 06  method and limits
// ---------------------------------------------------------------------------

function Method({ r }: { r: NetworkReport }) {
  const p = r.params
  const w = p.weights
  const e = r.evaluation
  const lines: [string, string][] = [
    ['fan_in', `strangers paying it in ${p.window_hours} h ÷ ${p.fan_in_full}, at most 1`],
    ['pass_through', `money it sent on ÷ money it received, last ${p.window_hours} h (from ${num(p.min_inflow)} BDT in)`],
    ['untrusted', 'share of its payments that came from an email, web page or file'],
    ['linked', 'it pays a cash-out account, or shares a source with a flagged number'],
  ]
  const results: [string, ReactNode][] = [
    ['Scam numbers flagged', <>{e.mules_flagged} of {e.mules}{e.mules_watch ? <span className="text-muted"> · {e.mules_watch} on watch</span> : null}</>],
    ['Cash-out accounts found', <>{e.cashouts_found} of {e.cashouts}</>],
    ['Legit accounts flagged', <>{e.legit_flagged} of {num(e.legit_accounts)}</>],
    ['Legit accounts on watch', <>{e.legit_watch}</>],
  ]
  return (
    <div className="grid gap-3 lg:grid-cols-[minmax(0,7fr)_minmax(0,5fr)] lg:gap-4">
      <div className="card min-w-0 p-4 sm:p-5">
        <Eyebrow>Score, per receiving number, after every payment</Eyebrow>
        <pre className="mt-3 overflow-x-auto rounded-xl border border-line bg-well/25 p-3.5 font-mono text-[0.78rem] leading-[1.75] text-body">
          <span className="text-ink">score</span> = {w.fan_in}·fan_in{NL}      + {w.pass_through}·pass_through{NL}      + {w.untrusted}·untrusted{NL}      + {w.linked}·linked   <span className="text-muted">(at most 1)</span>
        </pre>
        <dl className="mt-3 grid gap-x-4 gap-y-2 text-[0.84rem] sm:grid-cols-[8.5rem_minmax(0,1fr)]">
          {lines.map(([k, v]) => (
            <Fragment key={k}>
              <dt className="font-mono text-[0.78rem] text-soft">{k}</dt>
              <dd className="text-body">{v}</dd>
            </Fragment>
          ))}
        </dl>
        <ul className="mt-4 flex flex-col gap-1.5 border-t border-line pt-4 text-[0.84rem] text-body">
          <li><span className="font-mono text-ink">≥ {p.flag_at}</span> flagged: every later payment to it is blocked, and its own transfers are held.</li>
          <li><span className="font-mono text-ink">≥ {p.watch_at}</span> watch: later payments to it need the user's confirmation.</li>
          <li>An account that gets at least {pct(p.cashout_share)} of its money from flagged numbers is marked as cash-out.</li>
        </ul>
      </div>
      <div className="card flex min-w-0 flex-col p-4 sm:p-5">
        <Eyebrow>Against the simulation's truth</Eyebrow>
        <dl className="mt-3 flex flex-col divide-y divide-line">
          {results.map(([k, v]) => (
            <div key={k} className="flex items-baseline justify-between gap-4 py-2.5">
              <dt className="text-[0.86rem] text-body">{k}</dt>
              <dd className="font-mono text-[0.86rem] text-ink tabular-nums">{v}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-auto pt-4 text-[0.8rem] leading-relaxed text-muted">
          {r.note} Approval rates assumed: {pct(p.approve_legit)} for real payments, {pct(p.approve_scam)} for scam victims. Seed {p.seed}.
        </p>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// page
// ---------------------------------------------------------------------------

function closeCallSummary(watch: NetAccount[]): string {
  const right = watch.filter((a) => a.truth === 'legit').length
  const missed = watch.length - right
  const parts = []
  if (right) parts.push(`${right} rightly left open`)
  if (missed) parts.push(`${missed} ${missed === 1 ? 'scam' : 'scams'} missed`)
  return parts.join(', ')
}

export default function Network() {
  const { data: r, error, isPending } = useQuery({ queryKey: ['network'], queryFn: api.network, staleTime: Infinity })
  const watch = r?.accounts.filter((a) => a.tier === 'watch') ?? []
  const stats = r
    ? [
        { label: 'Stopped by the network', value: num(r.with_network.scam_stopped_network), note: 'scam payments the per-call checks let through', tone: 'var(--color-info)' },
        { label: 'Real payments made', value: `${num(r.with_network.legit_paid)}`, note: `of ${num(r.with_network.legit_attempts)} · per-call only ${num(r.per_call.legit_paid)}` },
        { label: 'Extra confirmations', value: num(r.with_network.legit_extra_confirm), note: `real payments asked again, ${r.with_network.legit_declined_network} declined` },
        { label: 'Real accounts flagged', value: `${r.evaluation.legit_flagged}`, note: `of ${num(r.evaluation.legit_accounts)} real accounts`, tone: 'var(--color-ok)' },
      ]
    : []

  return (
    <>
      <PageHeader
        title="Network"
        sub="AgentShield judges one payment for one person. A wallet that runs it for everyone can also see the same stranger across many people, and where their money goes next. One simulated week, replayed in time order."
        right={
          r && (
            <span className="inline-flex min-h-9 items-center gap-2 rounded-xl border border-warn/30 bg-warn/[0.07] px-3 font-mono text-[0.74rem] text-warn-ink">
              Simulation · {num(r.world.users)} users · 7 days
            </span>
          )
        }
      />
      {isPending && <PageSkeleton cards={4} />}
      {error && <ErrorNote error={error} />}
      {r && (
        <div className="flex flex-col gap-12">
          <Reveal>
            <Section n={1} title="One payment, or a pattern">
              <Contrast r={r} />
            </Section>
          </Reveal>

          <Reveal>
            <Section n={2} title="What the network check adds">
              <MoneyBars r={r} />
              <StatRail label="Network check outcomes" items={stats} />
            </Section>
          </Reveal>

          <Reveal>
            <Section n={3} title="Rings"
              sub="Numbers are joined when money moves between them or when they appear in the same untrusted source. Each dot is one payment, earliest first.">
              <Legend items={['moved', 'agentshield', 'network']} />
              <div className="grid gap-3 lg:grid-cols-2 lg:gap-4">
                {r.rings.map((ring) => <RingCard key={ring.id} ring={ring} />)}
              </div>
            </Section>
          </Reveal>

          {watch.length > 0 && (
            <Reveal>
              <Section n={4} title="Close calls"
                sub={`Numbers that looked suspicious but stayed below the flag line: ${closeCallSummary(watch)}.`}>
                <div className="grid gap-3 md:grid-cols-2 lg:gap-4">
                  {watch.map((a) => <CloseCall key={a.number} a={a} p={r.params} />)}
                </div>
              </Section>
            </Reveal>
          )}

          <Reveal>
            <Section n={watch.length ? 5 : 4} title="Every scored number"
              sub="All accounts with a score above 0.05 at their peak, with the simulation's ground truth beside the result.">
              <AccountsTable r={r} />
            </Section>
          </Reveal>

          <Reveal>
            <Section n={watch.length ? 6 : 5} title="Method and limits">
              <Method r={r} />
            </Section>
          </Reveal>
        </div>
      )}
    </>
  )
}
