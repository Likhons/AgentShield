import type { Thresholds } from './api'

/** Same bands as the engine's DecisionThresholds: ask at 0.4, block at 0.75 (values come from the API). */
export function riskLevel(score: number, t: Thresholds): { label: 'Low' | 'Medium' | 'High'; cls: string; text: string } {
  if (score >= t.block_at) return { label: 'High', cls: 'text-bad-ink border-bad/40 bg-bad/12', text: 'text-bad-ink' }
  if (score >= t.ask_human_at) return { label: 'Medium', cls: 'text-warn border-warn/40 bg-warn/12', text: 'text-warn' }
  return { label: 'Low', cls: 'text-ok border-ok/35 bg-ok/10', text: 'text-ok' }
}

export const utcFull = (iso: string) =>
  new Date(iso).toLocaleString('en-US', {
    month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false, timeZone: 'UTC',
  })
