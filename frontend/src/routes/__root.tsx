import { useEffect, useState, type ReactNode } from 'react'
import type { QueryClient } from '@tanstack/react-query'
import { Outlet, createRootRouteWithContext } from '@tanstack/react-router'

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  component: RootComponent,
})

function RootComponent() {
  return (
    <MockingGate>
      <Outlet />
    </MockingGate>
  )
}

function MockingGate({ children }: { children: ReactNode }) {
  const [ready, setReady] = useState(() => import.meta.env.VITE_API_MOCKING !== 'true')

  useEffect(() => {
    if (import.meta.env.VITE_API_MOCKING !== 'true') return
    let cancelled = false
    void import('@/features/datasets/mocks/browser').then(({ worker }) =>
      worker.start({ onUnhandledRequest: 'bypass' }).then(() => {
        if (!cancelled) setReady(true)
      }),
    )
    return () => {
      cancelled = true
    }
  }, [])

  if (!ready) {
    return (
      <p className="sr-only" aria-live="polite">
        Loading datasets…
      </p>
    )
  }

  return children
}
