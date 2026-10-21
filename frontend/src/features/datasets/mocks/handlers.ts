import { http, HttpResponse } from 'msw'
import * as z from 'zod'

import { zDatasetCreate } from '../api/generated/zod.gen'
import { createStoredDataset, deleteStoredDataset, listStoredDatasets } from './store'

// Like the API, the mock trims the text fields before it validates them.
const createBodySchema = zDatasetCreate.extend({
  name: z.string().trim().min(1),
  owner: z.string().trim().default(''),
  description: z.string().trim().min(1),
})

export const datasetsHandlers = [
  http.get('/datasets', () => HttpResponse.json(listStoredDatasets(), { status: 200 })),

  http.post('/datasets', async ({ request }) => {
    const parsed = createBodySchema.safeParse(await request.json())
    if (!parsed.success) {
      const fields = parsed.error.issues.map((issue) => {
        const field = String(issue.path[0])
        return { field, message: `${field} is required` }
      })
      return HttpResponse.json({ error: 'Validation failed', fields }, { status: 400 })
    }
    return HttpResponse.json(createStoredDataset(parsed.data), { status: 201 })
  }),

  http.delete('/datasets/:dataset_id', ({ params }) => {
    const datasetId = String(params.dataset_id)
    const deleted = deleteStoredDataset(datasetId)
    if (!deleted) {
      return HttpResponse.json({ error: `Dataset '${datasetId}' not found` }, { status: 404 })
    }
    return HttpResponse.json(deleted, { status: 200 })
  }),
]
