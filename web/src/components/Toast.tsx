import { CircleAlert, CircleCheck, Info } from 'lucide-react'
import { useCallback, useState, type ReactNode } from 'react'
import { ToastContext, type Tone } from '../lib/toast'

interface ToastItem { id: number; text: string; tone: Tone }

/** Short confirmations ("Copied", "Run finished") at the bottom of the screen; read out by screen readers. */
export function ToastProvider({ children }: { children: ReactNode }) {
  const [items, setItems] = useState<ToastItem[]>([])
  const toast = useCallback((text: string, tone: Tone = 'ok') => {
    const id = Date.now() + Math.random()
    setItems((all) => [...all.slice(-2), { id, text, tone }])
    setTimeout(() => setItems((all) => all.filter((t) => t.id !== id)), 2800)
  }, [])
  const icon = { ok: CircleCheck, info: Info, error: CircleAlert }
  const color = { ok: 'text-ok', info: 'text-[#C9A6FF]', error: 'text-[#FF6B78]' }
  return (
    <ToastContext.Provider value={toast}>
      {children}
      <div aria-live="polite" className="pointer-events-none fixed inset-x-0 bottom-4 z-[60] flex flex-col items-center gap-2 px-4">
        {items.map((t) => {
          const Icon = icon[t.tone]
          return (
            <div key={t.id} className="toast-in card flex max-w-md items-center gap-2.5 px-4 py-2.5 text-sm font-semibold shadow-[0_16px_40px_-12px_rgba(0,0,0,.8)]">
              <Icon size={17} className={color[t.tone]} aria-hidden />
              {t.text}
            </div>
          )
        })}
      </div>
    </ToastContext.Provider>
  )
}

