import { lazy, Suspense, type ReactNode } from 'react'
import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import { Spinner } from './components/ui'
import Placeholder from './pages/Placeholder'
import Landing from './pages/Landing'
import { loaders } from './lib/pages'
import { useSpotlight } from './lib/spotlight'

// The landing page loads with the app; every dashboard page is its own chunk. They are fetched in the background
// (lib/pages.ts) once the visitor is in the dashboard, and the Playground already while the landing page is read.
const Playground = lazy(loaders.playground)
const AuditLog = lazy(loaders.audit)
const Benchmarks = lazy(loaders.benchmarks)
const Datasets = lazy(loaders.datasets)
const Policies = lazy(loaders.policies)
const Network = lazy(loaders.network)

const page = (el: ReactNode) => <Suspense fallback={<Spinner />}>{el}</Suspense>

export default function App() {
  useSpotlight() // spotlight borders and card tilt, app-wide
  return (
    <Routes>
      <Route index element={<Landing />} />
      <Route element={<Layout />}>
        <Route path="playground" element={page(<Playground />)} />
        <Route path="benchmarks" element={page(<Benchmarks />)} />
        <Route path="audit" element={page(<AuditLog />)} />
        <Route path="policies" element={page(<Policies />)} />
        <Route path="datasets" element={page(<Datasets />)} />
        <Route path="network" element={page(<Network />)} />
        <Route path="*" element={<Placeholder title="Not found" sub="This page does not exist." />} />
      </Route>
    </Routes>
  )
}
