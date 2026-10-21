import { useRouter, type ErrorComponentProps } from '@tanstack/react-router'

import { PageShell } from '@/components/page-shell'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { getErrorMessage } from '../api/errors'
import { CatalogueHeader } from './CatalogueHeader'

export function CatalogueError({ error }: ErrorComponentProps) {
  const router = useRouter()
  return (
    <PageShell>
      <CatalogueHeader />
      <Alert variant="destructive">
        <AlertTitle>Could not load datasets</AlertTitle>
        <AlertDescription className="flex flex-col items-start gap-2">
          {getErrorMessage(error)}
          {/* invalidate() reruns the route loader, which refetches the list. */}
          <Button
            type="button"
            variant="outline"
            size="sm"
            onClick={() => void router.invalidate()}
          >
            Try again
          </Button>
        </AlertDescription>
      </Alert>
    </PageShell>
  )
}
