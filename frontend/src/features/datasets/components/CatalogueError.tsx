import type { ErrorComponentProps } from '@tanstack/react-router'

import { PageShell } from '@/components/page-shell'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { CatalogueHeader } from './CatalogueHeader'

export function CatalogueError({ error }: ErrorComponentProps) {
  const message = error instanceof Error ? error.message : 'Could not load datasets.'
  return (
    <PageShell>
      <CatalogueHeader />
      <Alert variant="destructive">
        <AlertTitle>Could not load datasets</AlertTitle>
        <AlertDescription aria-live="assertive">
          {message || 'Could not load datasets.'}
        </AlertDescription>
      </Alert>
    </PageShell>
  )
}
