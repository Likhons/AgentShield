import { useId } from 'react'

/** The AgentShield mark: a shield split down the middle into a gate, with the agent's action (the lime dot)
 *  held in it for checking. The halves take the text colour (off-white by night, near-black by day); a masked
 *  ring separates the dot from the halves on any background. */
export function LogoMark({ size = 32, className = '' }: { size?: number; className?: string }) {
  const id = useId().replace(/:/g, '')
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" className={`logo-mark shrink-0 ${className}`} aria-hidden>
      <defs>
        <mask id={`m-${id}`}>
          <rect width="32" height="32" fill="#fff" />
          <circle cx="16" cy="15.2" r="4.9" fill="#000" />
        </mask>
        <linearGradient id={`s-${id}`} x1="0" y1="0" x2="0" y2="1">
          <stop offset="0" stopColor="currentColor" stopOpacity="1" />
          <stop offset="1" stopColor="currentColor" stopOpacity="0.78" />
        </linearGradient>
      </defs>
      <g mask={`url(#m-${id})`} fill={`url(#s-${id})`}>
        {/* left and right halves of the shield, with a 2.6-unit gate between them */}
        <path d="M14.7 2.6 L4.6 6.4 V14.6 C4.6 21.6 8.9 26.6 14.7 29.3 Z" />
        <path d="M17.3 2.6 L27.4 6.4 V14.6 C27.4 21.6 23.1 26.6 17.3 29.3 Z" />
      </g>
      <circle cx="16" cy="15.2" r="3.3" className="logo-dot" />
    </svg>
  )
}

/** Mark + wordmark. `sub` is the small line under the name. */
export default function Logo({ sub, size = 32 }: { sub?: string; size?: number }) {
  return (
    <span className="flex items-center gap-2.5">
      <LogoMark size={size} className="text-ink" />
      <span className="leading-none">
        <span className="block font-display text-[1.12rem] font-extrabold tracking-[-0.035em] text-ink">
          Agent<span className="text-soft">Shield</span>
        </span>
        {sub && <span className="mt-1 block text-[0.72rem] font-medium whitespace-nowrap text-muted">{sub}</span>}
      </span>
    </span>
  )
}
