import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { render, type RenderOptions } from '@testing-library/react'
import { Suspense, type ReactNode } from 'react'

export function createTestQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0 },
      mutations: { retry: false },
    },
  })
}

export function renderWithQuery(ui: ReactNode, options?: Omit<RenderOptions, 'wrapper'>) {
  const queryClient = createTestQueryClient()
  const view = render(
    <QueryClientProvider client={queryClient}>
      <Suspense fallback={<p>Loading datasets…</p>}>{ui}</Suspense>
    </QueryClientProvider>,
    options,
  )
  return { ...view, queryClient }
}
