import { useState } from 'react'

import { getErrorMessage } from '../services/datasetsApi'
import type { Dataset } from '../types'

type DatasetRowProps = {
  dataset: Dataset
  onDelete: (id: string) => Promise<void>
}

export function DatasetRow({ dataset, onDelete }: DatasetRowProps) {
  const [isDeleting, setIsDeleting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleDelete() {
    setIsDeleting(true)
    setError(null)
    try {
      await onDelete(dataset.id)
    } catch (deleteError) {
      setError(`Could not delete. ${getErrorMessage(deleteError)}`)
      setIsDeleting(false)
    }
  }

  return (
    <tr>
      <th scope="row">{dataset.name}</th>
      <td>{dataset.owner || '—'}</td>
      {dataset.curation_status === 'failed' ? (
        <td colSpan={2}>AI curation failed for this dataset, so it has no tags or summary.</td>
      ) : (
        <>
          <td>{dataset.tags.join(', ')}</td>
          <td>{dataset.summary}</td>
        </>
      )}
      <td>
        <button type="button" onClick={handleDelete} disabled={isDeleting} aria-label={`Delete ${dataset.name}`}>
          {isDeleting ? 'Deleting…' : 'Delete'}
        </button>
        {error && (
          <p role="alert" className="error">
            {error}
          </p>
        )}
      </td>
    </tr>
  )
}
