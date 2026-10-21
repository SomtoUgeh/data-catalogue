import type { Dataset } from '../api/generated/types.gen'

export const PLACEHOLDER_TAGS = ['uncurated']
export const PLACEHOLDER_SUMMARY =
  'Curation unavailable. Tags and summary will appear once tagging succeeds.'

export const SEEDED_DATASETS: Dataset[] = [
  {
    id: '1',
    name: 'Customer Transactions',
    owner: 'Finance Team',
    description:
      'Contains daily transaction records including transaction ID, customer ID, amount, currency, and timestamp.',
    tags: ['finance', 'transactions', 'PII', 'daily'],
    summary: 'A daily feed of customer transaction records covering amounts, currencies, and timestamps.',
    curation_status: 'ok',
  },
  {
    id: '2',
    name: 'Product Inventory',
    owner: 'Operations Team',
    description:
      'Snapshot of warehouse stock levels by SKU, including product name, quantity on hand, and reorder threshold.',
    tags: ['inventory', 'operations', 'warehouse'],
    summary: 'A warehouse snapshot tracking stock levels and reorder thresholds per product SKU.',
    curation_status: 'ok',
  },
  {
    id: '3',
    name: 'Employee Directory',
    owner: 'HR Team',
    description:
      'List of current employees with name, department, role, and office location. Updated weekly.',
    tags: ['HR', 'PII', 'employees', 'weekly'],
    summary: 'A weekly-refreshed directory of employees including role, department, and location.',
    curation_status: 'ok',
  },
]
