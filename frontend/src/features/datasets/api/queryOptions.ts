import { queryOptions } from '@tanstack/react-query'

import { listDatasetsQueryKey } from './generated/@tanstack/react-query.gen'
import { listDatasets } from './generated/sdk.gen'
import { unwrapResponse } from './errors'

export function datasetsQueryOptions() {
  return queryOptions({
    queryKey: listDatasetsQueryKey(),
    queryFn: ({ signal }) =>
      unwrapResponse(
        listDatasets({
          signal,
          throwOnError: false,
        }),
      ),
  })
}
