import { useState } from 'react'

import { createDataset, deleteDataset } from '../api/datasets'
import { AddDatasetForm } from './AddDatasetForm'
import { DatasetList } from './DatasetList'
import { StatusBanner } from './StatusBanner'
import type { Dataset, DatasetInput } from '../types'

type CataloguePageProps = {
  datasets: Dataset[]
  onChanged: () => Promise<unknown> | unknown
}

export function CataloguePage({ datasets, onChanged }: CataloguePageProps) {
  const [listError, setListError] = useState<string | null>(null)

  async function handleCreate(input: DatasetInput): Promise<Dataset> {
    setListError(null)
    const created = await createDataset(input)
    await onChanged()
    return created
  }

  async function handleDelete(id: string): Promise<void> {
    setListError(null)
    try {
      await deleteDataset(id)
      await onChanged()
    } catch (error) {
      setListError(error instanceof Error ? error.message : 'Could not delete the dataset.')
    }
  }

  return (
    <main>
      <h1>Data catalogue</h1>
      {listError ? <StatusBanner>{listError}</StatusBanner> : null}
      <AddDatasetForm onSubmit={handleCreate} />
      <DatasetList datasets={datasets} onDelete={handleDelete} />
    </main>
  )
}
