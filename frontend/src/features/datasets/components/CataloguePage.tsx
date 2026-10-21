import { useSuspenseQuery } from '@tanstack/react-query'

import { PageShell } from '@/components/page-shell'
import { StatusBanner } from '@/components/status-banner'
import { getErrorMessage } from '../api/errors'
import { useDeleteDatasetMutation } from '../api/mutations'
import { datasetsQueryOptions } from '../api/queryOptions'
import { AddDatasetForm } from './AddDatasetForm'
import { CatalogueHeader } from './CatalogueHeader'
import { DatasetList } from './DatasetList'

export function CataloguePage() {
  const { data: datasets } = useSuspenseQuery(datasetsQueryOptions())
  const deleteDataset = useDeleteDatasetMutation()

  return (
    <PageShell>
      <CatalogueHeader />
      {deleteDataset.isError ? (
        <StatusBanner>{getErrorMessage(deleteDataset.error)}</StatusBanner>
      ) : null}
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(20rem,24rem)_minmax(0,1fr)]">
        <div className="lg:sticky lg:top-6">
          <AddDatasetForm />
        </div>
        <DatasetList
          datasets={datasets}
          deletingId={deleteDataset.isPending ? (deleteDataset.variables ?? null) : null}
          onDelete={(id) => {
            deleteDataset.reset()
            deleteDataset.mutate(id)
          }}
        />
      </div>
    </PageShell>
  )
}
