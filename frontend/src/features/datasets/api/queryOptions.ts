// The list query, shared by the route loader, CataloguePage, and the mutations that invalidate it.
import { infiniteQueryOptions } from '@tanstack/react-query'

import { listDatasetsInfiniteQueryKey } from './generated/@tanstack/react-query.gen'
import { listDatasets } from './generated/sdk.gen'
import { unwrapResponse } from './errors'

export const PAGE_SIZE = 50

/** The first page has no cursor. Each later page asks for datasets older than the last one shown. */
const FIRST_PAGE: string | null = null

/** Pages of datasets, newest first. A page shorter than PAGE_SIZE is the last one. */
export function datasetsQueryOptions() {
  return infiniteQueryOptions({
    queryKey: listDatasetsInfiniteQueryKey({ query: { limit: PAGE_SIZE } }),
    queryFn: ({ pageParam, signal }) =>
      unwrapResponse(
        listDatasets({
          query: { limit: PAGE_SIZE, before: pageParam },
          signal,
          throwOnError: false,
        }),
      ),
    initialPageParam: FIRST_PAGE,
    getNextPageParam: (lastPage) =>
      lastPage.length < PAGE_SIZE ? null : (lastPage.at(-1)?.id ?? null),
  })
}
