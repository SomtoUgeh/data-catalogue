import { PageShell } from '@/components/page-shell'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { CatalogueHeader } from './CatalogueHeader'

export function CatalogueSkeleton() {
  return (
    <PageShell>
      <CatalogueHeader />
      <p className="sr-only" aria-live="polite">
        Loading datasets…
      </p>
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(20rem,24rem)_minmax(0,1fr)]">
        <Card>
          <CardHeader className="flex flex-col gap-2">
            <Skeleton className="h-5 w-28" />
            <Skeleton className="h-4 w-52" />
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-16 w-full" />
            <Skeleton className="h-8 w-24" />
          </CardContent>
        </Card>
        <div className="flex flex-col gap-3">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
          <Skeleton className="h-28 w-full" />
        </div>
      </div>
    </PageShell>
  )
}
