import type { Dataset } from './api/generated/types.gen'

export function curationBanner(dataset: Pick<Dataset, 'curation_status' | 'tags'>): string | null {
  if (dataset.curation_status === 'failed') {
    return 'AI curation failed. The dataset was still saved.'
  }
  if (dataset.curation_status === 'partial') {
    return dataset.tags.length
      ? 'Summary could not be generated. The tags were saved.'
      : 'Tags could not be generated. The summary was saved.'
  }
  return null
}
