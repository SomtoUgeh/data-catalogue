import { createFileRoute, useRouter } from '@tanstack/react-router'

import { fetchDatasets } from '../api/datasetFns'
import { CataloguePage } from '../components/CataloguePage'

export const Route = createFileRoute('/')({
  loader: () => fetchDatasets(),
  pendingComponent: CataloguePending,
  errorComponent: CatalogueError,
  component: Home,
})

function Home() {
  const datasets = Route.useLoaderData()
  const router = useRouter()

  return (
    <CataloguePage
      datasets={datasets}
      onChanged={() => router.invalidate()}
    />
  )
}

function CataloguePending() {
  return (
    <main>
      <h1>Data catalogue</h1>
      <p aria-live="polite">Loading datasets…</p>
    </main>
  )
}

function CatalogueError({ error }: { error: Error }) {
  return (
    <main>
      <h1>Data catalogue</h1>
      <p role="alert" aria-live="assertive">
        {error.message || 'Could not load datasets.'}
      </p>
    </main>
  )
}
