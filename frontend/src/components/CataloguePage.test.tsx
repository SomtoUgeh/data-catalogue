import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { CataloguePage } from './CataloguePage'
import { ApiError } from '../types'
import type { Dataset } from '../types'

const seeded: Dataset[] = [
  {
    id: '1',
    name: 'Customer Transactions',
    owner: 'Finance Team',
    description: 'Contains daily transaction records.',
    tags: ['finance', 'transactions', 'PII', 'daily'],
    summary: 'A daily feed of customer transaction records.',
    curation_status: 'ok',
  },
  {
    id: '2',
    name: 'Product Inventory',
    owner: 'Operations Team',
    description: 'Snapshot of warehouse stock levels.',
    tags: ['inventory', 'operations', 'warehouse'],
    summary: 'A warehouse snapshot tracking stock levels.',
    curation_status: 'ok',
  },
  {
    id: '3',
    name: 'Employee Directory',
    owner: 'HR Team',
    description: 'List of current employees.',
    tags: ['HR', 'PII', 'employees', 'weekly'],
    summary: 'A weekly-refreshed directory of employees.',
    curation_status: 'ok',
  },
]

const created: Dataset = {
  id: '4',
  name: 'Trade Confirmations',
  owner: 'Middle Office',
  description: 'Daily export of confirmed trades.',
  tags: ['trading', 'finance', 'settlements', 'daily'],
  summary: 'A daily export of confirmed trades covering counterparties and settlements.',
  curation_status: 'ok',
}

const createDataset = vi.fn()
const deleteDataset = vi.fn()

vi.mock('../api/datasets', () => ({
  createDataset: (...args: unknown[]) => createDataset(...args),
  deleteDataset: (...args: unknown[]) => deleteDataset(...args),
}))

describe('CataloguePage', () => {
  beforeEach(() => {
    createDataset.mockReset()
    deleteDataset.mockReset()
  })

  it('renders the seeded dataset list', () => {
    render(<CataloguePage datasets={seeded} onChanged={vi.fn()} />)

    expect(screen.getByRole('heading', { name: 'Customer Transactions' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Product Inventory' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Employee Directory' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete Customer Transactions' })).toBeInTheDocument()
  })

  it('adds a dataset through the API module and refreshes the list', async () => {
    const user = userEvent.setup()
    const onChanged = vi.fn().mockResolvedValue(undefined)
    createDataset.mockResolvedValue(created)

    const { rerender } = render(<CataloguePage datasets={seeded} onChanged={onChanged} />)

    await user.type(screen.getByLabelText('Name'), created.name)
    await user.type(screen.getByLabelText('Owner'), created.owner)
    await user.type(screen.getByLabelText('Description'), created.description)
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(createDataset).toHaveBeenCalledWith({
      name: created.name,
      owner: created.owner,
      description: created.description,
    })
    expect(onChanged).toHaveBeenCalled()

    rerender(<CataloguePage datasets={[...seeded, created]} onChanged={onChanged} />)
    expect(screen.getByRole('heading', { name: 'Trade Confirmations' })).toBeInTheDocument()
    expect(screen.getByText(/trading, finance, settlements, daily/)).toBeInTheDocument()
  })

  it('deletes a dataset through the API module without a reload', async () => {
    const user = userEvent.setup()
    const onChanged = vi.fn().mockResolvedValue(undefined)
    deleteDataset.mockResolvedValue(seeded[0])

    const { rerender } = render(<CataloguePage datasets={seeded} onChanged={onChanged} />)
    await user.click(screen.getByRole('button', { name: 'Delete Customer Transactions' }))

    expect(deleteDataset).toHaveBeenCalledWith('1')
    expect(onChanged).toHaveBeenCalled()

    rerender(<CataloguePage datasets={seeded.slice(1)} onChanged={onChanged} />)
    expect(screen.queryByRole('heading', { name: 'Customer Transactions' })).not.toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Product Inventory' })).toBeInTheDocument()
  })

  it('shows a request error banner when delete fails', async () => {
    const user = userEvent.setup()
    deleteDataset.mockRejectedValue(new ApiError('Dataset with id \'1\' was not found.', 404))

    render(<CataloguePage datasets={seeded} onChanged={vi.fn()} />)
    await user.click(screen.getByRole('button', { name: 'Delete Customer Transactions' }))

    expect(await screen.findByRole('alert')).toHaveTextContent("Dataset with id '1' was not found.")
  })
})
