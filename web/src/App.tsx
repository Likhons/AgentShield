import { ChartColumn, Database, FileText, Scale } from 'lucide-react'
import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout'
import Placeholder from './pages/Placeholder'
import Playground from './pages/Playground'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Playground />} />
        <Route path="benchmarks" element={<Placeholder icon={ChartColumn} title="Benchmarks" sub="Numbers come only from saved runs in benchmark/results/." />} />
        <Route path="audit" element={<Placeholder icon={FileText} title="Audit Log" sub="Every AgentShield decision, newest first." />} />
        <Route path="policies" element={<Placeholder icon={Scale} title="Policies" sub="Deterministic rules from default.yaml." />} />
        <Route path="datasets" element={<Placeholder icon={Database} title="Datasets" sub="Labeled texts used by the benchmark and for training." />} />
        <Route path="*" element={<Placeholder icon={FileText} title="Not found" sub="This page does not exist." />} />
      </Route>
    </Routes>
  )
}
