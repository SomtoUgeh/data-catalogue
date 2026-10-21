import { http, HttpResponse } from 'msw'

import { getApiBaseUrl } from '@/lib/api-base'
import { zodIssuesToFieldErrors } from '../api/errors'
import { zDatasetCreate } from '../api/generated/zod.gen'
import {
  createStoredDataset,
  deleteStoredDataset,
  listStoredDatasets,
} from './store'

function apiUrl(path: string): string {
  const base = getApiBaseUrl()
  return base ? `${base}${path}` : path
}

function trimCreateBody(raw: unknown): unknown {
  if (!raw || typeof raw !== 'object') return raw
  const body = raw as Record<string, unknown>
  const next: Record<string, unknown> = { ...body }
  for (const key of ['name', 'owner', 'description']) {
    if (typeof next[key] === 'string') next[key] = next[key].trim()
  }
  return next
}

function validationFailed(fields: Record<string, string>) {
  return HttpResponse.json(
    {
      error: 'Validation failed',
      fields: Object.entries(fields).map(([field, message]) => ({ field, message })),
    },
    { status: 400 },
  )
}

export const datasetsHandlers = [
  http.get(apiUrl('/datasets'), () => {
    return HttpResponse.json(listStoredDatasets(), { status: 200 })
  }),

  http.post(apiUrl('/datasets'), async ({ request }) => {
    const parsed = zDatasetCreate.safeParse(trimCreateBody(await request.json().catch(() => ({}))))
    if (!parsed.success) {
      const fields: Record<string, string> = {}
      for (const field of Object.keys(zodIssuesToFieldErrors(parsed.error))) {
        fields[field] = `${field} is required`
      }
      return validationFailed(fields)
    }

    const failed = request.headers.get('x-curator') === 'fail'
    const created = createStoredDataset(
      {
        name: parsed.data.name,
        owner: parsed.data.owner,
        description: parsed.data.description,
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
