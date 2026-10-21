import type { Dataset } from '../types'
import { DatasetRow } from './DatasetRow'

type DatasetListProps = {
  datasets: Dataset[]
  onDelete: (id: string) => Promise<void>
}

export function DatasetList({ datasets, onDelete }: DatasetListProps) {
  if (datasets.length === 0) {
    return <p>No datasets yet. Add one with the form above.</p>
  }

  return (
    <table>
      <thead>
        <tr>
          <th scope="col">Name</th>
          <th scope="col">Owner</th>
          <th scope="col">Tags</th>
          <th scope="col">Summary</th>
          <th scope="col">Actions</th>
        </tr>
      </thead>
      <tbody>
        {datasets.map((dataset) => (
          <DatasetRow key={dataset.id} dataset={dataset} onDelete={onDelete} />
        ))}
      </tbody>
    </table>
  )
}
