import { Button } from '@/components/ui/button'
import { Spinner } from '@/components/ui/spinner'
import type { Dataset } from '../api/generated/types.gen'
import { DatasetEmptyState } from './DatasetEmptyState'
import { DatasetRow } from './DatasetRow'

type DatasetListProps = {
  datasets: Dataset[]
  hasMore: boolean
  isLoadingMore: boolean
  onLoadMore: () => void
  deletingId: string | null
  onDelete: (id: string) => void
}

function countLabel(count: number, hasMore: boolean): string {
  if (hasMore) return `Showing the newest ${count}`
  return count === 1 ? '1 dataset' : `${count} datasets`
}

export function DatasetList({
  datasets,
  hasMore,
  isLoadingMore,
  onLoadMore,
  deletingId,
  onDelete,
}: DatasetListProps) {
  return (
    <section aria-label="Registered datasets" className="flex flex-col gap-3">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="text-lg font-medium tracking-tight">Datasets</h2>
        <p className="text-sm text-muted-foreground" aria-live="polite">
          {countLabel(datasets.length, hasMore)}
        </p>
      </div>
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
      {hasMore ? (
        <Button
          type="button"
          variant="outline"
          className="self-center"
          disabled={isLoadingMore}
          onClick={onLoadMore}
        >
          {isLoadingMore ? (
            <>
              <Spinner data-icon="inline-start" aria-hidden />
              Loading…
            </>
          ) : (
            'Load more datasets'
          )}
        </Button>
      ) : null}
    </section>
  )
}
