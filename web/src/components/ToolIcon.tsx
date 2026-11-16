import { CreditCard, FileText, Globe, Mail, Wallet, Wrench, type LucideProps } from 'lucide-react'

/** Icon for a demo tool name (send_money, read_email, web_search, read_file, get_balance, ...). */
export default function ToolIcon({ tool, ...props }: { tool: string } & LucideProps) {
  const t = tool.toLowerCase()
  if (/money|pay|transfer|bank/.test(t)) return <CreditCard {...props} />
  if (/mail|inbox/.test(t)) return <Mail {...props} />
  if (/web|search|browse/.test(t)) return <Globe {...props} />
  if (/file/.test(t)) return <FileText {...props} />
  if (/balance/.test(t)) return <Wallet {...props} />
  return <Wrench {...props} />
}
