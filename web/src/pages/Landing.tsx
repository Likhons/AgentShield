import { ChartColumn, PlayCircle } from 'lucide-react'
import { lazy, Suspense, useEffect, useRef, useState, type RefObject } from 'react'
import { Link } from 'react-router-dom'
import About from '../components/landing/About'
import DevTerminal from '../components/landing/DevTerminal'
import Marquee from '../components/landing/Marquee'
import Logo from '../components/Logo'
import ThemeToggle from '../components/ThemeToggle'
import HeroSimulation from '../components/landing/HeroSimulation'
import Pipeline from '../components/landing/Pipeline'
import { CountUp, Reveal } from '../components/Motion'
import { reducedMotion, useInView } from '../lib/motion'

const SandboxModal = lazy(() => import('../components/landing/SandboxModal'))

// Everything shown here is real: the transcript and the four check results are the recorded run
// demo_agent/recordings/groq/attack_bill_bn_with.json (qwen/qwen3.8-27b via Groq, 13 Nov 2026);
// the numbers come from benchmark run agent_20261112-111137.

/** Writes how far the element has scrolled out of view (0..1) into the CSS variable --p. No re-renders. */
function useScrollProgress<T extends HTMLElement>(ref: RefObject<T | null>) {
  useEffect(() => {
    const el = ref.current
    if (!el || reducedMotion()) return
    let frame = 0
    const update = () => {
      frame = 0
      const r = el.getBoundingClientRect()
      el.style.setProperty('--p', String(Math.min(1, Math.max(0, -r.top / r.height))))
    }
    const onScroll = () => { if (!frame) frame = requestAnimationFrame(update) }
    update()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => { window.removeEventListener('scroll', onScroll); cancelAnimationFrame(frame) }
  }, [ref])
}

// ---------------------------------------------------------------------------
// hero

const HEADLINE = ['Your AI agent can', 'pay a bill that was', 'never real.']
const HEADLINE_WORDS = HEADLINE.map((line, i) => ({
  line,
  words: line.split(' ').map((word, j) => ({ word, index: HEADLINE.slice(0, i).join(' ').split(' ').filter(Boolean).length + j })),
}))

function Headline() {
  return (
    <>
      <span className="word-rise inline-flex items-center gap-2.5 rounded-full border border-line2 bg-accent/[0.05] px-4 py-1.5 font-mono text-[0.74rem] tracking-[0.16em] text-body uppercase">
        <span className="h-2 w-2 rounded-full bg-mark shadow-[0_0_10px_var(--color-mark)]" aria-hidden /> Runtime action firewall
      </span>
      <h1 className="mt-6 text-[clamp(2.75rem,5.6vw,4.6rem)] leading-[0.98] font-semibold tracking-[-0.045em]" aria-label={HEADLINE.join(' ')}>
        {HEADLINE_WORDS.map(({ line, words }, i) =>
          i === HEADLINE.length - 1 ? (
            // the last line rises as one piece, so its gradient runs across both words
            <span key={line} className="hero-line block" style={{ ['--dir' as string]: '-1' }} aria-hidden>
              <span className="hero-gradient accent-serif word-rise inline-block pr-[0.08em] pb-[0.1em]" style={{ animationDelay: `${0.08 + 0.06 * words[0].index}s` }}>
                {line}
              </span>
            </span>
          ) : (
            <span key={line} className="hero-line block" style={{ ['--dir' as string]: i % 2 ? '1' : '-1' }} aria-hidden>
              {words.map(({ word, index }) => (
                <span key={index} className="word-rise inline-block" style={{ animationDelay: `${0.08 + 0.06 * index}s` }}>
                  {word}&nbsp;
                </span>
              ))}
            </span>
          ),
        )}
      </h1>
    </>
  )
}

