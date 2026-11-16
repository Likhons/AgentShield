import { FileText } from 'lucide-react'
import { lazy, Suspense, type ReactNode } from 'react'
import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { Spinner } from './components/ui'
import Placeholder from './pages/Placeholder'
import Landing from './pages/Landing'
import Playground from './pages/Playground'

// Playground is the landing page and loads with the app; the rest (charts, Markdown) load when opened.
const AuditLog = lazy(() => import('./pages/AuditLog'))
const Benchmarks = lazy(() => import('./pages/Benchmarks'))
const Datasets = lazy(() => import('./pages/Datasets'))
const Policies = lazy(() => import('./pages/Policies'))

const page = (el: ReactNode) => <Suspense fallback={<Spinner />}>{el}</Suspense>

export default function App() {
  return (
    <Routes>
      <Route index element={<Landing />} />
      <Route element={<Layout />}>
        <Route path="playground" element={<Playground />} />
        <Route path="benchmarks" element={page(<Benchmarks />)} />
        <Route path="audit" element={page(<AuditLog />)} />
        <Route path="policies" element={page(<Policies />)} />
        <Route path="datasets" element={page(<Datasets />)} />
        <Route path="*" element={<Placeholder icon={FileText} title="Not found" sub="This page does not exist." />} />
      </Route>
    </Routes>
  )
}
