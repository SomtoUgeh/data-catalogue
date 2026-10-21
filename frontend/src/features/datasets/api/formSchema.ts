import * as z from 'zod'

import { zDatasetCreate } from './generated/zod.gen'

export const datasetCreateFormSchema = zDatasetCreate.extend({
  name: z.string().trim().min(1, 'Name is required'),
  description: z.string().trim().min(1, 'Description is required'),
  owner: z.string().trim(),
})

export type DatasetCreateFormValues = z.infer<typeof datasetCreateFormSchema>
