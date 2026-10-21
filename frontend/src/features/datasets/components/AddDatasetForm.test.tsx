import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse, delay } from 'msw'
import { describe, expect, it } from 'vitest'

import { getApiBaseUrl } from '@/lib/api-base'
import { renderWithQuery } from '@/test/render'
import { server } from '../mocks/server'
import { AddDatasetForm } from './AddDatasetForm'

describe('AddDatasetForm', () => {
  it('shows inline validation errors when name or description is empty', async () => {
    const user = userEvent.setup()
    renderWithQuery(<AddDatasetForm />)

    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByText('Name is required')).toBeInTheDocument()
    expect(screen.getByText('Description is required')).toBeInTheDocument()
  })

  it('surfaces a server 400 message on the matching field', async () => {
    const user = userEvent.setup()
    server.use(
      http.post(`${getApiBaseUrl()}/datasets`, () =>
        HttpResponse.json({ error: 'name is required and cannot be blank' }, { status: 400 }),
      ),
    )
    renderWithQuery(<AddDatasetForm />)

    await user.type(screen.getByLabelText('Name'), 'Trade Confirmations')
    await user.type(screen.getByLabelText('Description'), 'Daily export of confirmed trades.')
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByText('name is required and cannot be blank')).toBeInTheDocument()
  })

  it('shows a loading label while the request is in flight', async () => {
    const user = userEvent.setup()
    server.use(
      http.post(`${getApiBaseUrl()}/datasets`, async () => {
        await delay(150)
        return HttpResponse.json(
          {
            id: '4',
            name: 'Trade Confirmations',
            owner: 'Middle Office',
            description: 'Daily export of confirmed trades.',
            tags: ['trading', 'finance', 'settlements', 'daily'],
            summary: 'A daily export of confirmed trades covering counterparties and settlements.',
            curation_status: 'ok',
          },
          { status: 201 },
        )
      }),
    )
    renderWithQuery(<AddDatasetForm />)

    await user.type(screen.getByLabelText('Name'), 'Trade Confirmations')
    await user.type(screen.getByLabelText('Description'), 'Daily export of confirmed trades.')
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByRole('button', { name: 'Curating…' })).toBeDisabled()
    expect(await screen.findByRole('button', { name: 'Add dataset' })).toBeEnabled()
  })
})