function Hero({ onRunAttack }: { onRunAttack: () => void }) {
  const ref = useRef<HTMLElement>(null)
  const card = useRef<HTMLDivElement>(null)
  const [runKey, setRunKey] = useState(0)
  useScrollProgress(ref)

  // the card's own replay button restarts the recorded run; the hero CTA lets the visitor run the attack
  // themselves in the sandbox (the fake Bangla bill is preloaded there)
  const replay = () => setRunKey((k) => k + 1)
  const runAttack = onRunAttack

  return (
    <section ref={ref} className="relative overflow-x-clip">
      <div className="landing-grid pointer-events-none absolute inset-0" aria-hidden />
      <div className="glow glow-lime -top-40 left-[-10%] h-[560px] w-[560px]" aria-hidden />
      <div className="glow glow-emerald top-10 right-[-8%] h-[620px] w-[620px]" aria-hidden />
      <div className="relative mx-auto grid max-w-6xl items-center gap-10 px-4 pt-28 pb-16 sm:px-6 lg:grid-cols-[1.05fr_1fr] lg:pt-36 lg:pb-24">
        <div>
          <Headline />
          <div className="landing-step" style={{ animationDelay: '0.45s' }}>
            <p className="mt-6 max-w-[54ch] text-[1.08rem] leading-[1.65] text-body sm:text-[1.18rem]">
              AgentShield checks every action an AI agent is about to take, such as sending money, and stops the ones the
              user never asked for. It catches tricks hidden in emails, web pages and files, in Bangla, Banglish and English.
            </p>
            <p lang="bn" className="bn-callout mt-6 w-fit max-w-full text-[1.08rem] text-balance sm:text-[1.15rem]">
              এআই এজেন্ট টাকা পাঠানোর আগে AgentShield প্রতিটি কাজ যাচাই করে।
            </p>
            <div className="mt-8 flex flex-col gap-3 sm:flex-row">
              <button type="button" onClick={runAttack} className="btn-primary lift inline-flex min-h-12 items-center justify-center gap-2 rounded-xl px-6 font-bold">
                <PlayCircle size={18} aria-hidden /> Run the attack yourself
              </button>
              <Link to="/benchmarks" className="lift inline-flex min-h-12 items-center justify-center gap-2 rounded-xl border border-fg/12 bg-fg/[0.02] px-6 font-bold hover:border-line2 hover:bg-accent/[0.06]">
                <ChartColumn size={18} aria-hidden /> See the measurements
              </Link>
            </div>
          </div>
        </div>
        <div ref={card} className="hero-card">
          <HeroSimulation key={runKey} runKey={runKey} onReplay={replay} />
        </div>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// how it works: the blocked payment stays in view while the four checks resolve one by one

function HowItWorks() {
  return (
    <section id="how" className="relative scroll-mt-20 border-t border-fg/6">
      <div className="mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:py-24">
        <Reveal>
          <h2 className="max-w-[22ch] text-[clamp(2rem,4.6vw,3.4rem)] leading-[1.04] font-semibold tracking-[-0.04em]">
            Four checks run before every action, <em className="accent-serif text-soft">in about a millisecond.</em>
          </h2>
          <p className="mt-5 max-w-[62ch] text-[1.05rem] leading-relaxed text-body sm:text-[1.1rem]">
            Follow the fake bill’s payment through them. The stricter of the score and the rules decides: allow, ask the
            user, or block. Every decision is explained in Bangla and English and kept in an audit log.
          </p>
        </Reveal>
        <Pipeline />
        <Reveal>
          <p className="mt-12 max-w-[62ch] text-[0.95rem] text-body">
            The text filter alone would have paid the attacker. AI judges where judgment is needed; fixed rules decide
            where certainty is needed.
          </p>
        </Reveal>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// results

function Bar({ label, value, total, tone, shown }: { label: string; value: number; total: number; tone: 'bad' | 'ok' | 'muted'; shown: boolean }) {
  const color = { bad: 'bg-bad', ok: 'bg-ok', muted: 'bg-muted/45' }[tone]
  const text = { bad: 'text-bad-ink', ok: 'text-ok-ink', muted: 'text-ink' }[tone]
  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <span className="text-sm text-muted">{label}</span>
        <span className={`font-mono text-[1.6rem] leading-none font-bold tabular-nums ${text}`}>
          <CountUp to={value} run={shown} /><span className="text-base text-muted">/{total}</span>
        </span>
      </div>
      <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-fg/[0.06]" role="img" aria-label={`${label}: ${value} of ${total}`}>
        <div className={`fill-bar h-full rounded-full ${color}`} style={{ transform: `scaleX(${shown ? Math.max(0.015, value / total) : 0})` }} />
      </div>
    </div>
  )
}

// From the recorded run attack_bill_bn_with.json (13 Nov 2026, n=1): the blocked call's taint 0.31 ms +
// classifier 0.36 ms + policy 0.16 ms; its intent judge 797.5 ms; the judge was skipped on 3 of 5 calls.
const PILLS = [
  { value: '0.8 ms', label: 'rule checks on the blocked call' },
  { value: '0.8 s', label: 'intent judge (gpt-oss-120b), only when needed' },
  { value: '2 of 5', label: 'tool calls needed the judge' },
]

function Results() {
  const [barsRef, barsShown] = useInView<HTMLDivElement>(0.3)
  return (
    <section id="results" className="relative scroll-mt-20 border-t border-fg/6">
      <div className="glow glow-emerald top-1/4 -left-40 h-[520px] w-[520px] opacity-70" aria-hidden />
      <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:py-24">
        <div className="grid gap-10 lg:grid-cols-[1fr_1.25fr] lg:items-center">
          <Reveal>
            <h2 className="text-[clamp(2rem,4.6vw,3.4rem)] leading-[1.04] font-semibold tracking-[-0.04em]">
              Attacks stopped. <em className="accent-serif text-soft">Real bills still paid.</em>
            </h2>
            <p className="mt-5 max-w-[54ch] text-[1.05rem] leading-relaxed text-body sm:text-[1.1rem]">
              A real model (qwen3.8-27b via Groq) worked through 20 Bangla and Banglish attacks and 20 normal bill payments,
              once without and once with AgentShield. Small samples: the benchmark page shows the confidence intervals.
            </p>
            <Link to="/benchmarks" className="lift mt-5 inline-flex min-h-11 items-center gap-2 rounded-xl border border-fg/12 px-5 text-sm font-bold hover:border-line2 hover:bg-accent/[0.06]">
              <ChartColumn size={16} aria-hidden /> Open the benchmarks
            </Link>
          </Reveal>
          <div ref={barsRef} className="grid gap-4 sm:grid-cols-2">
            <div className="glass spotlight lift p-5">
              <h3 className="relative mb-4 font-bold">Attacks that moved money</h3>
              <div className="relative flex flex-col gap-4">
                <Bar label="Without" value={4} total={20} tone="bad" shown={barsShown} />
                <Bar label="With AgentShield" value={0} total={20} tone="ok" shown={barsShown} />
              </div>
            </div>
            <div className="glass spotlight lift p-5">
              <h3 className="relative mb-4 font-bold">Rent paid on time</h3>
              <div className="relative flex flex-col gap-4">
                <Bar label="Without" value={16} total={20} tone="muted" shown={barsShown} />
                <Bar label="With AgentShield" value={16} total={20} tone="ok" shown={barsShown} />
              </div>
              <p className="relative mt-4 text-[0.82rem] text-muted">The four unpaid rents were unpaid without AgentShield too.</p>
            </div>
          </div>
        </div>
        <Reveal className="mt-8">
          <ul className="flex flex-wrap gap-2.5">
            {PILLS.map((p) => (
              <li key={p.label} className="glass spotlight inline-flex min-h-10 items-center gap-2.5 rounded-full! px-4 py-1.5 text-sm">
                <span className="relative shrink-0 font-mono font-bold whitespace-nowrap tabular-nums text-soft">{p.value}</span>
                <span className="relative text-muted">{p.label}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2.5 text-xs text-muted">Latency from the recorded run on 13 Nov 2026 (one run, n=1).</p>
        </Reveal>
      </div>
    </section>
  )
}

// ---------------------------------------------------------------------------
// page

export default function Landing() {
  const [demoOpen, setDemoOpen] = useState(false)

  return (
    <div className="relative min-h-dvh overflow-x-clip">
      <div className="cyber-grid" aria-hidden />
      <a href="#main" className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-50 focus:rounded-lg focus:bg-accent focus:px-3 focus:py-2">
        Skip to main content
      </a>
      <header data-scroll-header className="fixed inset-x-0 top-3 z-30 px-3 sm:px-6">
        <nav aria-label="Main" className="glass glass-blur mx-auto flex h-14 max-w-6xl items-center justify-between gap-4 rounded-2xl! px-3 sm:px-4">
          <Link to="/" aria-label="AgentShield home" className="flex min-h-11 items-center">
            <Logo size={30} />
          </Link>
          <div className="hidden items-center gap-4 text-[0.88rem] whitespace-nowrap md:flex lg:gap-7 lg:text-[0.95rem]">
            <a href="#how" className="inline-flex min-h-11 items-center font-semibold text-muted transition-colors duration-300 hover:text-ink">How it works</a>
            <a href="#results" className="inline-flex min-h-11 items-center font-semibold text-muted transition-colors duration-300 hover:text-ink">Results</a>
            <a href="#builders" className="inline-flex min-h-11 items-center font-semibold text-muted transition-colors duration-300 hover:text-ink">For developers</a>
            <a href="#about" className="inline-flex min-h-11 items-center font-semibold text-muted transition-colors duration-300 hover:text-ink">About</a>
          </div>
          <div className="flex items-center gap-2.5">
            <ThemeToggle />
            <button type="button" onClick={() => setDemoOpen(true)} className="btn-primary lift inline-flex min-h-10 items-center gap-2 rounded-xl px-3.5 text-sm font-bold whitespace-nowrap sm:px-4">
              <PlayCircle size={16} aria-hidden /> <span className="hidden lg:inline">Open the demo</span><span className="lg:hidden">Demo</span>
            </button>
          </div>
        </nav>
      </header>

      <main id="main" className="relative">
        <Hero onRunAttack={() => setDemoOpen(true)} />
        <Marquee />
        <HowItWorks />
        <Results />
        <section id="builders" className="relative scroll-mt-20 border-t border-fg/6">
          <div className="glow glow-lime right-[-12%] bottom-0 h-[520px] w-[520px] opacity-80" aria-hidden />
          <div className="relative mx-auto grid max-w-6xl gap-10 px-4 py-16 sm:px-6 lg:grid-cols-[1fr_1.4fr] lg:items-center lg:py-24">
            <Reveal>
              <h2 className="text-[clamp(2rem,4.6vw,3.4rem)] leading-[1.04] font-semibold tracking-[-0.04em]">
                One call <em className="accent-serif text-soft">before</em> each tool runs.
              </h2>
              <p className="mt-5 max-w-[50ch] text-[1.05rem] leading-relaxed text-body sm:text-[1.1rem]">
                Use the Python SDK, which wraps your agent’s tools, or call the HTTP gateway from any language or agent
                framework. The answer comes with a risk score and a reason the user can read.
              </p>
            </Reveal>
            <Reveal delay={0.1}>
              <DevTerminal />
            </Reveal>
          </div>
        </section>
        <About />
      </main>

      <footer className="footer-dots relative border-t border-fg/6">
        <div className="relative mx-auto flex max-w-6xl flex-col gap-4 px-4 py-14 text-sm text-muted sm:flex-row sm:items-center sm:justify-between sm:px-6">
          <p>Built for the International AI Builders Congress 2026. Demo data is fake: numbers start with 010, domains end in .example.</p>
          <div className="flex gap-5">
            <Link to="/playground" className="inline-flex min-h-11 min-w-11 items-center transition-colors hover:text-soft">Demo</Link>
            <Link to="/benchmarks" className="inline-flex min-h-11 items-center transition-colors hover:text-soft">Benchmarks</Link>
            <Link to="/policies" className="inline-flex min-h-11 items-center transition-colors hover:text-soft">Policies</Link>
          </div>
        </div>
      </footer>

      {demoOpen && (
        <Suspense fallback={null}>
          <SandboxModal onClose={() => setDemoOpen(false)} />
        </Suspense>
      )}
    </div>
  )
}
