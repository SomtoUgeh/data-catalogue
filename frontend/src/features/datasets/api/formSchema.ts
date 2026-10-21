import * as z from 'zod'

import { zDatasetCreate } from './generated/zod.gen'

// The generated schema has the API's rules. This adds trimming and messages for the form.
// The limits match backend/src/app/schemas.py.
export const datasetCreateFormSchema = zDatasetCreate.extend({
  name: z
    .string()
    .trim()
    .min(1, 'Name is required')
    .max(200, 'Name must be at most 200 characters'),
  owner: z.string().trim().max(200, 'Owner must be at most 200 characters'),
  description: z
    .string()
    .trim()
    .min(1, 'Description is required')
    .max(2000, 'Description must be at most 2000 characters'),
})
