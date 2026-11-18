// Typed client for the Python dashboard API (webapi/app.py). Same-origin: Vite proxies /api in dev,
// a Vercel rewrite does it in production.

export type Decision = 'allow' | 'ask_human' | 'block'
export type RunMode = 'mock' | 'groq' | 'recorded'

export interface Rate {
  text: string
  hits: number | null
  total: number | null
  pct: number | null
  ci: [number, number] | null
}

export interface Overview {
  version: string
  agent_llm: string
  detector: string
  checks: string[]
  policy_rules: number
  decisions_logged: number
  attack_samples: { total: number; by_language: Record<string, number> }
  real_llm: { source: string; with: Rate; without: Rate } | null
  live_mode_available: boolean
}

export interface UntrustedItem {
  source: 'tool:email' | 'tool:web' | 'tool:file'
  origin: string
  title: string
  text: string
  kind: 'attack' | 'normal'
}

export interface Scenario {
  name: string
  kind: 'attack' | 'benign'
  description: string
  user_task: string
  has_recording: boolean
  untrusted?: UntrustedItem[] // missing on API servers older than 17 Nov
  requests?: { to: string; amount: number; origin: string; kind: 'attack' | 'normal' }[]
}

export interface Thresholds {
  ask_human_at: number
  block_at: number
}

export interface CheckResult {
  check: string
  risk_score: number
  flagged: boolean
  skipped: boolean
  reason_en: string
  reason_bn: string
  latency_ms: number
  details?: Record<string, unknown>
  forced_decision?: Decision | null
}

export interface Verdict {
  request_id: string
  decision: Decision
  risk_score: number
  reason_en: string
  reason_bn: string
  checks: CheckResult[]
  total_latency_ms: number
}

export interface Step {
  number: number
  tool: string
  args: Record<string, unknown>
  result: string
  stopped_by_shield: boolean
  verdict: Verdict | null
}

export interface RunSide {
  task: string
  shielded: boolean
  start_balance: number
  end_balance: number
  stolen: number
  unauthorized: { to: string; amount: number }[]
  stopped: number
  steps: Step[]
  final_answer: string
}

export interface RunResult {
  scenario: string
  mode: RunMode
  recorded_utc: string | null
  banner: { tone: 'saved' | 'neutral' | 'held'; text: string } | null
  without: RunSide
  with: RunSide
}

export interface AuditRecord {
  id: string
  timestamp: string
  session_id: string
  request_id: string
  user_request: string
  tool_name: string
  arguments: Record<string, unknown>
  decision: Decision
  risk_score: number
  reason_en: string
  reason_bn: string
  tainted: boolean
  total_latency_ms: number
  checks: CheckResult[]
}

export interface AuditStats {
  total: number
  allow: number
  ask_human: number
  block: number
  llm_calls: number
  median_latency_ms: number | null
}

export interface AuditPage {
  records: AuditRecord[]
  total: number
  counts: Record<string, number>
  stats: AuditStats
  tools: string[]
  thresholds: Thresholds
  newest: string | null
}

export interface AuditFilters {
  decision?: Decision
  search?: string
  tool?: string
  tainted?: boolean
  min_risk?: number
  since?: string
  limit?: number
  offset?: number
}

export interface AgentRow {
  language: string
  label: string
  'attack success WITHOUT AgentShield': Rate
  'attack success WITH AgentShield': Rate
  'benign task done WITHOUT': Rate
  'benign task done WITH': Rate
}

export interface AgentSection {
  kind: 'agent'
  title: string
  source: string
  provider: string
  note: string
  detector: string
  runs: number
  rows: AgentRow[]
  outcomes: { language: string; item: string; 'outcomes with AgentShield': string }[]
  outcome_totals: { outcome: string; count: number }[]
}

export interface DetectionSection {
  kind: 'detection'
  title: string
  source: string
  note: string
  dataset: string
  rows: { detector: string; language: string; label: string; attacks_flagged: Rate; benign_flagged: Rate }[]
}

export type BenchmarkSection = AgentSection | DetectionSection

export interface PolicyRule {
  id: string
  description?: string
  tools?: string[]
  when?: Record<string, unknown>
  decision: Decision
  risk?: number
  reason_en?: string
  reason_bn?: string
}

export interface Policies {
  file: string
  rules: PolicyRule[]
  yaml: Record<string, string>
  thresholds: Thresholds
}

export interface DatasetPreview {
  file: string
  total: number
  records: Record<string, unknown>[]
  texts_public: boolean
  note: string | null
  by_language: { language: string; label: string; attack: number; benign: number; reviewed: number }[]
}

export interface Datasets {
  languages: { language: string; label: string; attack: number; benign: number }[]
  files: { file: string; items: number; reviewed: number; sources: string[]; size_bytes: number; texts_public: boolean }[]
}

export type SandboxSource = 'tool:email' | 'tool:web' | 'tool:file'

export interface SandboxPreset {
  id: string
  kind: 'normal' | 'attack'
  language: string
  label: string
  content: string
  to: string
  amount: number
}

export interface SandboxPresets {
  user_request: string
  contacts: Record<string, string>
  presets: SandboxPreset[]
}

export interface SandboxInput {
  user_request: string
  content: string
  source: SandboxSource
  to: string
  amount: number
}

export interface SandboxResult {
  verdict: Verdict
  thresholds: Thresholds
  judge: string
  found_order: { to: string; amount: number } | null
}

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

