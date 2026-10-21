import type { Dataset, DatasetCreate } from '../api/generated/types.gen'
import { SEEDED_DATASETS } from './fixtures'

let items: Dataset[] = cloneSeed()
let nextId = 4

function cloneSeed(): Dataset[] {
  return SEEDED_DATASETS.map((item) => ({ ...item, tags: [...item.tags] }))
}

export function resetDatasetStore() {
  items = cloneSeed()
  nextId = 4
}

/** Newest first, like the API: up to `limit` datasets with ids below `before`. */
export function listStoredDatasets(limit: number, before: string | null): Dataset[] {
  return items
    .filter((item) => before === null || Number(item.id) < Number(before))
    .sort((a, b) => Number(b.id) - Number(a.id))
    .slice(0, limit)
    .map((item) => ({ ...item, tags: [...item.tags] }))
}

export function createStoredDataset(payload: DatasetCreate): Dataset {
  const dataset: Dataset = {
    id: String(nextId),
    name: payload.name,
    owner: payload.owner ?? '',
    description: payload.description,
    tags: ['trading', 'finance', 'settlements', 'daily'],
    summary: `A catalogue entry for ${payload.name}.`,
    curation_status: 'ok',
  }
  nextId += 1
  items = [...items, dataset]
  return { ...dataset, tags: [...dataset.tags] }
}

export function deleteStoredDataset(datasetId: string): Dataset | null {
  const index = items.findIndex((item) => item.id === datasetId)
  if (index === -1) return null
  const [removed] = items.splice(index, 1)
  return removed
}
