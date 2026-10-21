import type { Dataset } from '../types'

type DatasetRowProps = {
  dataset: Dataset
  onDelete: (id: string) => Promise<void>
}

export function DatasetRow({ dataset, onDelete }: DatasetRowProps) {
  return (
    <article className="dataset-row">
      <header>
        <h3>{dataset.name}</h3>
        <p className="owner">Owner: {dataset.owner || 'Unassigned'}</p>
      </header>
      <p className="tags">
        <span className="sr-only">Tags: </span>
        {dataset.tags.join(', ')}
      </p>
      <p>{dataset.summary}</p>
      {dataset.curation_status === 'failed' ? (
        <p className="banner banner-warning" role="status">
          Curation fell back to placeholders for this dataset.
        </p>
      ) : null}
      <button type="button" onClick={() => void onDelete(dataset.id)}>
        {`Delete ${dataset.name}`}
      </button>
    </article>
  )
}
