import { http, HttpResponse } from 'msw'

import { getApiBaseUrl } from '@/lib/api-base'
import type { DatasetCreate } from '../api/generated/types.gen'
import {
  createStoredDataset,
  deleteStoredDataset,
  listStoredDatasets,
} from './store'

function apiUrl(path: string): string {
  const base = getApiBaseUrl()
  return base ? `${base}${path}` : path
}

function missingOrBlank(value: unknown): 'missing' | 'blank' | null {
  if (value === undefined) return 'missing'
  if (typeof value !== 'string' || !value.trim()) return 'blank'
  return null
}

export const datasetsHandlers = [
  http.get(apiUrl('/datasets'), () => {
    return HttpResponse.json(listStoredDatasets(), { status: 200 })
  }),

  http.post(apiUrl('/datasets'), async ({ request }) => {
    const body = (await request.json().catch(() => ({}))) as Partial<DatasetCreate>
    const nameIssue = missingOrBlank(body.name)
    if (nameIssue === 'missing') {
      return HttpResponse.json({ error: 'name is required' }, { status: 400 })
    }
    if (nameIssue === 'blank') {
      return HttpResponse.json({ error: 'name is required and cannot be blank' }, { status: 400 })
    }
    const descriptionIssue = missingOrBlank(body.description)
    if (descriptionIssue === 'missing') {
      return HttpResponse.json({ error: 'description is required' }, { status: 400 })
    }
    if (descriptionIssue === 'blank') {
      return HttpResponse.json({ error: 'description is required and cannot be blank' }, { status: 400 })
    }

    const failed = request.headers.get('x-curator') === 'fail'
    const created = createStoredDataset(
      {
        name: String(body.name).trim(),
        owner: typeof body.owner === 'string' ? body.owner.trim() : '',
        description: String(body.description).trim(),
      },
      failed,
    )
    return HttpResponse.json(created, { status: 201 })
  }),

  http.delete(apiUrl('/datasets/:dataset_id'), ({ params }) => {
    const datasetId = String(params.dataset_id)
    const deleted = deleteStoredDataset(datasetId)
    if (!deleted) {
      return HttpResponse.json(
        { error: `Dataset with id '${datasetId}' was not found.` },
        { status: 404 },
      )
    }
    return HttpResponse.json(deleted, { status: 200 })
  }),
]
