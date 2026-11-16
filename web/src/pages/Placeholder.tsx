import type { LucideIcon } from 'lucide-react'
import { Card, PageHeader } from '../components/ui'

/** Temporary page body until the real page is ported from the Streamlit dashboard. */
export default function Placeholder({ icon, title, sub }: { icon: LucideIcon; title: string; sub: string }) {
  return (
    <>
      <PageHeader icon={icon} title={title} sub={sub} />
      <Card>
        <p className="text-sm text-muted">
          This page is being moved from the Streamlit dashboard. Until then, the live Streamlit demo shows it.
        </p>
      </Card>
    </>
  )
}
