import { useMutation, useQueryClient } from '@tanstack/react-query'

import { createDataset, deleteDataset } from './generated/sdk.gen'
import type { DatasetCreate } from './generated/types.gen'
import { unwrapResponse } from './errors'
import { datasetsQueryOptions } from './queryOptions'

export function useCreateDatasetMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (body: DatasetCreate) =>
      unwrapResponse(
        createDataset({
          body,
          throwOnError: false,
        }),
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: datasetsQueryOptions().queryKey })
    },
  })
}

export function useDeleteDatasetMutation() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (datasetId: string) =>
      unwrapResponse(
        deleteDataset({
          path: { dataset_id: datasetId },
          throwOnError: false,
        }),
      ),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: datasetsQueryOptions().queryKey })
    },
  })
}
