import { createFileRoute } from '@tanstack/react-router'

import { CatalogueError } from '@/features/datasets/components/CatalogueError'
import { CataloguePage } from '@/features/datasets/components/CataloguePage'
import { CatalogueSkeleton } from '@/features/datasets/components/CatalogueSkeleton'
import { datasetsQueryOptions } from '@/features/datasets/api/queryOptions'

export const Route = createFileRoute('/')({
  // 'static' reuses any cached pages, so returning to the page does not wait on a refetch.
  // useSuspenseInfiniteQuery still refetches in the background once the data is stale.
  loader: ({ context }) =>
    context.queryClient.infiniteQuery({ ...datasetsQueryOptions(), staleTime: 'static' }),
  pendingComponent: CatalogueSkeleton,
  errorComponent: CatalogueError,
  component: CataloguePage,
})
