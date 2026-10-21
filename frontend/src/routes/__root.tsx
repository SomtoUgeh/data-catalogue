import { useEffect, useState, type ReactNode } from 'react'
import type { QueryClient } from '@tanstack/react-query'
import { HeadContent, Scripts, createRootRouteWithContext } from '@tanstack/react-router'

import appCss from '../styles.css?url'

export const Route = createRootRouteWithContext<{ queryClient: QueryClient }>()({
  head: () => ({
    meta: [
      {
        charSet: 'utf-8',
      },
      {
        name: 'viewport',
        content: 'width=device-width, initial-scale=1',
      },
      {
        title: 'Data catalogue',
      },
    ],
    links: [
      {
        rel: 'preconnect',
        href: 'https://fonts.googleapis.com',
      },
      {
        rel: 'preconnect',
        href: 'https://fonts.gstatic.com',
      },
      {
        rel: 'stylesheet',
        href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap',
      },
      {
        rel: 'stylesheet',
        href: appCss,
      },
    ],
  }),
  shellComponent: RootDocument,
})

function RootDocument({ children }: { children: ReactNode }) {
  return (
    <html lang="en" className="h-full">
      <head>
        <HeadContent />
      </head>
      <body className="min-h-svh bg-background font-sans antialiased">
        <MockingGate>{children}</MockingGate>
        <Scripts />
      </body>
    </html>
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
