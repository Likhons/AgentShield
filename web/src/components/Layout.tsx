import { useQuery } from '@tanstack/react-query'
import { ChartColumn, Database, FileText, Menu, PlayCircle, Scale, ShieldCheck, X, type LucideIcon } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { NavLink, Outlet, useLocation } from 'react-router-dom'
import { api } from '../lib/api'

interface NavItem {
  to: string
  label: string
  icon: LucideIcon
}

const SECTIONS: { title: string; items: NavItem[] }[] = [
  {
    title: 'Workspace',
    items: [
      { to: '/', label: 'Playground', icon: PlayCircle },
      { to: '/benchmarks', label: 'Benchmarks', icon: ChartColumn },
      { to: '/audit', label: 'Audit Log', icon: FileText },
    ],
  },
  {
    title: 'Security',
    items: [
      { to: '/policies', label: 'Policies', icon: Scale },
      { to: '/datasets', label: 'Datasets', icon: Database },
    ],
  },
]
const ALL_ITEMS = SECTIONS.flatMap((s) => s.items)

function Brand() {
  return (
    <div className="flex items-center gap-3">
      <span className="icon-tile h-10 w-10">
        <ShieldCheck size={21} className="text-[#E9D5FF]" aria-hidden />
      </span>
      <div className="leading-tight">
        <div className="text-[1.15rem] font-extrabold tracking-tight">AgentShield</div>
        <div className="text-xs text-[#C9B6FF]">AI Agent Safety Platform</div>
      </div>
    </div>
  )
}

function NavList({ onNavigate }: { onNavigate?: () => void }) {
  return (
    <nav aria-label="Main" className="flex flex-col gap-5">
      {SECTIONS.map((section) => (
        <div key={section.title}>
          <div className="mb-2 px-2 text-[0.7rem] font-semibold tracking-[0.14em] text-muted uppercase">{section.title}</div>
          <ul className="flex flex-col gap-1">
            {section.items.map(({ to, label, icon: Icon }) => (
              <li key={to}>
                <NavLink
                  to={to}
                  end={to === '/'}
                  onClick={onNavigate}
                  className={({ isActive }) =>
                    `flex min-h-11 items-center gap-3 rounded-xl border px-3.5 text-[0.95rem] font-semibold transition-colors ${
                      isActive
                        ? 'border-accent2/60 bg-gradient-to-r from-accent/80 to-accent2/60 text-white shadow-[0_8px_24px_-10px_rgba(145,71,255,.8)]'
                        : 'border-transparent text-[#D5DCF6] hover:border-line hover:bg-white/5'
                    }`
                  }
                >
                  <Icon size={17} aria-hidden />
                  {label}
                </NavLink>
              </li>
            ))}
          </ul>
        </div>
      ))}
    </nav>
  )
}

function StatusCard() {
  const { data } = useQuery({ queryKey: ['overview'], queryFn: api.overview })
  const rows: [string, string | number][] = data
    ? [
        ['Agent LLM', data.agent_llm],
        ['Injection detector', data.detector],
        ['Checks', data.checks.length],
        ['Policy rules', data.policy_rules],
        ['Decisions logged', data.decisions_logged],
      ]
    : []
  return (
    <div className="card p-4">
      <div className="mb-3 flex items-center gap-2 text-sm font-bold">
        <span className={`h-2 w-2 rounded-full ${data ? 'bg-ok animate-pulse' : 'bg-muted'}`} aria-hidden />
        {data ? 'Gateway Ready' : 'Connecting…'}
      </div>
      <dl className="flex flex-col gap-2 text-[0.82rem]">
        {rows.map(([k, v]) => (
          <div key={k} className="flex justify-between gap-2">
            <dt className="text-muted">{k}</dt>
            <dd className="font-bold">{v}</dd>
          </div>
        ))}
      </dl>
      {data && <div className="mt-3 border-t border-line pt-2 text-xs text-muted">v{data.version}</div>}
    </div>
  )
}

export default function Layout() {
  const [open, setOpen] = useState(false)
  const location = useLocation()
  const drawerRef = useRef<HTMLDivElement>(null)
  const menuButtonRef = useRef<HTMLButtonElement>(null)
  const current = ALL_ITEMS.find((i) => (i.to === '/' ? location.pathname === '/' : location.pathname.startsWith(i.to)))

  // nav links close the drawer themselves; Escape closes it; focus moves in and back out
  useEffect(() => {
    if (!open) return
    const menuButton = menuButtonRef.current
    drawerRef.current?.querySelector<HTMLElement>('a, button')?.focus()
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && setOpen(false)
    document.addEventListener('keydown', onKey)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKey)
      document.body.style.overflow = ''
      menuButton?.focus()
    }
  }, [open])

  return (
    <div className="min-h-dvh lg:pl-[280px]">
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-3 focus:py-2">
        Skip to main content
      </a>

      {/* desktop sidebar */}
      <aside className="fixed inset-y-0 left-0 hidden w-[280px] flex-col gap-6 overflow-y-auto border-r border-line bg-side/95 px-5 py-6 lg:flex">
        <Brand />
        <div className="h-px bg-line" />
        <NavList />
        <div className="mt-auto">
          <StatusCard />
        </div>
      </aside>

      {/* mobile / tablet top bar */}
      <header className="sticky top-0 z-30 flex h-14 items-center justify-between border-b border-line bg-bg/85 px-4 backdrop-blur-md lg:hidden">
        <Brand />
        <div className="flex items-center gap-2">
          {current && (
            <span className="hidden rounded-full border border-line2 bg-accent/15 px-3 py-1 text-xs font-semibold text-[#E9D5FF] sm:inline">
              {current.label}
            </span>
          )}
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
        className={`fixed inset-0 z-40 bg-black/60 backdrop-blur-sm transition-opacity lg:hidden ${open ? 'opacity-100' : 'pointer-events-none opacity-0'}`}
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
        className={`fixed inset-y-0 left-0 z-50 flex w-[min(300px,86vw)] flex-col gap-6 overflow-y-auto border-r border-line2 bg-side px-5 py-5 transition-transform duration-300 ease-out-soft lg:hidden ${
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
        <NavList onNavigate={() => setOpen(false)} />
        <div className="mt-auto">
          <StatusCard />
        </div>
      </div>

      <main id="main" className="mx-auto w-full max-w-[1480px] px-4 py-5 sm:px-6 lg:px-9 lg:py-7">
        <Outlet />
      </main>
    </div>
  )
}
