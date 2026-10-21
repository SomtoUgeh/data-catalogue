import { DatasetRow } from './DatasetRow'
import type { Dataset } from '../types'

type DatasetListProps = {
  datasets: Dataset[]
  onDelete: (id: string) => Promise<void>
}

export function DatasetList({ datasets, onDelete }: DatasetListProps) {
  if (datasets.length === 0) {
    return <p>No datasets registered yet.</p>
  }

  return (
    <section aria-label="Registered datasets">
      <h2>Datasets</h2>
      <div className="dataset-list">
        {datasets.map((dataset) => (
          <DatasetRow key={dataset.id} dataset={dataset} onDelete={onDelete} />
        ))}
      </div>
    </section>
  )
}
