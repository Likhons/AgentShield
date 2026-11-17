import { Fragment } from 'react'

// What AgentShield is, as a slow ticker under the hero. Only facts that the rest of the page backs up.
const ITEMS: { text: string; bn?: boolean; hot?: boolean }[] = [
  { text: 'Checks every tool call before it runs' },
  { text: 'Taint tracking' },
  { text: 'Multilingual injection classifier' },
  { text: 'বাংলা · Banglish · English', bn: true },
  { text: 'Intent judge only when needed' },
  { text: 'Readable YAML policies' },
  { text: 'টাকা পাঠানোর আগে যাচাই', bn: true },
  { text: 'Reasons in Bangla and English' },
  { text: 'Audit log for every decision' },
  { text: 'Python SDK · HTTP gateway' },
  { text: '0/20 attacks moved money with AgentShield (real model)', hot: true },
]

function Row({ hidden = false }: { hidden?: boolean }) {
  return (
    <ul className="marquee-row" aria-hidden={hidden || undefined}>
      {ITEMS.map((item) => (
        <Fragment key={item.text}>
          <li lang={item.bn ? 'bn' : undefined} className={`marquee-item ${item.hot ? 'text-soft' : ''}`}>{item.text}</li>
          <li className="marquee-sep" aria-hidden>
            ◆
          </li>
        </Fragment>
      ))}
    </ul>
  )
}

/** Seamless ticker: the row is drawn twice and the track slides by exactly one row (-50%), so the loop has
 *  no seam. Edges fade out with a mask. Pauses under a mouse; stands still (wrapped) with reduced motion. */
export default function Marquee() {
  return (
    <section aria-label="What AgentShield does" className="marquee relative border-y border-fg/6 py-4">
      <div className="marquee-track">
        <Row />
        <Row hidden />
      </div>
    </section>
  )
}
