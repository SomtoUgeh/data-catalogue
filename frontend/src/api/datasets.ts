import { ApiError, type Dataset, type DatasetInput } from '../types'

function apiBase(): string {
  if (typeof process !== 'undefined' && process.env.API_BASE_URL) {
    return process.env.API_BASE_URL
  }
  return import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000'
}

async function readError(response: Response): Promise<ApiError> {
  const body = (await response.json().catch(() => ({}))) as { error?: string }
  return new ApiError(body.error ?? `Request failed (${response.status})`, response.status)
}

export async function listDatasets(): Promise<Dataset[]> {
  const response = await fetch(`${apiBase()}/datasets`)
  if (!response.ok) throw await readError(response)
  return response.json()
}

export async function createDataset(input: DatasetInput): Promise<Dataset> {
  const response = await fetch(`${apiBase()}/datasets`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(input),
  })
  if (!response.ok) throw await readError(response)
  return response.json()
}

export async function deleteDataset(id: string): Promise<Dataset> {
  const response = await fetch(`${apiBase()}/datasets/${id}`, { method: 'DELETE' })
  if (!response.ok) throw await readError(response)
  return response.json()
}
