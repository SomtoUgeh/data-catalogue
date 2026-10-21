import { PageShell } from '@/components/page-shell'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { CatalogueHeader } from './CatalogueHeader'

export function CatalogueError({ error }: { error: Error }) {
  return (
    <PageShell>
      <CatalogueHeader />
      <Alert variant="destructive">
        <AlertTitle>Could not load datasets</AlertTitle>
        <AlertDescription aria-live="assertive">
          {error.message || 'Could not load datasets.'}
        </AlertDescription>
      </Alert>
    </PageShell>
  )
}
