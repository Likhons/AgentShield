import Logo from './Logo'
import ThemeToggle from './ThemeToggle'
import { useTheme } from '../lib/theme'
import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ChartColumn, GitBranch, Languages, Loader2, Menu, ScrollText, SquareTerminal, Waypoints, X, type LucideIcon } from 'lucide-react'
import type { Overview } from '../lib/api'
import { useEffect, useRef, useState } from 'react'
import { Link, NavLink, Outlet, useLocation } from 'react-router-dom'
import { api } from '../lib/api'
import { lockScroll, scrollToTop, unlockScroll } from '../lib/motion'
import { prefetchPages, warmRoute } from '../lib/pages'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
  /** small marker on the right, from live data: a count chip or a short tag */
  badge?: (o: Overview) => { text: string; kind: 'count' | 'tag' } | null
}

const SECTIONS: { title: string; items: NavItem[] }[] = [
  {
    title: 'Workspace',
    items: [
      { to: '/playground', label: 'Playground', icon: SquareTerminal },
      { to: '/benchmarks', label: 'Benchmarks', icon: ChartColumn },
      { to: '/audit', label: 'Audit Log', icon: ScrollText, badge: (o) => ({ text: compact(o.decisions_logged), kind: 'count' }) },
    ],
  },
  {
    title: 'Security',
    items: [
      { to: '/policies', label: 'Policies', icon: GitBranch, badge: (o) => ({ text: String(o.policy_rules), kind: 'count' }) },
      { to: '/datasets', label: 'Datasets', icon: Languages, badge: () => ({ text: 'BN/EN', kind: 'tag' }) },
      { to: '/network', label: 'Network', icon: Waypoints, badge: () => ({ text: 'SIM', kind: 'tag' }) },
    ],
  },
]

/** 454 -> "454", 1234 -> "1.2k" */
const compact = (n: number) => (n < 1000 ? String(n) : `${(n / 1000).toFixed(n < 10000 ? 1 : 0)}k`)
const ALL_ITEMS = SECTIONS.flatMap((s) => s.items)

function Brand() {
  return (
    <Link to="/" aria-label="AgentShield home" className="flex min-h-11 items-center">
      <Logo sub="AI Agent Safety Platform" size={34} />
    </Link>
  )
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  const { data } = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  const qc = useQueryClient()
  return (
    <nav aria-label="Main" className="flex flex-col gap-6 lg:gap-5">
      {SECTIONS.map((section) => (
        <div key={section.title}>
          <div className="mb-2.5 px-3 font-mono text-[0.68rem] tracking-[0.2em] text-muted uppercase lg:mb-2">{section.title}</div>
          {/* desktop (mouse): 40 px rows packed tight; the phone drawer keeps 44 px touch targets */}
          <ul className="flex flex-col gap-1.5 lg:gap-0.5">
            {section.items.map(({ to, label, icon: Icon, badge }) => {
              const b = data && badge ? badge(data) : null
              return (
                <li key={to}>
                  <NavLink
                    to={to}
                    onClick={onNavigate}
                    onMouseEnter={() => warmRoute(to, qc)}
                    onFocus={() => warmRoute(to, qc)}
                    onTouchStart={() => warmRoute(to, qc)}
                    className={({ isActive }) =>
                      `nav-item flex min-h-11 items-center gap-3 rounded-xl border px-3 text-[0.95rem] font-semibold lg:min-h-10 ${isActive ? 'nav-active' : 'border-transparent text-body'}`
                    }
                  >
                    {({ isActive }) => (
                      <>
                        <Icon size={18} strokeWidth={1.8} className="shrink-0" aria-hidden />
                        <span className="min-w-0 flex-1 truncate">{label}</span>
                        {isActive ? (
                          <span className="nav-dot h-1.5 w-1.5 shrink-0 rounded-full" aria-hidden />
                        ) : b?.kind === 'count' ? (
                          <span className="shrink-0 rounded-md border border-fg/10 bg-fg/[0.04] px-1.5 py-0.5 font-mono text-[0.68rem] text-muted tabular-nums">{b.text}</span>
                        ) : b ? (
                          <span className="shrink-0 font-mono text-[0.68rem] font-bold tracking-wide text-ok-ink">{b.text}</span>
                        ) : null}
                      </>
                    )}
                  </NavLink>
                </li>
              )
            })}
          </ul>
        </div>
      ))}
    </nav>
  )
}

const PING_EVERY_MS = 15_000
const PING_KEEP = 14

/** Round trip to the gateway's /health, measured in the browser every 15 s while the app is open.
 *  online: null until the first answer, then whether the last check got one. */
