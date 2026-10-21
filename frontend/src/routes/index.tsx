// The only page. The loader fetches the first page of datasets before render; CatalogueSkeleton shows
// while it loads and CatalogueError if it fails.
import { createFileRoute } from '@tanstack/react-router'

import { CatalogueError } from '@/features/datasets/components/CatalogueError'
import { CataloguePage } from '@/features/datasets/components/CataloguePage'
import { CatalogueSkeleton } from '@/features/datasets/components/CatalogueSkeleton'
import { datasetsQueryOptions } from '@/features/datasets/api/queryOptions'

export const Route = createFileRoute('/')({
  loader: ({ context }) => context.queryClient.ensureInfiniteQueryData(datasetsQueryOptions()),
  pendingComponent: CatalogueSkeleton,
  errorComponent: CatalogueError,
  component: CataloguePage,
})
