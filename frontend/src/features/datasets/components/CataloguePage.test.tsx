import { QueryClientProvider } from '@tanstack/react-query'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { http, HttpResponse } from 'msw'
import { describe, expect, it } from 'vitest'

import { createTestQueryClient } from '@/test/render'
import type { Dataset } from '../api/generated/types.gen'
import { datasetsQueryOptions, PAGE_SIZE } from '../api/queryOptions'
import { server } from '../mocks/server'
import { CataloguePage } from './CataloguePage'

async function renderCatalogue() {
  const queryClient = createTestQueryClient()
  await queryClient.ensureInfiniteQueryData(datasetsQueryOptions())
  const view = render(
    <QueryClientProvider client={queryClient}>
      <CataloguePage />
    </QueryClientProvider>,
  )
  return { ...view, queryClient }
}

function dataset(id: number): Dataset {
  return {
    id: String(id),
    name: `Feed ${id}`,
    owner: 'Middle Office',
    description: 'A daily feed.',
    tags: ['daily'],
    summary: 'A daily feed.',
    curation_status: 'ok',
  }
}

describe('CataloguePage', () => {
  it('renders the seeded dataset list', async () => {
    await renderCatalogue()

    expect(
      await screen.findByRole('heading', { name: 'Customer Transactions' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Product Inventory' })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Employee Directory' })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Delete Customer Transactions' })).toBeInTheDocument()
  })

  it('adds a dataset through the API and refreshes the list', async () => {
    const user = userEvent.setup()
    await renderCatalogue()

    await user.type(screen.getByLabelText('Name'), 'Trade Confirmations')
    await user.type(screen.getByLabelText('Owner (optional)'), 'Middle Office')
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
      expect(
        screen.queryByRole('heading', { name: 'Customer Transactions' }),
      ).not.toBeInTheDocument()
    })
    expect(screen.getByRole('heading', { name: 'Product Inventory' })).toBeInTheDocument()
  })

  it('shows at most five tags on a catalogue row', async () => {
    server.use(
      http.get('/datasets', () =>
        HttpResponse.json(
          [
            {
              id: '8',
              name: 'Trade Confirmations',
              owner: 'Middle Office',
              description: 'Daily export of confirmed trades.',
              tags: ['finance', 'trading', 'daily', 'transactions', 'settlements'],
              summary: 'A daily export of trade confirmations.',
              curation_status: 'ok',
            },
          ],
          { status: 200 },
        ),
      ),
    )
    await renderCatalogue()

    const tags = await screen.findByText(/^Tags:/)
    const labels = tags.textContent?.replace('Tags: ', '').split(', ') ?? []
    expect(labels).toHaveLength(5)
    expect(labels).toEqual(['finance', 'trading', 'daily', 'transactions', 'settlements'])
  })

  it('shows a failed-AI indicator on a row that saved without tags', async () => {
    server.use(
      http.get('/datasets', () =>
        HttpResponse.json(
          [
            {
              id: '9',
              name: 'Broken Feed',
              owner: 'Middle Office',
              description: 'A feed that could not be curated.',
              tags: [],
              summary: '',
              curation_status: 'failed',
            },
          ],
          { status: 200 },
        ),
      ),
    )
    await renderCatalogue()

    expect(await screen.findByRole('heading', { name: 'Broken Feed' })).toBeInTheDocument()
    expect(
      screen.getByText('AI curation failed. The dataset was saved without tags or a summary.'),
    ).toBeInTheDocument()
    expect(screen.queryByText(/^Tags:/)).not.toBeInTheDocument()
    expect(screen.queryByText('No tags matched this description.')).not.toBeInTheDocument()
  })

  it('shows a request error banner when delete fails', async () => {
    const user = userEvent.setup()
    server.use(
      http.delete('/datasets/:dataset_id', () =>
        HttpResponse.json({ error: "Dataset '1' not found" }, { status: 404 }),
      ),
    )
    await renderCatalogue()
    await user.click(screen.getByRole('button', { name: 'Delete Customer Transactions' }))

    expect(await screen.findByText("Dataset '1' not found")).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Customer Transactions' })).toBeInTheDocument()
  })

  it('says no tags matched when curation succeeded without tags', async () => {
    server.use(
      http.get('/datasets', () =>
        HttpResponse.json([{ ...dataset(10), tags: [], curation_status: 'ok' }]),
      ),
    )
    await renderCatalogue()

    expect(await screen.findByText('No tags matched this description.')).toBeInTheDocument()
    expect(screen.getByText('A daily feed.')).toBeInTheDocument()
    expect(screen.queryByText(/curation failed/i)).not.toBeInTheDocument()
  })

  it('says the tags were kept when only the summary failed', async () => {
    server.use(
      http.get('/datasets', () =>
        HttpResponse.json([{ ...dataset(9), summary: '', curation_status: 'failed' }]),
      ),
    )
    await renderCatalogue()

    expect(
      await screen.findByText('AI could not write a summary. The dataset and its tags were saved.'),
    ).toBeInTheDocument()
    expect(screen.getByText('Tags: daily')).toBeInTheDocument()
  })

  it('loads the next page of older datasets on request', async () => {
    const user = userEvent.setup()
    const newest = Array.from({ length: PAGE_SIZE }, (_, i) => dataset(100 - i))
    server.use(
      http.get('/datasets', ({ request }) => {
        const before = new URL(request.url).searchParams.get('before')
        return HttpResponse.json(before === '51' ? [dataset(7)] : newest)
      }),
    )
    await renderCatalogue()

    expect(screen.getByText(`Showing the newest ${PAGE_SIZE}`)).toBeInTheDocument()
    await user.click(screen.getByRole('button', { name: 'Load more datasets' }))

    expect(await screen.findByRole('heading', { name: 'Feed 7' })).toBeInTheDocument()
    expect(screen.getByText(`${PAGE_SIZE + 1} datasets`)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Load more datasets' })).not.toBeInTheDocument()
  })
})
