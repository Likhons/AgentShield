import { X } from 'lucide-react'
import { useEffect, useRef, type ReactNode } from 'react'
import { createPortal } from 'react-dom'
import { lockScroll, unlockScroll } from '../lib/motion'

/** Accessible dialog: Escape and backdrop close it, focus moves in and back, background does not scroll.
 *  Full screen on phones, a centred panel from the sm breakpoint up. */
export default function Modal({ title, onClose, children, wide = false, footer }: { title: ReactNode; onClose: () => void; children: ReactNode; wide?: boolean; footer?: ReactNode }) {
  const panel = useRef<HTMLDivElement>(null)
  const close = useRef(onClose)
  useEffect(() => {
    close.current = onClose
  }, [onClose])

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    panel.current?.focus({ preventScroll: true })
    const onKey = (e: KeyboardEvent) => e.key === 'Escape' && close.current()
    document.addEventListener('keydown', onKey)
    lockScroll()
    return () => {
      document.removeEventListener('keydown', onKey)
      unlockScroll()
      previous?.focus({ preventScroll: true })
    }
  }, [])

  // rendered into <body> so no transformed ancestor can turn 'fixed' into 'scrolls with the page'
  return createPortal(
    <div className="fade-in fixed inset-0 z-50 flex items-stretch justify-center bg-black/65 backdrop-blur-sm sm:items-center sm:p-6" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        tabIndex={-1}
        className={`card modal-in flex w-full flex-col rounded-none outline-none sm:max-h-[86dvh] sm:rounded-card ${wide ? 'sm:max-w-5xl' : 'sm:max-w-2xl'}`}
      >
        <div className="flex items-center justify-between gap-3 border-b border-line px-4 py-3 sm:px-5">
          <h2 className="min-w-0 text-base font-bold break-words">{title}</h2>
          <button type="button" onClick={onClose} aria-label="Close" className="inline-flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-line hover:border-line2">
            <X size={17} aria-hidden />
          </button>
        </div>
        <div data-lenis-prevent className="min-h-0 flex-1 overflow-y-auto px-4 py-4 sm:px-5">{children}</div>
        {/* always visible under the scrolling body */}
        {footer && <div className="border-t border-line px-4 py-3 sm:px-5">{footer}</div>}
      </div>
    </div>,
    document.body,
  )
}
