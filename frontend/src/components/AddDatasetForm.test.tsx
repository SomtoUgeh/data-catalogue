import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, expect, it, vi } from 'vitest'

import { AddDatasetForm } from './AddDatasetForm'
import { ApiError } from '../types'
import type { Dataset } from '../types'

const sample: Dataset = {
  id: '4',
  name: 'Trade Confirmations',
  owner: 'Middle Office',
  description: 'Daily export of confirmed trades.',
  tags: ['trading', 'finance', 'settlements', 'daily'],
  summary: 'A daily export of confirmed trades covering counterparties and settlements.',
  curation_status: 'ok',
}

describe('AddDatasetForm', () => {
  it('shows inline validation errors when name or description is empty', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn()
    render(<AddDatasetForm onSubmit={onSubmit} />)

    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByText('Name is required')).toBeInTheDocument()
    expect(screen.getByText('Description is required')).toBeInTheDocument()
    expect(onSubmit).not.toHaveBeenCalled()
  })

  it('surfaces a server 400 message on the matching field', async () => {
    const user = userEvent.setup()
    const onSubmit = vi.fn().mockRejectedValue(new ApiError('name is required and cannot be blank', 400))
    render(<AddDatasetForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText('Name'), 'Trade Confirmations')
    await user.type(screen.getByLabelText('Description'), 'Daily export of confirmed trades.')
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByText('name is required and cannot be blank')).toBeInTheDocument()
  })

  it('shows a loading label while the request is in flight', async () => {
    const user = userEvent.setup()
    let resolveSubmit: (value: Dataset) => void = () => undefined
    const onSubmit = vi.fn(
      () =>
        new Promise<Dataset>((resolve) => {
          resolveSubmit = resolve
        }),
    )
    render(<AddDatasetForm onSubmit={onSubmit} />)

    await user.type(screen.getByLabelText('Name'), 'Trade Confirmations')
    await user.type(screen.getByLabelText('Description'), 'Daily export of confirmed trades.')
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByRole('button', { name: 'Saving dataset…' })).toBeDisabled()
    resolveSubmit(sample)
    expect(await screen.findByRole('button', { name: 'Add dataset' })).toBeEnabled()
  })
})
