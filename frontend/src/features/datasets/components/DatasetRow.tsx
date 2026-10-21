import { StatusBanner } from '@/components/status-banner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import type { Dataset } from '../api/generated/types.gen'
import { curationBanner } from '../curationBanner'
import { DatasetOwner } from './DatasetOwner'
import { DatasetTags } from './DatasetTags'

type DatasetRowProps = {
  dataset: Dataset
  isDeleting: boolean
  onDelete: (id: string) => void
}

export function DatasetRow({ dataset, isDeleting, onDelete }: DatasetRowProps) {
  const banner = curationBanner(dataset)
  return (
    <article>
      <Card size="sm">
        <CardHeader>
          <div className="flex items-start justify-between gap-3">
            <div className="flex min-w-0 flex-col gap-2">
              <h3 className="text-base leading-snug font-medium tracking-tight">{dataset.name}</h3>
              <DatasetOwner owner={dataset.owner} />
            </div>
            <Button
              type="button"
              variant="outline"
              size="sm"
              disabled={isDeleting}
              onClick={() => onDelete(dataset.id)}
            >
              {isDeleting ? (
                <>
                  <Spinner data-icon="inline-start" aria-hidden />
                  Deleting…
                </>
              ) : (
                `Delete ${dataset.name}`
              )}
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex flex-col gap-3">
          <DatasetTags tags={dataset.tags} />
          {dataset.summary ? (
            <p className="text-sm text-muted-foreground">{dataset.summary}</p>
          ) : null}
          {banner ? <StatusBanner tone="warning">{banner}</StatusBanner> : null}
        </CardContent>
      </Card>
    </article>
  )
}
