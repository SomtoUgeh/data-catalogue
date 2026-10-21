import { useEffect, useState } from 'react'

import { createDataset, deleteDataset, getErrorMessage, listDatasets } from '../services/datasetsApi'
import type { Dataset, NewDataset } from '../types'

export function useDatasets() {
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)

  useEffect(() => {
    let ignore = false
    listDatasets()
      .then((items) => {
        if (!ignore) setDatasets(items)
      })
      .catch((error: unknown) => {
        if (!ignore) setLoadError(getErrorMessage(error))
      })
      .finally(() => {
        if (!ignore) setIsLoading(false)
      })
    return () => {
      ignore = true
    }
  }, [])

  async function addDataset(input: NewDataset): Promise<Dataset> {
    const created = await createDataset(input)
    setDatasets((current) => [...current, created])
    return created
  }

  async function removeDataset(id: string): Promise<void> {
    await deleteDataset(id)
    setDatasets((current) => current.filter((dataset) => dataset.id !== id))
  }

  return { datasets, isLoading, loadError, addDataset, removeDataset }
}
