import { createServerFn } from '@tanstack/react-start'

import { createDataset, deleteDataset, listDatasets } from './datasets'
import type { DatasetInput } from '../types'

export const fetchDatasets = createServerFn({ method: 'GET' }).handler(() =>
  listDatasets(),
)

export const addDataset = createServerFn({ method: 'POST' })
  .validator((input: DatasetInput) => input)
  .handler(({ data }) => createDataset(data))

export const removeDataset = createServerFn({ method: 'POST' })
  .validator((id: string) => id)
  .handler(({ data }) => deleteDataset(data))