// -- network (simulated wallet, cross-user graph check: benchmark/network.py) --
export type NetOutcome = 'moved' | 'agentshield' | 'network'
export type NetTier = 'flagged' | 'cashout' | 'watch' | 'clear'

export interface NetPayment {
  t: string
  amount?: number
  outcome: NetOutcome
}

export interface NetMember {
  number: string
  role: 'collecting' | 'cash-out'
  tier: NetTier
  flagged_at: string | null
  flagged_after: number | null
  score: number
  payers: number
  attempts: NetPayment[]
  received_from: string[]
  origins: string[]
  truth: string
}

export interface NetRing {
  id: string
  name: string
  first: string
  last: string
  people: number
  attempts: number
  sources: string[]
  origins: string[]
  moved_per_call: number
  moved_with_network: number
  members: NetMember[]
  edges: { from: string; to: string; amount: number; held: boolean }[]
  truth: string[]
}

export interface NetAccount {
  number: string
  known_as: string
  tier: NetTier
  score: number
  parts: { fan_in: number; pass_through: number; untrusted: number; linked: number }
  strangers: number
  pass_through: number
  untrusted: number
  linked: boolean
  payers: number
  flagged_at: string | null
  flagged_after: number | null
  truth: string
  truth_role: string
}

export interface NetMoney {
  scam_attempts: number
  scam_moved: number
  scam_moved_count: number
  scam_stopped_agentshield: number
  scam_stopped_network: number
  legit_attempts: number
  legit_paid: number
  legit_blocked_network: number
  legit_extra_confirm: number
  legit_declined_network: number
}

export interface NetworkReport {
  simulated: true
  note: string
  params: {
    seed: number
    window_hours: number
    fan_in_full: number
    min_inflow: number
    weights: { fan_in: number; pass_through: number; untrusted: number; linked: number }
    flag_at: number
    watch_at: number
    cashout_share: number
    approve_legit: number
    approve_scam: number
  }
  world: { users: number; accounts: number; payments: number; forwards: number; start: string; end: string }
  per_call: NetMoney
  with_network: NetMoney
  spotlight: {
    number: string
    first_payment: { t: string; amount: number; source: string; origin: string | null; verdict: Decision; rule: string | null }
    per_person_median: number
    first_seen: string
    flagged_at: string
    flagged_after: number
    people: number
    last_seen: string
    sources: string[]
    payments: NetPayment[]
  }
  rings: NetRing[]
  accounts: NetAccount[]
  evaluation: {
    mules: number
    mules_flagged: number
    mules_watch: number
    cashouts: number
    cashouts_found: number
    legit_accounts: number
    legit_flagged: number
    legit_watch: number
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...init })
  if (!res.ok) {
    let detail = res.statusText
    try {
      const d = (await res.json()).detail
      // FastAPI validation errors are a list of {msg}; everything else is a string
      detail = Array.isArray(d) ? d.map((x) => x?.msg ?? String(x)).join('; ') : (d ?? detail)
    } catch {
      /* not JSON */
    }
    throw new ApiError(res.status, String(detail))
  }
  return res.json() as Promise<T>
}

function query(params: Record<string, string | number | boolean | undefined>): string {
  const q = new URLSearchParams()
  for (const [k, v] of Object.entries(params)) if (v !== undefined && v !== '') q.set(k, String(v))
  const s = q.toString()
  return s ? `?${s}` : ''
}

export const api = {
  overview: () => request<Overview>('/api/overview'),
  scenarios: () => request<Scenario[]>('/api/scenarios'),
  run: (name: string, mode: RunMode, approve: boolean) =>
    request<RunResult>(`/api/scenarios/${encodeURIComponent(name)}/run`, {
      method: 'POST',
      body: JSON.stringify({ mode, approve }),
    }),
  audit: (f: AuditFilters) => request<AuditPage>(`/api/audit${query({ ...f })}`),
  auditRecord: (id: string) => request<AuditRecord>(`/api/audit/${encodeURIComponent(id)}`),
  auditCsvUrl: (f: Omit<AuditFilters, 'limit' | 'offset'>) => `/api/audit.csv${query({ ...f })}`,
  benchmarks: () => request<{ sections: BenchmarkSection[] }>('/api/benchmarks'),
  policies: () => request<Policies>('/api/policies'),
  network: () => request<NetworkReport>('/api/network'),
  validatePolicy: (rule: Record<string, unknown>) =>
    request<{ valid: boolean; yaml?: string; error?: string }>('/api/policies/validate', { method: 'POST', body: JSON.stringify(rule) }),
  doc: (name: 'results' | 'datasets-readme') => request<{ name: string; file: string; markdown: string }>(`/api/docs/${name}`),
  datasets: () => request<Datasets>('/api/datasets'),
  datasetPreview: (file: string, limit = 15) =>
    request<DatasetPreview>(`/api/datasets/${encodeURIComponent(file)}${query({ limit })}`),
  datasetDownloadUrl: (file: string) => `/api/datasets/${encodeURIComponent(file)}/download`,
  sandboxPresets: () => request<SandboxPresets>('/api/check/presets'),
  sandboxCheck: (body: SandboxInput, signal?: AbortSignal) =>
    request<SandboxResult>('/api/check', { method: 'POST', body: JSON.stringify(body), signal }),
}
