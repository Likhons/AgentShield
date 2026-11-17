import { setTheme, useTheme } from '../lib/theme'

/** Day / night switch: the knob slides across a sky (stars at night, a soft haze by day) and turns from a
 *  crescent moon into the sun. The page then changes as a circle spreading from the knob. */
export default function ThemeToggle({ className = '' }: { className?: string }) {
  const theme = useTheme()
  const day = theme === 'light'
  return (
    <button
      type="button"
      role="switch"
      aria-checked={day}
      aria-label={day ? 'Day mode on. Switch to night mode' : 'Night mode on. Switch to day mode'}
      title={day ? 'Switch to night' : 'Switch to day'}
      onClick={(e) => {
        const r = e.currentTarget.getBoundingClientRect()
        const knobX = day ? r.left + r.height / 2 : r.right - r.height / 2 // where the knob is going
        setTheme(day ? 'dark' : 'light', { x: knobX, y: r.top + r.height / 2 })
      }}
      className={`theme-toggle ${day ? 'is-day' : ''} ${className}`}
    >
      <span className="tt-sky" aria-hidden>
        <span className="tt-star" style={{ left: '58%', top: '28%' }} />
        <span className="tt-star" style={{ left: '74%', top: '58%', animationDelay: '0.6s' }} />
        <span className="tt-star" style={{ left: '86%', top: '26%', animationDelay: '1.2s' }} />
        <span className="tt-haze" />
      </span>
      <span className="tt-knob" aria-hidden>
        <span className="tt-rays" />
        <span className="tt-core" />
        <span className="tt-bite" />
      </span>
    </button>
  )
}
