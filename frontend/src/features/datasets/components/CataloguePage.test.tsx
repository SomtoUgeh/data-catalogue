import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { getApiBaseUrl } from '@/lib/api-base'
import { createTestQueryClient } from '@/test/render'
import { datasetsQueryOptions } from '../api/queryOptions'
import { server } from '../mocks/server'
import { CataloguePage } from './CataloguePage'

async function renderCatalogue() {
  const queryClient = createTestQueryClient()
  await queryClient.ensureQueryData(datasetsQueryOptions())
  const view = render(
    <QueryClientProvider client={queryClient}>
      <CataloguePage />
    </QueryClientProvider>,
  )
  return { ...view, queryClient }
}

describe('CataloguePage', () => {
  it('renders the seeded dataset list', async () => {
    await renderCatalogue()

    expect(await screen.findByRole('heading', { name: 'Customer Transactions' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Product Inventory' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Employee Directory' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete Customer Transactions' })).toBeInTheDocument()
  })

  it('adds a dataset through the API and refreshes the list', async () => {
    const user = userEvent.setup()
    await renderCatalogue()

    await user.type(screen.getByLabelText('Name'), 'Trade Confirmations')
    await user.type(screen.getByLabelText('Owner'), 'Middle Office')
    await user.type(
      screen.getByLabelText('Description'),
      'Daily export of confirmed trades including instrument type, counterparty, notional value, and settlement date.',
    )
    await user.click(screen.getByRole('button', { name: 'Add dataset' }))

    expect(await screen.findByRole('heading', { name: 'Trade Confirmations' })).toBeInTheDocument()
    expect(screen.getByText(/trading, finance, settlements, daily/)).toBeInTheDocument()
  })

  it('deletes a dataset through the API without a reload', async () => {
    const user = userEvent.setup()
    await renderCatalogue()

    await user.click(screen.getByRole('button', { name: 'Delete Customer Transactions' }))

    await waitFor(() => {
      expect(screen.queryByRole('heading', { name: 'Customer Transactions' })).not.toBeInTheDocument()
    })
    expect(screen.getByRole('heading', { name: 'Product Inventory' })).toBeInTheDocument()
  })

  it('shows a failed-AI indicator on a row that saved without tags', async () => {
    server.use(
      http.get(`${getApiBaseUrl()}/datasets`, () =>
        HttpResponse.json(
          [
            {
              id: '9',
              name: 'Broken Feed',
              owner: 'Middle Office',
              description: 'A feed that could not be curated.',
              tags: [],
              summary: 'Curation unavailable. Tags and summary will appear once tagging succeeds.',
              curation_status: 'failed',
            },
          ],
          { status: 200 },
        ),
      ),
    )
    await renderCatalogue()

    expect(await screen.findByRole('heading', { name: 'Broken Feed' })).toBeInTheDocument()
    expect(screen.getByText('AI curation failed. The dataset was still saved.')).toBeInTheDocument()
  })

  it('shows a request error banner when delete fails', async () => {
    const user = userEvent.setup()
    server.use(
      http.delete(`${getApiBaseUrl()}/datasets/:dataset_id`, () =>
        HttpResponse.json({ error: "Dataset with id '1' was not found." }, { status: 404 }),
      ),
    )
    await renderCatalogue()
    await user.click(screen.getByRole('button', { name: 'Delete Customer Transactions' }))

    expect(await screen.findByRole('alert')).toHaveTextContent("Dataset with id '1' was not found.")
  })
})
