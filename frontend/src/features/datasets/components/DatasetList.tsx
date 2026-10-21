import type { Dataset } from '../api/generated/types.gen'
import { DatasetEmptyState } from './DatasetEmptyState'
import { DatasetRow } from './DatasetRow'

type DatasetListProps = {
  datasets: Dataset[]
  deletingId: string | null
  onDelete: (id: string) => void
}

function ListHeader({ count }: { count: number }) {
  return (
    <div className="flex items-baseline justify-between gap-3">
      <h2 className="text-lg font-medium tracking-tight">Datasets</h2>
      <p className="text-sm text-muted-foreground" aria-live="polite">
        {count === 1 ? '1 dataset' : `${count} datasets`}
      </p>
    </div>
  )
}

export function DatasetList({ datasets, deletingId, onDelete }: DatasetListProps) {
  return (
    <section aria-label="Registered datasets" className="flex flex-col gap-3">
      <ListHeader count={datasets.length} />
      {datasets.length === 0 ? (
        <DatasetEmptyState />
      ) : (
        <div className="flex flex-col gap-3">
          {datasets.map((dataset) => (
            <DatasetRow
              key={dataset.id}
              dataset={dataset}
              isDeleting={deletingId === dataset.id}
              onDelete={onDelete}
            />
          ))}
        </div>
      )}
    </section>
  )
}
