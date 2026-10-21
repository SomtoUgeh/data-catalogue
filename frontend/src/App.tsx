import { DatasetForm } from './components/DatasetForm'
import { DatasetList } from './components/DatasetList'
import { useDatasets } from './hooks/useDatasets'

export function App() {
  const { datasets, isLoading, loadError, addDataset, removeDataset } = useDatasets()

  return (
    <main>
      <h1>Data Catalogue</h1>
      <DatasetForm onCreate={addDataset} />

      <section aria-labelledby="datasets-heading">
        <h2 id="datasets-heading">Datasets</h2>
        {isLoading && <p>Loading datasets…</p>}
        {loadError && (
          <p role="alert" className="error">
            Could not load datasets. {loadError}
          </p>
        )}
        {!isLoading && !loadError && <DatasetList datasets={datasets} onDelete={removeDataset} />}
      </section>
    </main>
  )
}
