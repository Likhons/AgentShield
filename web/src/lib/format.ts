export const taka = (amount: number) => `৳ ${amount.toLocaleString('en-US')}`

/** 'bn' -> 'BN', 'banglish' -> 'Banglish', 'all' -> 'All' (same as the Streamlit dashboard). */
export const langLabel = (code: string) => (code.length <= 2 ? code.toUpperCase() : code[0].toUpperCase() + code.slice(1))

/** Cut at a word boundary and mark the cut. */
export function short(text: string, limit: number): string {
  if (text.length <= limit) return text
  const cut = text.slice(0, limit)
  const space = cut.lastIndexOf(' ')
  return (space > 0 ? cut.slice(0, space) : cut).replace(/[.,;:]+$/, '') + '…'
}

export function utcTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('en-US', { month: 'short', day: '2-digit', hour: '2-digit', minute: '2-digit', hour12: false, timeZone: 'UTC' })
}
