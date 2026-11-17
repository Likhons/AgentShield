import { ArrowRight, Building2, Landmark, Languages, MessageSquareText, Plug, ScanSearch, Smartphone, Wrench, type LucideIcon } from 'lucide-react'
import { Link } from 'react-router-dom'
import { Reveal } from '../Motion'

// What AgentShield is, for a first-time visitor. Wording follows docs/pitch.md and docs/business_model.md;
// it makes no claim that is not measured on the benchmark page.

const POINTS: { icon: LucideIcon; title: string; body: string }[] = [
  {
    icon: ScanSearch,
    title: 'Checks the action, not only the text',
    body: 'A fake bill that never talks to the AI slips past text filters. AgentShield looks at the tool call itself: where the number and the amount came from, and whether the user asked for it.',
  },
  {
    icon: Languages,
    title: 'Bangla, Banglish and English',
    body: 'Tested on Bangla and Banglish attacks, public English agent attacks and normal look-alike messages, with false alarms reported per language.',
  },
  {
    icon: MessageSquareText,
    title: 'Explains every decision',
    body: 'Allow, ask the user, or block, each with a reason in Bangla and English, and every decision kept in an audit log.',
  },
  {
    icon: Plug,
    title: 'Fits any agent',
    body: 'A Python SDK that wraps the agent’s tools, or an HTTP gateway for any language or agent framework.',
  },
]

const FOR: { icon: LucideIcon; who: string; why: string }[] = [
  { icon: Smartphone, who: 'Mobile wallets and MFS', why: 'AI assistants that can move money, with heavy Bangla and Banglish traffic' },
  { icon: Landmark, who: 'Banks and NBFIs', why: 'Human oversight and an audit trail for automated decisions, on their own servers' },
  { icon: Building2, who: 'Fintech and e-commerce', why: 'Shipping agents fast without a security team' },
  { icon: Wrench, who: 'Agent builders', why: 'A security layer to build in for their clients' },
]

export default function About() {
  return (
    <section id="about" className="relative scroll-mt-20 border-t border-fg/6">
      <div className="relative mx-auto max-w-6xl px-4 py-16 sm:px-6 lg:py-24">
        <div className="grid gap-10 lg:grid-cols-[1fr_1.15fr] lg:gap-14">
          <Reveal>
            <span className="font-mono text-[0.72rem] tracking-[0.2em] text-muted uppercase">About AgentShield</span>
            <h2 className="mt-3 text-[clamp(1.7rem,3.6vw,2.5rem)] leading-tight font-extrabold">
              A safety check between an AI agent and the money it can move.
            </h2>
            <p className="mt-4 max-w-[56ch] leading-relaxed text-body">
              Banks and wallets are starting to give AI agents real permissions: reading customer emails, browsing the
              web, opening files and calling payment tools. An agent cannot reliably tell its user’s instruction from
              text an attacker hid in the data it reads. In Bangladesh that text is often Bangla or Banglish, and most
              guardrails are built and tested for English.
            </p>
            <p lang="bn" className="bn-callout mt-5 w-fit max-w-full text-[1rem]">
              এআই এজেন্ট ইমেইল, ওয়েব পেজ বা ফাইলে লুকানো নির্দেশে টাকা পাঠিয়ে দিতে পারে। AgentShield প্রতিটি কাজ চলার
              আগে যাচাই করে, আর কেন আটকানো হলো তা বাংলা ও ইংরেজিতে জানায়।
            </p>
            <blockquote className="mt-6 border-l border-fg/15 pl-4 text-[1.02rem] font-semibold">
              “AI where judgment is needed, deterministic rules where certainty is needed.”
              <span className="mt-1 block text-xs font-normal text-muted">The design principle behind the four checks</span>
            </blockquote>
          </Reveal>

          <ul className="grid gap-3 sm:grid-cols-2">
            {POINTS.map(({ icon: Icon, title, body }, i) => (
              <li key={title}>
                <Reveal delay={i * 0.06} className="h-full">
                  <div className="glass spotlight lift h-full p-5">
                    <span className="relative inline-flex h-10 w-10 items-center justify-center rounded-xl border border-fg/10 bg-fg/[0.04] text-soft">
                      <Icon size={19} strokeWidth={1.8} aria-hidden />
                    </span>
                    <h3 className="relative mt-4 text-[1.02rem] font-bold">{title}</h3>
                    <p className="relative mt-1.5 text-[0.9rem] leading-relaxed text-muted">{body}</p>
                  </div>
                </Reveal>
              </li>
            ))}
          </ul>
        </div>

        <Reveal className="mt-14">
          <h3 className="font-mono text-[0.72rem] tracking-[0.2em] text-muted uppercase">Who it is for</h3>
          <ul className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {FOR.map(({ icon: Icon, who, why }) => (
              <li key={who} className="flex gap-3 rounded-2xl border border-fg/8 bg-fg/[0.02] p-4">
                <Icon size={18} strokeWidth={1.8} className="mt-0.5 shrink-0 text-soft" aria-hidden />
                <span>
                  <b className="block text-[0.95rem]">{who}</b>
                  <span className="mt-0.5 block text-[0.84rem] leading-relaxed text-muted">{why}</span>
                </span>
              </li>
            ))}
          </ul>
          <p className="mt-6 flex flex-wrap items-center gap-x-3 gap-y-2 text-[0.84rem] text-muted">
            <span>A research prototype built for the International AI Builders Congress 2026. Demo data is fake; every number on this site comes from a saved run.</span>
            <Link to="/benchmarks" className="inline-flex items-center gap-1 font-semibold text-soft hover:text-ink">
              See the measurements <ArrowRight size={14} aria-hidden />
            </Link>
          </p>
        </Reveal>
      </div>
    </section>
  )
}
