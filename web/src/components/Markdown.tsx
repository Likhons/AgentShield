import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

/** Renders the repo's own Markdown docs (results.md, datasets/README.md). No raw HTML is allowed. */
export default function Markdown({ text }: { text: string }) {
  return (
    <div className="md text-[0.92rem] leading-relaxed text-[#D6E0D9]">
      <ReactMarkdown remarkPlugins={[remarkGfm]}>{text}</ReactMarkdown>
    </div>
  )
}
