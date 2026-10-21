import { screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse, delay } from 'msw'
import { describe, expect, it } from 'vitest'

import { renderWithQuery } from '@/test/render'
import { server } from '../mocks/server'
import { AddDatasetForm } from './AddDatasetForm'

const TRADE_CONFIRMATIONS = {
  id: '4',
  name: 'Trade Confirmations',
  owner: '',
  description: 'Daily export of confirmed trades.',
  tags: ['trading', 'finance', 'settlements', 'daily'],
  summary: 'A daily export of confirmed trades covering counterparties and settlements.',
  curation_status: 'ok',
}

async function fillRequiredFields(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText('Name'), 'Trade Confirmations')
  await user.type(screen.getByLabelText('Description'), 'Daily export of confirmed trades.')
}

describe('AddDatasetForm', () => {
  it('shows the required-field errors and focuses Name when submitted empty', async () => {
    const user = userEvent.setup()
    renderWithQuery(<AddDatasetForm />)

    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByText('Name is required')).toBeInTheDocument()
    expect(screen.getByText('Description is required')).toBeInTheDocument()
    expect(screen.queryByText(/Owner/, { selector: 'p' })).not.toBeInTheDocument()
    expect(screen.getByLabelText('Name')).toHaveFocus()
    expect(screen.getByLabelText('Name')).toHaveAccessibleDescription('Name is required')
  })

  it('does not show errors for fields the user has not reached', async () => {
    const user = userEvent.setup()
    renderWithQuery(<AddDatasetForm />)

    await user.type(screen.getByLabelText('Name'), 'T')

    expect(screen.queryByText('Description is required')).not.toBeInTheDocument()
  })

  it('shows the error once the user leaves a required field empty', async () => {
    const user = userEvent.setup()
    renderWithQuery(<AddDatasetForm />)

    await user.click(screen.getByLabelText('Name'))
    await user.tab()

    expect(await screen.findByText('Name is required')).toBeInTheDocument()
  })

  it('saves a dataset without an owner and clears the form', async () => {
    const user = userEvent.setup()
    renderWithQuery(<AddDatasetForm />)

    await fillRequiredFields(user)
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByRole('button', { name: 'Add dataset' })).toBeEnabled()
    expect(screen.getByLabelText('Name')).toHaveValue('')
  })

  it('shows a server 400 message on the matching field and focuses it', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/datasets', () =>
        HttpResponse.json(
          {
            error: 'Validation failed',
            fields: [
              { field: 'description', message: 'description must be at most 2000 characters' },
            ],
          },
          { status: 400 },
        ),
      ),
    )
    renderWithQuery(<AddDatasetForm />)

    await fillRequiredFields(user)
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(
      await screen.findByText('description must be at most 2000 characters'),
    ).toBeInTheDocument()
    expect(screen.getByLabelText('Description')).toHaveFocus()
  })

  it('announces a request error that is not about a field', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/datasets', () =>
        HttpResponse.json({ error: 'Too many requests. Try again in a minute.' }, { status: 429 }),
      ),
    )
    renderWithQuery(<AddDatasetForm />)

    await fillRequiredFields(user)
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Too many requests. Try again in a minute.',
    )
  })

  it('shows a loading label while the request is in flight', async () => {
    const user = userEvent.setup()
    server.use(
      http.post('/datasets', async () => {
        await delay(150)
        return HttpResponse.json(TRADE_CONFIRMATIONS, { status: 201 })
      }),
    )
    renderWithQuery(<AddDatasetForm />)

    await fillRequiredFields(user)
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByRole('button', { name: 'Curating…' })).toBeDisabled()
    expect(await screen.findByRole('button', { name: 'Add dataset' })).toBeEnabled()
  })
})
