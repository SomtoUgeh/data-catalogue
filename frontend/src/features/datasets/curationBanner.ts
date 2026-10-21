import type { Dataset } from './api/generated/types.gen'

export function curationBanner(dataset: Pick<Dataset, 'curation_status'>): string | null {
  return dataset.curation_status === 'failed'
    ? 'AI curation failed. The dataset was still saved.'
    : null
}
