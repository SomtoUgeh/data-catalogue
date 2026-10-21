import { useState, type FormEvent } from 'react'

import { getErrorMessage } from '../services/datasetsApi'
import type { Dataset, NewDataset } from '../types'
import { TextField } from './TextField'

type DatasetFormProps = {
  onCreate: (dataset: NewDataset) => Promise<Dataset>
}

type FieldErrors = Partial<Record<keyof NewDataset, string>>

const EMPTY_FORM: NewDataset = { name: '', owner: '', description: '' }

function validate(values: NewDataset): FieldErrors {
  const errors: FieldErrors = {}
  if (!values.name.trim()) errors.name = 'Name is required.'
  if (!values.description.trim()) errors.description = 'Description is required.'
  return errors
}

export function DatasetForm({ onCreate }: DatasetFormProps) {
  const [values, setValues] = useState<NewDataset>(EMPTY_FORM)
  const [errors, setErrors] = useState<FieldErrors>({})
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [notice, setNotice] = useState<string | null>(null)

  function setField(field: keyof NewDataset) {
    return (value: string) => setValues((current) => ({ ...current, [field]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitError(null)
    setNotice(null)

    const fieldErrors = validate(values)
    setErrors(fieldErrors)
    const firstInvalid = Object.keys(fieldErrors)[0]
    if (firstInvalid) {
      const input = event.currentTarget.elements.namedItem(firstInvalid)
      if (input instanceof HTMLElement) input.focus()
      return
    }

    setIsSubmitting(true)
    try {
      const created = await onCreate(values)
      setValues(EMPTY_FORM)
      setNotice(
        created.curation_status === 'failed'
          ? `Saved "${created.name}", but AI curation failed, so it has no tags or summary.`
          : `Saved "${created.name}".`,
      )
    } catch (error) {
      setSubmitError(`Could not save the dataset. ${getErrorMessage(error)}`)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate aria-labelledby="add-dataset-heading">
      <h2 id="add-dataset-heading">Add a dataset</h2>
      <TextField id="name" label="Name" value={values.name} onChange={setField('name')} error={errors.name} required />
      <TextField id="owner" label="Owner" value={values.owner} onChange={setField('owner')} />
      <TextField
        id="description"
        label="Description"
        value={values.description}
        onChange={setField('description')}
        error={errors.description}
        required
        multiline
      />

      <button type="submit" disabled={isSubmitting}>
        {isSubmitting ? 'Saving and curating…' : 'Add dataset'}
      </button>

      {submitError && (
        <p role="alert" className="error">
          {submitError}
        </p>
      )}
      <p role="status">{notice}</p>
    </form>
  )
}
