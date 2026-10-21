import { render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { App } from './App'
import type { Dataset } from './types'

const seeded: Dataset[] = [
  {
    id: '1',
    name: 'Customer Transactions',
    owner: 'Finance Team',
    description: 'Contains daily transaction records.',
    tags: ['finance', 'transactions', 'PII', 'daily'],
    summary: 'A daily feed of customer transaction records covering amounts, currencies, and timestamps.',
    curation_status: 'ok',
  },
  {
    id: '2',
    name: 'Product Inventory',
    owner: 'Operations Team',
    description: 'Snapshot of warehouse stock levels by SKU.',
    tags: ['inventory', 'operations', 'warehouse'],
    summary: 'A warehouse snapshot tracking stock levels and reorder thresholds per product SKU.',
    curation_status: 'ok',
  },
]

const tradeInput = {
  name: 'Trade Confirmations',
  owner: 'Middle Office',
  description: 'Daily export of confirmed trades including instrument type, counterparty, notional value, and settlement date.',
}

const trade: Dataset = {
  id: '4',
  ...tradeInput,
  tags: ['trading', 'finance', 'settlements', 'daily'],
  summary: 'A daily trading dataset covering instrument type, counterparty, notional value, and settlement date.',
  curation_status: 'ok',
}

const fetchMock = vi.fn<typeof fetch>()

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

async function renderWithDatasets(datasets: Dataset[] = seeded) {
  fetchMock.mockResolvedValueOnce(jsonResponse(200, datasets))
  render(<App />)
  await screen.findByRole('table')
}

async function fillForm(input: typeof tradeInput) {
  const user = userEvent.setup()
  await user.type(screen.getByLabelText('Name'), input.name)
  await user.type(screen.getByLabelText('Owner'), input.owner)
  await user.type(screen.getByLabelText('Description'), input.description)
  return user
}

beforeEach(() => {
  fetchMock.mockReset()
  vi.stubGlobal('fetch', fetchMock)
})

describe('App', () => {
  it('lists the datasets returned by the API', async () => {
    await renderWithDatasets()

    const rows = within(screen.getByRole('table')).getAllByRole('row').slice(1)
    expect(rows.map((row) => within(row).getByRole('rowheader').textContent)).toEqual([
      'Customer Transactions',
      'Product Inventory',
    ])
    expect(screen.getByRole('row', { name: /Customer Transactions/ })).toHaveTextContent(
      'finance, transactions, PII, daily',
    )
  })

  it('shows an error when the datasets cannot be loaded', async () => {
    fetchMock.mockRejectedValueOnce(new TypeError('Failed to fetch'))
    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not reach the server')
  })

  it('shows inline errors and does not call the API when name or description is empty', async () => {
    await renderWithDatasets()
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(screen.getByLabelText('Name')).toHaveAccessibleDescription('Name is required.')
    expect(screen.getByLabelText('Description')).toHaveAccessibleDescription('Description is required.')
    expect(screen.getByLabelText('Name')).toHaveFocus()
    expect(fetchMock).toHaveBeenCalledTimes(1)
  })

  it('saves a dataset, shows a loading state, and adds the curated row to the list', async () => {
    await renderWithDatasets()
    let respond: (response: Response) => void = () => {}
    fetchMock.mockReturnValueOnce(new Promise((resolve) => (respond = resolve)))
    const user = await fillForm(tradeInput)

    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(screen.getByRole('button', { name: 'Saving and curating…' })).toBeDisabled()
    expect(fetchMock).toHaveBeenLastCalledWith('/datasets', expect.objectContaining({ method: 'POST', body: JSON.stringify(tradeInput) }))

    respond(jsonResponse(201, trade))

    const row = await screen.findByRole('row', { name: /Trade Confirmations/ })
    expect(row).toHaveTextContent('trading, finance, settlements, daily')
    expect(row).toHaveTextContent(trade.summary)
    expect(screen.getByLabelText('Name')).toHaveValue('')
    expect(screen.getByRole('button', { name: 'Add dataset' })).toBeEnabled()
  })

  it('tells the user when the dataset saved but curation failed', async () => {
    await renderWithDatasets()
    fetchMock.mockResolvedValueOnce(jsonResponse(201, { ...trade, tags: [], summary: '', curation_status: 'failed' }))
    const user = await fillForm(tradeInput)

    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByRole('status')).toHaveTextContent('AI curation failed')
    expect(screen.getByRole('row', { name: /Trade Confirmations/ })).toHaveTextContent('AI curation failed')
  })

  it('shows the API error message when saving fails', async () => {
    await renderWithDatasets()
    fetchMock.mockResolvedValueOnce(jsonResponse(400, { detail: 'name is required' }))
    const user = await fillForm(tradeInput)

    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Could not save the dataset. name is required')
    expect(screen.getByLabelText('Name')).toHaveValue(tradeInput.name)
  })

  it('removes a dataset from the list after it is deleted', async () => {
    await renderWithDatasets()
    fetchMock.mockResolvedValueOnce(jsonResponse(200, seeded[0]))
    const user = userEvent.setup()

    await user.click(screen.getByRole('button', { name: 'Delete Customer Transactions' }))

    expect(fetchMock).toHaveBeenLastCalledWith('/datasets/1', { method: 'DELETE' })
    expect(screen.queryByRole('row', { name: /Customer Transactions/ })).not.toBeInTheDocument()
    expect(screen.getByRole('row', { name: /Product Inventory/ })).toBeInTheDocument()
  })
})
