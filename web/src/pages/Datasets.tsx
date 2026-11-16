import { useQuery, useQueryClient } from '@tanstack/react-query'
import { ChartColumn, Database, Download, ExternalLink, Eye, FileText, Globe, Laptop, RefreshCw, Search } from 'lucide-react'
import { useState } from 'react'
import Donut from '../components/Donut'
import Markdown from '../components/Markdown'
import Modal from '../components/Modal'
import { Card, ErrorNote, PageHeader, Spinner } from '../components/ui'
import { api, type Datasets as DatasetsData } from '../lib/api'

type FileInfo = DatasetsData['files'][number]
type Action = 'preview' | 'open'

function SourcePill({ sources }: { sources: string[] }) {
  const Icon = sources.some((s) => s.includes('external')) ? Globe : Laptop
  return (
    <span className="inline-flex items-center gap-1.5 rounded-lg border border-line2 bg-accent/12 px-2.5 py-1 text-[0.76rem] font-semibold text-[#E9D5FF]">
      <Icon size={13} aria-hidden /> {sources.join(', ')}
    </span>
  )
}

function Progress({ pct }: { pct: number }) {
  return (
    <div className="flex items-center gap-2.5">
      <div className="h-2 flex-1 overflow-hidden rounded-full bg-[#1E2952]" role="progressbar" aria-valuenow={pct} aria-valuemin={0} aria-valuemax={100}>
        <div className="h-full rounded-full bg-gradient-to-r from-ok to-[#2EE59D]" style={{ width: `${pct}%` }} />
      </div>
      <span className="w-10 text-right text-xs text-muted tabular-nums">{pct}%</span>
    </div>
  )
}

