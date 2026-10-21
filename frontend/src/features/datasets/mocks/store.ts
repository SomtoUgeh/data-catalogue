import type { Dataset, DatasetCreate } from '../api/generated/types.gen'
import { PLACEHOLDER_SUMMARY, PLACEHOLDER_TAGS, SEEDED_DATASETS } from './fixtures'

const KEYWORD_RULES: Array<[string, string[]]> = [
  ['trading', ['trade', 'trading', 'counterparty', 'notional', 'instrument']],
  ['finance', ['finance', 'currency', 'amount', 'notional', 'transaction', 'transactions']],
  ['settlements', ['settlement', 'settlements', 'settle']],
  ['transactions', ['transaction', 'transactions']],
  ['inventory', ['inventory', 'sku', 'stock', 'reorder']],
  ['warehouse', ['warehouse']],
  ['operations', ['operations', 'warehouse', 'ops']],
  ['HR', ['employee', 'employees', 'hr', 'department']],
  ['employees', ['employee', 'employees']],
  ['daily', ['daily']],
  ['weekly', ['weekly']],
  ['monthly', ['monthly']],
]

let items: Dataset[] = cloneSeed()
let nextId = 4

function cloneSeed(): Dataset[] {
  return SEEDED_DATASETS.map((item) => ({ ...item, tags: [...item.tags] }))
}

export function resetDatasetStore() {
  items = cloneSeed()
  nextId = 4
}

export function listStoredDatasets(): Dataset[] {
  return items.map((item) => ({ ...item, tags: [...item.tags] }))
}

export function curateDataset(payload: DatasetCreate): Pick<Dataset, 'tags' | 'summary'> {
  const haystack = `${payload.name} ${payload.description}`.toLowerCase()
  const words = new Set(haystack.match(/[a-z0-9]+/g) ?? [])
  const tags: string[] = []

  for (const [tag, keywords] of KEYWORD_RULES) {
    if (keywords.some((keyword) => words.has(keyword)) && !tags.includes(tag)) {
      tags.push(tag)
    }
  }

  if (/\bcustomer id\b|\bpii\b|\bemployees?\b.*\bname\b/.test(haystack) && !tags.includes('PII')) {
    tags.push('PII')
  }

  while (tags.length < 3) {
    for (const extra of ['catalogue', 'dataset', 'uncategorised']) {
      if (!tags.includes(extra)) tags.push(extra)
      if (tags.length === 3) break
    }
  }

  const firstClause = payload.description.trim().split('.')[0]?.trim() || payload.name
  const cadence = tags.find((tag) => tag === 'daily' || tag === 'weekly' || tag === 'monthly')
  const lowered = firstClause ? firstClause[0].toLowerCase() + firstClause.slice(1) : payload.name
  const summary = cadence
    ? lowered.startsWith(cadence)
      ? `A ${lowered}.`
      : `A ${cadence} catalogue entry for ${payload.name}: ${firstClause}.`
    : `A catalogue entry for ${payload.name}: ${firstClause}.`

  return { tags: tags.slice(0, 6), summary }
}

export function createStoredDataset(payload: DatasetCreate, failed = false): Dataset {
  const curated = failed
    ? { tags: [...PLACEHOLDER_TAGS], summary: PLACEHOLDER_SUMMARY }
    : curateDataset(payload)
  const dataset: Dataset = {
    id: String(nextId),
    name: payload.name,
    owner: payload.owner ?? '',
    description: payload.description,
    tags: curated.tags,
    summary: curated.summary,
    curation_status: failed ? 'failed' : 'ok',
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
