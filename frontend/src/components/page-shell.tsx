import type { ReactNode } from 'react'

export function PageShell({ children }: { children: ReactNode }) {
  return (
    <main className="mx-auto flex w-full max-w-6xl flex-col gap-8 px-4 py-8 md:px-6 lg:py-10">
      {children}
    </main>
  )
}
