import type { Dataset, NewDataset } from '../types'

const DATASETS_URL = '/datasets'

export function listDatasets(): Promise<Dataset[]> {
  return request(DATASETS_URL)
}

export function createDataset(dataset: NewDataset): Promise<Dataset> {
  return request(DATASETS_URL, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(dataset),
  })
}

export function deleteDataset(id: string): Promise<Dataset> {
  return request(`${DATASETS_URL}/${encodeURIComponent(id)}`, { method: 'DELETE' })
}

export function getErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Something went wrong.'
}

async function request<T>(url: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(url, init)
  } catch {
    throw new Error('Could not reach the server. Check that the API is running.')
  }

  if (!response.ok) {
    const body: unknown = await response.json().catch(() => null)
    throw new Error(readDetail(body) ?? `Request failed with status ${response.status}.`)
  }
  return response.json()
}

// The API returns errors as {"detail": "<message>"}.
function readDetail(body: unknown): string | undefined {
  if (typeof body === 'object' && body !== null && 'detail' in body && typeof body.detail === 'string') {
    return body.detail
  }
  return undefined
}
