import type { Dataset } from './api/generated/types.gen'

export function curationBanner(dataset: Pick<Dataset, 'curation_status' | 'tags'>): string | null {
  if (dataset.curation_status !== 'failed') return null
  return dataset.tags.length > 0
    ? 'AI could not write a summary. The dataset and its tags were saved.'
    : 'AI curation failed. The dataset was saved without tags or a summary.'
}
