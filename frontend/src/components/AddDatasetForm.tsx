import { useState } from 'react'
import { useForm } from '@tanstack/react-form'

import { ApiError } from '../types'
import { StatusBanner } from './StatusBanner'
import type { Dataset, DatasetInput } from '../types'

type AddDatasetFormProps = {
  onSubmit: (input: DatasetInput) => Promise<Dataset>
}

function requiredMessage(field: string, value: string): string | undefined {
  return value.trim() ? undefined : `${field} is required`
}

export function AddDatasetForm({ onSubmit }: AddDatasetFormProps) {
  const [formError, setFormError] = useState<string | null>(null)
  const [curationWarning, setCurationWarning] = useState<string | null>(null)

  const form = useForm({
    defaultValues: {
      name: '',
      owner: '',
      description: '',
    },
    onSubmit: async ({ value }) => {
      setFormError(null)
      setCurationWarning(null)
      try {
        const created = await onSubmit({
          name: value.name.trim(),
          owner: value.owner.trim(),
          description: value.description.trim(),
        })
        form.reset()
        if (created.curation_status === 'failed') {
          setCurationWarning(
            'Curation fell back to placeholders. The dataset was still saved.',
          )
        }
      } catch (error) {
        if (error instanceof ApiError && error.status === 400) {
          const message = error.message
          if (/name/i.test(message)) {
            form.setFieldMeta('name', (prev) => ({
              ...prev,
              errorMap: { ...prev.errorMap, onSubmit: message },
            }))
          }
          if (/description/i.test(message)) {
            form.setFieldMeta('description', (prev) => ({
              ...prev,
              errorMap: { ...prev.errorMap, onSubmit: message },
            }))
          }
          if (!/name/i.test(message) && !/description/i.test(message)) {
            setFormError(message)
          }
          return
        }
        setFormError(error instanceof Error ? error.message : 'Could not save the dataset.')
      }
    },
  })

  return (
    <form
      className="panel"
      onSubmit={(event) => {
        event.preventDefault()
        event.stopPropagation()
        void form.handleSubmit()
      }}
      noValidate
    >
      <h2>Add dataset</h2>
      <div aria-live="polite">
        {formError ? <StatusBanner>{formError}</StatusBanner> : null}
        {curationWarning ? (
          <StatusBanner tone="warning">{curationWarning}</StatusBanner>
        ) : null}
      </div>

      <form.Field
        name="name"
        validators={{
          onSubmit: ({ value }) => requiredMessage('Name', value),
        }}
      >
        {(field) => {
          const error = field.state.meta.errors[0]
          const errorId = 'name-error'
          return (
            <div className="field">
              <label htmlFor="name">Name</label>
              <input
                id="name"
                name="name"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={(event) => field.handleChange(event.target.value)}
                aria-invalid={Boolean(error)}
                aria-describedby={error ? errorId : undefined}
                autoComplete="off"
              />
              {error ? (
                <p id={errorId} className="field-error" role="alert">
                  {error}
                </p>
              ) : null}
            </div>
          )
        }}
      </form.Field>

      <form.Field name="owner">
        {(field) => (
          <div className="field">
            <label htmlFor="owner">Owner</label>
            <input
              id="owner"
              name="owner"
              value={field.state.value}
              onBlur={field.handleBlur}
              onChange={(event) => field.handleChange(event.target.value)}
              autoComplete="off"
            />
          </div>
        )}
      </form.Field>

      <form.Field
        name="description"
        validators={{
          onSubmit: ({ value }) => requiredMessage('Description', value),
        }}
      >
        {(field) => {
          const error = field.state.meta.errors[0]
          const errorId = 'description-error'
          return (
            <div className="field">
              <label htmlFor="description">Description</label>
              <textarea
                id="description"
                name="description"
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={(event) => field.handleChange(event.target.value)}
                aria-invalid={Boolean(error)}
                aria-describedby={error ? errorId : undefined}
                rows={3}
              />
              {error ? (
                <p id={errorId} className="field-error" role="alert">
                  {error}
                </p>
              ) : null}
            </div>
          )
        }}
      </form.Field>

      <form.Subscribe selector={(state) => state.isSubmitting}>
        {(isSubmitting) => (
          <button type="submit" disabled={isSubmitting}>
            {isSubmitting ? 'Saving dataset…' : 'Add dataset'}
          </button>
        )}
      </form.Subscribe>
    </form>
  )
}