function usePing() {
  const [pings, setPings] = useState<number[]>([])
  const [online, setOnline] = useState<boolean | null>(null)
  useEffect(() => {
    let alive = true
    const ping = async () => {
      if (document.hidden) return
      const t0 = performance.now()
      try {
        const r = await fetch('/health', { cache: 'no-store' })
        if (!alive) return
        if (!r.ok) return setOnline(false)
        const ms = Math.round(performance.now() - t0)
        setPings((p) => [...p.slice(-(PING_KEEP - 1)), ms])
        setOnline(true)
      } catch {
        if (alive) setOnline(false) // keep the last values, show the gateway as unreachable
      }
    }
    void ping()
    const id = window.setInterval(ping, PING_EVERY_MS)
    return () => { alive = false; clearInterval(id) }
  }, [])
  return { pings, online }
}

/** Five bars that bounce like an equalizer while the gateway answers; they lie flat when it does not. */
function Heartbeat({ live }: { live: boolean }) {
  return (
    <span className={`eq ${live ? 'is-live' : ''} flex h-4 shrink-0 items-end gap-[2px]`} aria-hidden>
      {[0, 1, 2, 3, 4].map((i) => (
        <span key={i} className={`eq-bar w-[3px] rounded-full ${live ? 'bg-ok' : 'bg-fg/20'}`} />
      ))}
    </span>
  )
}

function StatusCard() {
  const { data } = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  const { pings, online } = usePing()
  const last = pings.at(-1)
  const max = Math.max(...pings, 1)
  const live = !!data && online !== false
  const label = online === false ? 'Gateway Unreachable' : data ? 'Gateway Ready' : 'Connecting…'
  const rows: [string, string | number][] = data
    ? [
        ['model', data.agent_llm],
        ['detector', data.detector],
        ['policy', `${data.policy_rules} rules`],
        ['decisions', data.decisions_logged],
      ]
    : []
  return (
    <div className="glass spotlight min-w-0 p-4">
      <div className="relative mb-3 flex items-center justify-between gap-2">
        <span className="flex min-w-0 items-center gap-2 text-[0.84rem] font-bold">
          <span className="relative flex h-2.5 w-2.5 shrink-0" aria-hidden>
            {live && <span className="absolute inset-0 animate-ping rounded-full bg-ok/60" />}
            <span className={`relative h-2.5 w-2.5 rounded-full ${online === false ? 'bg-bad' : data ? 'bg-ok' : 'bg-muted'}`} />
          </span>
          <span className="truncate">{label}</span>
        </span>
        <Heartbeat live={live} />
      </div>
      {/* ping history: one bar per check, newest on the right */}
      <div className="relative flex h-9 items-end gap-[3px]" role="img" aria-label={last !== undefined ? `API ping, last ${last} milliseconds` : 'API ping not measured yet'}>
        {Array.from({ length: PING_KEEP }, (_, i) => {
          const v = pings[i - (PING_KEEP - pings.length)]
          return (
            <span
              key={i}
              className={`spark-bar min-w-0 flex-1 rounded-sm ${v === undefined ? 'bg-fg/8' : i === PING_KEEP - 1 ? 'bg-ok' : 'bg-ok/45'}`}
              style={{ height: '100%', transform: `scaleY(${v === undefined ? 0.12 : Math.max(0.12, v / max)})` }}
            />
          )
        })}
      </div>
      <div className="relative mt-2 mb-3 flex items-center justify-between gap-2 font-mono text-[0.7rem] text-muted">
        <span className="truncate">round trip</span>
        <span className="shrink-0 rounded-full border border-ok/35 bg-ok/10 px-2 py-0.5 text-[0.68rem] font-semibold text-ok-ink tabular-nums" title="Round trip to /health from this browser">
          {last !== undefined ? `${last} ms` : '– ms'}
        </span>
      </div>
      <dl className="relative flex flex-col gap-1.5 text-[0.8rem]">
        {rows.map(([k, v]) => (
          <div key={k} className="flex min-w-0 justify-between gap-2">
            <dt className="font-mono text-[0.74rem] text-muted">{k}</dt>
            <dd className="truncate font-mono text-[0.76rem] font-semibold tabular-nums">{v}</dd>
          </div>
        ))}
      </dl>
      {data && <div className="relative mt-3 border-t border-line pt-2 font-mono text-[0.7rem] text-muted">v{data.version} · API ping</div>}
    </div>
  )
}

/** Sidebar row: which theme is on, and the switch. */
function ThemeRow() {
  const day = useTheme() === 'light'
  return (
    <div className="flex items-center justify-between gap-3 rounded-xl border border-line px-3 py-2">
      <span className="text-sm">
        <span className="block font-semibold">{day ? 'Day mode' : 'Night mode'}</span>
        <span className="block text-xs text-muted">{day ? 'Bright and clear' : 'Low glare'}</span>
      </span>
      <ThemeToggle />
    </div>
  )
}

/** Free hosting puts the API to sleep when idle; the first answer can take about a minute. Say so instead of
 *  leaving the visitor with spinners. */
