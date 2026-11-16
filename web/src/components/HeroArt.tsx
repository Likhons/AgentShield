import { CircleAlert, EyeOff, Globe, Layers, Scale, Zap, type LucideIcon } from 'lucide-react'

const FEATURES: { label: string; icon: LucideIcon; pos: string }[] = [
  { label: 'Prompt Injection', icon: Zap, pos: 'lg:left-[1%] lg:top-[5%]' },
  { label: 'Data Tainting', icon: Layers, pos: 'lg:left-0 lg:top-[39%]' },
  { label: 'Multilingual (BN / Banglish / EN)', icon: Globe, pos: 'lg:left-0 lg:top-[73%]' },
  { label: 'Instruction Hiding', icon: EyeOff, pos: 'lg:right-[1%] lg:top-[5%]' },
  { label: 'Unsafe Action', icon: CircleAlert, pos: 'lg:right-0 lg:top-[39%]' },
  { label: 'Policy Enforcement', icon: Scale, pos: 'lg:right-0 lg:top-[73%]' },
]

/** Shield with orbit and six feature chips. Wide screens: chips around the shield, joined by traces.
 *  Narrow screens: a smaller shield with the chips wrapped underneath. */
export default function HeroArt() {
  return (
    <div className="relative flex flex-wrap items-center justify-center gap-2 lg:block lg:h-[265px]">
      <svg
        className="shield-art h-[148px] w-[220px] flex-[0_0_100%] lg:absolute lg:inset-0 lg:h-full lg:w-full"
        viewBox="0 0 580 265"
        role="img"
        aria-label="AgentShield shield"
      >
        <defs>
          <linearGradient id="sg" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#D47AFF" />
            <stop offset="50%" stopColor="#8A3FFC" />
            <stop offset="100%" stopColor="#491D8B" />
          </linearGradient>
          <linearGradient id="sg2" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#2E1B6E" />
            <stop offset="100%" stopColor="#120B36" />
          </linearGradient>
          <linearGradient id="traceL" x1="0" y1="0" x2="1" y2="0">
            <stop offset="0%" stopColor="#8B5CFF" stopOpacity=".18" />
            <stop offset="100%" stopColor="#C98BFF" stopOpacity=".75" />
          </linearGradient>
          <linearGradient id="traceR" x1="1" y1="0" x2="0" y2="0">
            <stop offset="0%" stopColor="#8B5CFF" stopOpacity=".18" />
            <stop offset="100%" stopColor="#C98BFF" stopOpacity=".75" />
          </linearGradient>
          <radialGradient id="glow" cx="50%" cy="46%" r="48%">
            <stop offset="0%" stopColor="#9333EA" stopOpacity=".55" />
            <stop offset="60%" stopColor="#6D28D9" stopOpacity=".18" />
            <stop offset="100%" stopColor="#6D28D9" stopOpacity="0" />
          </radialGradient>
          <radialGradient id="padglow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="#C084FC" stopOpacity=".65" />
            <stop offset="55%" stopColor="#7C3AED" stopOpacity=".28" />
            <stop offset="100%" stopColor="#7C3AED" stopOpacity="0" />
          </radialGradient>
        </defs>
        <ellipse className="aura" cx="290" cy="122" rx="185" ry="118" fill="url(#glow)" />
        <g className="hidden lg:inline" fill="none" strokeWidth="1.5">
          <path d="M 155 34 C 195 34, 205 74, 232 82" stroke="url(#traceL)" />
          <path d="M 145 122 L 222 122" stroke="url(#traceL)" />
          <path d="M 185 212 C 212 212, 218 164, 240 154" stroke="url(#traceL)" />
          <path d="M 425 34 C 385 34, 375 74, 348 82" stroke="url(#traceR)" />
          <path d="M 435 122 L 358 122" stroke="url(#traceR)" />
          <path d="M 395 212 C 368 212, 362 164, 340 154" stroke="url(#traceR)" />
          {[[232, 82], [222, 122], [240, 154], [348, 82], [358, 122], [340, 154]].map(([x, y]) => (
            <circle key={`${x}-${y}`} cx={x} cy={y} r="3" fill="#E9D5FF" />
          ))}
        </g>
        <ellipse className="pad-glow" cx="290" cy="212" rx="96" ry="22" fill="url(#padglow)" />
        <ellipse cx="290" cy="212" rx="86" ry="16" fill="none" stroke="#A855F7" strokeOpacity=".65" strokeWidth="1.8" />
        <ellipse cx="290" cy="212" rx="60" ry="10" fill="none" stroke="#E9D5FF" strokeOpacity=".75" strokeWidth="1.5" />
        <ellipse cx="290" cy="124" rx="108" ry="30" fill="none" stroke="#B44CFF" strokeOpacity=".28" strokeWidth="1.2" />
        <ellipse className="orbit" cx="290" cy="124" rx="108" ry="30" fill="none" stroke="#F3E8FF" strokeWidth="2"
          strokeLinecap="round" pathLength={1000} strokeDasharray="70 930" />
        <g className="shield-body">
          <path d="M290 30 L352 54 C352 118 330 160 290 185 C250 160 228 118 228 54 Z" fill="url(#sg)" stroke="#F3E8FF"
            strokeOpacity=".85" strokeWidth="2.2" />
          <path d="M290 46 L337 64 C337 115 320 148 290 167 C260 148 243 115 243 64 Z" fill="url(#sg2)" stroke="#C084FC"
            strokeOpacity=".65" strokeWidth="1.5" />
          <path d="M267 108 L283 124 L316 90" fill="none" stroke="#FFFFFF" strokeWidth="9.5" strokeLinecap="round"
            strokeLinejoin="round" />
        </g>
      </svg>
      {FEATURES.map(({ label, icon: Icon, pos }) => (
        <span
          key={label}
          className={`inline-flex min-h-9 items-center gap-1.5 rounded-full border border-line2 bg-[#1A1440]/90 py-1 pr-3 pl-1.5 text-[0.74rem] font-semibold text-[#E9D5FF] backdrop-blur lg:absolute lg:text-[0.8rem] ${pos}`}
        >
          <span className="inline-flex h-6 w-6 items-center justify-center rounded-full bg-accent/25">
            <Icon size={13} aria-hidden />
          </span>
          {label}
        </span>
      ))}
    </div>
  )
}
