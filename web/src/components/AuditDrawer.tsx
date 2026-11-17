import { useEffect, useRef } from 'react'
import { createPortal } from 'react-dom'
import type { AuditRecord, Thresholds } from '../lib/api'
import { lockScroll, unlockScroll } from '../lib/motion'
import AuditDetail from './AuditDetail'

/** Right-side slide-over with one audit record. Escape and the backdrop close it; focus moves in and back. */
export default function AuditDrawer({ record, thresholds, onClose }: { record: AuditRecord; thresholds: Thresholds; onClose: () => void }) {
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

  return createPortal(
    <div className="fade-in fixed inset-0 z-50 flex justify-end bg-black/55 backdrop-blur-[2px]" onMouseDown={(e) => e.target === e.currentTarget && onClose()}>
      <div
        ref={panel}
        role="dialog"
        aria-modal="true"
        aria-label="Audit details"
        tabIndex={-1}
        data-lenis-prevent
        className="drawer-in glass h-full w-full max-w-[520px] overflow-y-auto rounded-none! border-y-0! border-r-0! px-4 py-4 outline-none sm:px-5"
      >
        <AuditDetail record={record} thresholds={thresholds} onClose={onClose} />
      </div>
    </div>,
    document.body,
  )
}