function WakeNotice() {
  const { isPending, isError } = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  const [slow, setSlow] = useState(false)
  useEffect(() => {
    if (!isPending) return
    const id = window.setTimeout(() => setSlow(true), 3500)
    return () => clearTimeout(id)
  }, [isPending])
  if (!slow || !isPending || isError) return null
  return (
    <div role="status" className="fixed inset-x-3 bottom-3 z-40 mx-auto flex max-w-md items-center gap-3 rounded-xl border border-line2 bg-card2 px-4 py-3 text-[0.86rem] leading-snug text-body shadow-[0_18px_40px_-20px_rgb(0_0_0/0.8)] lg:left-[252px]">
      <Loader2 size={17} className="shrink-0 animate-spin text-soft" aria-hidden />
      Waking the demo server. Free hosting sleeps when idle, so the first load can take up to a minute.
    </div>
  )
}

export default function Layout() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const drawerRef = useRef<HTMLDivElement>(null)
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const current = ALL_ITEMS.find((i) => location.pathname.startsWith(i.to))

  useEffect(() => scrollToTop(), [location.pathname])
  // in the dashboard, the other pages are likely next: load their code while the browser is idle
  useEffect(() => prefetchPages(), [])

  // nav links close the drawer themselves; Escape closes it; focus moves in and back out
  useEffect(() => {
    if (!open) return
    const menuButton = menuButtonRef.current
    drawerRef.current?.querySelector<HTMLElement>('a, button')?.focus({ preventScroll: true })
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('keydown', onKey)
    lockScroll()
    return () => {
      document.removeEventListener('keydown', onKey)
      unlockScroll()
      menuButton?.focus({ preventScroll: true })
    }
  }, [open])

  return (
    <div className="relative min-h-dvh lg:pl-[240px]">
      <div className="cyber-grid app-grid" aria-hidden />
      <div className="aurora aurora-lime -top-40 right-[-10%] h-[620px] w-[620px]" aria-hidden />
      <div className="aurora aurora-emerald bottom-[-20%] left-[10%] h-[560px] w-[560px]" aria-hidden />
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-3 focus:py-2">
        Skip to main content
      </a>

      {/* desktop sidebar */}
      <aside data-lenis-prevent className="sidebar-glass fixed inset-y-0 left-0 z-20 hidden w-[240px] flex-col gap-6 overflow-y-auto px-4 py-6 lg:flex">
        <Brand />
        <div className="side-rule" aria-hidden />
        <NavList />
        <div className="mt-auto flex flex-col gap-3">
          <ThemeRow />
          <StatusCard />
        </div>
      </aside>

      {/* mobile / tablet top bar */}
      <header data-scroll-header className="sidebar-glass sticky top-0 z-30 flex h-14 items-center justify-between border-b border-line px-4 lg:hidden">
        <Brand />
        <div className="flex items-center gap-2">
          {current && (
            <span className="hidden rounded-full border border-line2 bg-accent/15 px-3 py-1 text-xs font-semibold text-soft sm:inline">
              {current.label}
            </span>
          )}
          <ThemeToggle />
          <button
            ref={menuButtonRef}
            type="button"
            onClick={() => setOpen(true)}
            aria-label="Open menu"
            aria-expanded={open}
            aria-controls="mobile-drawer"
            className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-line2 bg-card2/80"
          >
            <Menu size={20} aria-hidden />
          </button>
        </div>
      </header>

      {/* mobile drawer */}
      <div
        className={`fixed inset-0 z-40 bg-black/60 transition-opacity lg:hidden ${open ? 'opacity-100 backdrop-blur-sm' : 'pointer-events-none opacity-0'}`}
        onClick={() => setOpen(false)}
        aria-hidden
      />
      <div
        id="mobile-drawer"
        ref={drawerRef}
        role="dialog"
        aria-modal="true"
        aria-label="Navigation"
        inert={!open}
        data-lenis-prevent
        className={`fixed inset-y-0 left-0 z-50 flex w-[min(300px,86vw)] flex-col gap-6 overflow-y-auto border-r border-line2 bg-side px-4 py-5 transition-transform duration-300 ease-out-soft lg:hidden ${
          open ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="flex items-center justify-between">
          <Brand />
          <button
            type="button"
            onClick={() => setOpen(false)}
            aria-label="Close menu"
            className="inline-flex h-11 w-11 items-center justify-center rounded-xl border border-line"
          >
            <X size={18} aria-hidden />
          </button>
        </div>
        <div className="side-rule" aria-hidden />
        <NavList onNavigate={() => setOpen(false)} />
        <div className="mt-auto">
          <StatusCard />
        </div>
      </div>

      <main id="main" className="relative mx-auto w-full max-w-[1480px] px-4 py-5 sm:px-6 lg:px-9 lg:py-7">
        {/* each page fades in on navigation and starts at the top */}
        <div key={location.pathname} className="page-enter">
          <Outlet />
        </div>
      </main>
      <WakeNotice />
    </div>
  )
}