function FileModal({ file, action, onClose }: { file: FileInfo; action: Action; onClose: () => void }) {
  const { data, error, isPending } = useQuery({ queryKey: ['dataset', file.file], queryFn: () => api.datasetPreview(file.file) })
  const cols = ['id', 'language', 'label', 'attack_type', 'source', 'notes', 'text'] as const
  return (
    <Modal wide onClose={onClose} title={<><code className="font-mono">{file.file}</code> · {file.items} items</>}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-sm text-muted">
            Reviewed <b className="text-ink">{file.reviewed} / {file.items}</b> · Sources: <b className="text-ink">{file.sources.join(', ')}</b>
          </p>
          <a href={api.datasetDownloadUrl(file.file)} download={file.file}
            className="inline-flex min-h-10 items-center justify-center gap-2 rounded-lg border border-line2 bg-accent/15 px-3.5 text-sm font-semibold">
            <Download size={15} aria-hidden /> Download JSONL
          </a>
        </div>
        {isPending && <Spinner />}
        {error && <ErrorNote error={error} />}
        {data && action === 'open' && (
          <div>
            <p className="mb-2 text-sm text-muted">Per-language breakdown in this file:</p>
            <div className="overflow-x-auto rounded-lg border border-line">
              <table className="w-full text-sm">
                <thead className="bg-card2 text-xs text-muted">
                  <tr>{['Language', 'Attack', 'Benign', 'Reviewed'].map((h) => <th key={h} className="px-3 py-2 text-left font-medium">{h}</th>)}</tr>
                </thead>
                <tbody>
                  {data.by_language.map((r) => (
                    <tr key={r.language} className="border-t border-line/60">
                      <td className="px-3 py-2 font-bold">{r.label}</td>
                      <td className="px-3 py-2 tabular-nums">{r.attack}</td>
                      <td className="px-3 py-2 tabular-nums">{r.benign}</td>
                      <td className="px-3 py-2 tabular-nums">{r.reviewed}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
        {data && (
          <div>
            <p className="mb-2 text-sm text-muted">Sample records (showing first {data.records.length} of {data.total}):</p>
            <div className="overflow-x-auto rounded-lg border border-line">
              <table className="w-full min-w-[820px] text-[0.8rem]">
                <thead className="bg-card2 text-xs text-muted">
                  <tr>{cols.map((c) => <th key={c} className="px-3 py-2 text-left font-medium">{c}</th>)}</tr>
                </thead>
                <tbody>
                  {data.records.map((r, i) => (
                    <tr key={String(r.id ?? i)} className="border-t border-line/60 align-top">
                      {cols.map((c) => (
                        <td key={c} className={`px-3 py-2 ${c === 'text' ? 'min-w-[280px]' : 'whitespace-nowrap'} ${c === 'id' ? 'font-mono text-[#C9B6FF]' : ''}`}>
                          {String(r[c] ?? (c === 'attack_type' ? '–' : ''))}
                        </td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>
    </Modal>
  )
}

export default function Datasets() {
  const queryClient = useQueryClient()
  const { data, error, isPending, isFetching } = useQuery({ queryKey: ['datasets'], queryFn: api.datasets })
  const [search, setSearch] = useState('')
  const [source, setSource] = useState('')
  const [open, setOpen] = useState<{ file: FileInfo; action: Action } | null>(null)
  const [readme, setReadme] = useState(false)
  const doc = useQuery({ queryKey: ['doc', 'datasets-readme'], queryFn: () => api.doc('datasets-readme'), enabled: readme })

  const langs = data?.languages ?? []
  const grand = langs.reduce((s, l) => s + l.attack + l.benign, 0)
  const totalAttack = langs.reduce((s, l) => s + l.attack, 0)
  const totalBenign = langs.reduce((s, l) => s + l.benign, 0)
  const sources = [...new Set((data?.files ?? []).flatMap((f) => f.sources))].sort()
  const q = search.trim().toLowerCase()
  const files = (data?.files ?? []).filter(
    (f) => (!q || f.file.toLowerCase().includes(q) || f.sources.join(', ').toLowerCase().includes(q)) && (!source || f.sources.includes(source)),
  )

  const headerRight = (
    <>
      <button type="button" onClick={() => void queryClient.invalidateQueries({ queryKey: ['datasets'] })}
        className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl border border-line2 bg-card2/80 px-4 text-sm font-semibold hover:bg-accent/12 sm:flex-none">
        <RefreshCw size={15} className={isFetching ? 'animate-spin' : ''} aria-hidden /> Refresh
      </button>
      <button type="button" onClick={() => setReadme(true)}
        className="inline-flex min-h-11 flex-1 items-center justify-center gap-2 rounded-xl border border-line2 bg-card2/80 px-4 text-sm font-semibold hover:bg-accent/12 sm:flex-none">
        <FileText size={15} aria-hidden /> View README
      </button>
    </>
  )

  return (
    <>
      <PageHeader icon={Database} title="Datasets" sub="Labeled texts used by the benchmark and for training. Fake data only (numbers start with 010, domains end in .example)." right={headerRight} />
      {isPending && <Spinner />}
      {error && <ErrorNote error={error} />}
      {data && (
        <div className="flex flex-col gap-4">
          <div className="grid gap-4 lg:grid-cols-[1.48fr_1fr]">
            <Card>
              <div className="mb-4 flex items-center gap-3">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-line2 bg-accent/15 text-[#D8B4FE]"><ChartColumn size={19} aria-hidden /></span>
                <div>
                  <h2 className="font-bold">Language Distribution</h2>
                  <p className="text-[0.8rem] text-muted">Number of samples by language in the dataset.</p>
                </div>
              </div>
              <table className="hidden w-full text-sm sm:table">
                <thead className="text-xs text-muted">
                  <tr className="border-b border-line">
                    {['Language', 'Attack', 'Benign', 'Total', 'Share'].map((h) => <th key={h} className="py-2 pr-3 text-left font-medium">{h}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {langs.map((l) => {
                    const tot = l.attack + l.benign
                    const share = grand ? (tot / grand) * 100 : 0
                    return (
                      <tr key={l.language} className="border-b border-line/50">
                        <td className="py-3 pr-3 font-bold">{l.label}</td>
                        <td className="py-3 pr-3 tabular-nums">{l.attack}</td>
                        <td className="py-3 pr-3 tabular-nums">{l.benign}</td>
                        <td className="py-3 pr-3 tabular-nums">{tot}</td>
                        <td className="w-[40%] py-3">
                          <div className="flex items-center gap-2">
                            <span className="w-12 text-xs text-muted tabular-nums">{share.toFixed(1)}%</span>
                            <div className="h-2 flex-1 rounded-full bg-[#1E2952]"><div className="h-full rounded-full bg-gradient-to-r from-accent to-accent2" style={{ width: `${Math.min(100, Math.max(4, share * 1.6))}%` }} /></div>
                          </div>
                        </td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
              <ul className="flex flex-col gap-2.5 sm:hidden">
                {langs.map((l) => {
                  const tot = l.attack + l.benign
                  const share = grand ? (tot / grand) * 100 : 0
                  return (
                    <li key={l.language} className="flex flex-col gap-2 rounded-xl border border-line bg-card2/50 px-3.5 py-3">
                      <div className="flex items-center justify-between"><b>{l.label}</b><span className="text-[0.82rem] font-semibold tabular-nums">{tot} samples ({share.toFixed(1)}%)</span></div>
                      <div className="flex gap-2 text-[0.78rem]">
                        <span className="inline-flex items-center gap-1.5 rounded-md border border-line bg-bg/60 px-2 py-0.5"><span className="h-2 w-2 rounded-full bg-bad" aria-hidden />Attack: {l.attack}</span>
                        <span className="inline-flex items-center gap-1.5 rounded-md border border-line bg-bg/60 px-2 py-0.5"><span className="h-2 w-2 rounded-full bg-ok" aria-hidden />Benign: {l.benign}</span>
                      </div>
                    </li>
                  )
                })}
              </ul>
            </Card>
            <Card className="flex items-center justify-center">
              <Donut centerLabel="Total Samples" slices={[{ label: 'Attack', value: totalAttack, color: '#F04452' }, { label: 'Benign', value: totalBenign, color: '#16C784' }]} />
            </Card>
          </div>

          <Card>
            <div className="mb-4 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center gap-3">
                <span className="inline-flex h-10 w-10 items-center justify-center rounded-xl border border-line2 bg-accent/15 text-[#D8B4FE]"><FileText size={19} aria-hidden /></span>
                <div>
                  <h2 className="font-bold">Dataset Files</h2>
                  <p className="text-[0.8rem] text-muted">Dataset files, sizes and usage across the platform.</p>
                </div>
              </div>
              <div className="flex flex-col gap-2 sm:flex-row">
                <label className="relative">
                  <span className="sr-only">Search dataset files</span>
                  <Search size={15} className="pointer-events-none absolute top-1/2 left-3 -translate-y-1/2 text-muted" aria-hidden />
                  <input type="search" value={search} onChange={(e) => setSearch(e.target.value)} placeholder="Search file (e.g., attacks.jsonl)…"
                    className="min-h-11 w-full rounded-xl border border-line bg-card2/80 pr-3 pl-9 text-sm placeholder:text-muted sm:w-64" />
                </label>
                <select aria-label="Filter by source" value={source} onChange={(e) => setSource(e.target.value)} className="min-h-11 rounded-xl border border-line bg-card2/80 px-3 text-sm">
                  <option value="">All Sources</option>
                  {sources.map((s) => <option key={s}>{s}</option>)}
                </select>
              </div>
            </div>

            {files.length === 0 ? (
              <p className="py-4 text-sm text-muted">No dataset files match your current search or source filter.</p>
            ) : (
              <>
                <div className="hidden overflow-x-auto md:block">
                  <table className="w-full text-sm">
                    <thead className="text-xs text-muted">
                      <tr className="border-b border-line">
                        {['File', 'Items', 'Reviewed', 'Review Progress', 'Source', 'Actions'].map((h) => <th key={h} className="px-2 py-2 text-left font-medium">{h}</th>)}
                      </tr>
                    </thead>
                    <tbody>
                      {files.map((f) => (
                        <tr key={f.file} className="border-b border-line/50 hover:bg-accent/5">
                          <td className="px-2 py-3"><span className="inline-flex items-center gap-2 font-semibold"><span className="rounded-md border border-line2 bg-accent/15 px-1.5 font-mono text-xs text-[#D8B4FE]">{'{}'}</span>{f.file}</span></td>
                          <td className="px-2 py-3 tabular-nums">{f.items}</td>
                          <td className="px-2 py-3 tabular-nums">{f.reviewed} / {f.items}</td>
                          <td className="min-w-[160px] px-2 py-3"><Progress pct={f.items ? Math.round((f.reviewed / f.items) * 100) : 0} /></td>
                          <td className="px-2 py-3"><SourcePill sources={f.sources} /></td>
                          <td className="px-2 py-3">
                            <div className="flex gap-1.5">
                              <button type="button" aria-label={`Preview ${f.file}`} title="Preview" onClick={() => setOpen({ file: f, action: 'preview' })} className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line hover:border-line2"><Eye size={15} aria-hidden /></button>
                              <button type="button" aria-label={`Inspect ${f.file}`} title="Inspect & download" onClick={() => setOpen({ file: f, action: 'open' })} className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-line hover:border-line2"><ExternalLink size={15} aria-hidden /></button>
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
                <ul className="flex flex-col gap-2.5 md:hidden">
                  {files.map((f) => (
                    <li key={f.file} className="flex flex-col gap-2.5 rounded-xl border border-line bg-card2/50 p-3.5">
                      <div className="flex flex-wrap items-center justify-between gap-2">
                        <span className="inline-flex items-center gap-2 font-bold"><span className="rounded-md border border-line2 bg-accent/15 px-1.5 font-mono text-xs text-[#D8B4FE]">{'{}'}</span>{f.file}</span>
                        <SourcePill sources={f.sources} />
                      </div>
                      <div className="flex justify-between text-[0.82rem]"><span>Items: <b>{f.items}</b></span><span>Reviewed: <b>{f.reviewed} / {f.items}</b></span></div>
                      <Progress pct={f.items ? Math.round((f.reviewed / f.items) * 100) : 0} />
                      <div className="grid grid-cols-2 gap-2">
                        <button type="button" onClick={() => setOpen({ file: f, action: 'preview' })} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-line text-sm font-semibold"><Eye size={15} aria-hidden /> Preview</button>
                        <button type="button" onClick={() => setOpen({ file: f, action: 'open' })} className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl border border-line text-sm font-semibold"><ExternalLink size={15} aria-hidden /> Inspect</button>
                      </div>
                    </li>
                  ))}
                </ul>
              </>
            )}
          </Card>
        </div>
      )}

      {open && <FileModal file={open.file} action={open.action} onClose={() => setOpen(null)} />}
      {readme && (
        <Modal wide title="datasets/README.md" onClose={() => setReadme(false)}>
          {doc.isPending && <Spinner />}
          {doc.error && <ErrorNote error={doc.error} />}
          {doc.data && <Markdown text={doc.data.markdown} />}
        </Modal>
      )}
    </>
  )
}
