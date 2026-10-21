import { useForm, useSelector } from '@tanstack/react-form'

import { TextAreaField, TextField } from '@/components/form-field'
import { StatusBanner } from '@/components/status-banner'
import { Button } from '@/components/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { firstErrorMessage, getErrorMessage, isValidationError } from '../api/errors'
import { datasetCreateFormSchema } from '../api/formSchema'
import { useCreateDatasetMutation } from '../api/mutations'
import { curationBanner } from '../curationBanner'

const FIELDS = ['name', 'owner', 'description'] as const
type Field = (typeof FIELDS)[number]

function isField(field: string): field is Field {
  return FIELDS.some((name) => name === field)
}

const fieldId = (field: Field) => `dataset-${field}`

function focusField(field: Field | undefined) {
  if (field) document.getElementById(fieldId(field))?.focus()
}

export function AddDatasetForm() {
  const createDataset = useCreateDatasetMutation()

  const form = useForm({
    defaultValues: { name: '', owner: '', description: '' },
    validators: {
      onChange: datasetCreateFormSchema,
      onBlur: datasetCreateFormSchema,
      onSubmit: datasetCreateFormSchema,
    },
    onSubmitInvalid: ({ formApi }) => {
      focusField(FIELDS.find((field) => formApi.getFieldMeta(field)?.isValid === false))
    },
    onSubmit: async ({ value }) => {
      const parsed = datasetCreateFormSchema.safeParse(value)
      if (!parsed.success) return

      try {
        await createDataset.mutateAsync(parsed.data)

        form.reset()
      } catch (error) {
        if (!isValidationError(error)) return

        const flagged = error.fields.map(({ field }) => field).filter(isField)

        for (const { field, message } of error.fields) {
          if (!isField(field)) continue

          form.setFieldMeta(field, (meta) => ({
            ...meta,
            errorMap: { ...meta.errorMap, onSubmit: message },
          }))
        }

        focusField(FIELDS.find((field) => flagged.includes(field)))
      }
    },
  })

  const submitted = useSelector(form.store, (state) => state.submissionAttempts > 0)
  const visibleError = (meta: { isBlurred: boolean; errors: unknown[] }) =>
    submitted || meta.isBlurred ? firstErrorMessage(meta.errors) : undefined

  const requestError =
    createDataset.isError && !isValidationError(createDataset.error)
      ? getErrorMessage(createDataset.error)
      : null

  const curationWarning = createDataset.isSuccess ? curationBanner(createDataset.data) : null

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault()
        event.stopPropagation()
        createDataset.reset()
        void form.handleSubmit()
      }}
      noValidate
    >
      <Card>
        <CardHeader>
          <CardTitle>
            <h2>Add dataset</h2>
          </CardTitle>
          <CardDescription>Name and description are required.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          {/* Live regions stay in the DOM so screen readers announce the messages put in them. */}
          <div role="alert" className="empty:hidden">
            {requestError ? <StatusBanner>{requestError}</StatusBanner> : null}
          </div>
          <div role="status" className="empty:hidden">
            {curationWarning ? <StatusBanner tone="warning">{curationWarning}</StatusBanner> : null}
          </div>

          <form.Field name="name">
            {(field) => (
              <TextField
                id={fieldId('name')}
                name={field.name}
                label="Name"
                error={visibleError(field.state.meta)}
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={field.handleChange}
              />
            )}
          </form.Field>

          <form.Field name="owner">
            {(field) => (
              <TextField
                id={fieldId('owner')}
                name={field.name}
                label="Owner (optional)"
                error={visibleError(field.state.meta)}
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={field.handleChange}
              />
            )}
          </form.Field>

          <form.Field name="description">
            {(field) => (
              <TextAreaField
                id={fieldId('description')}
                name={field.name}
                label="Description"
                error={visibleError(field.state.meta)}
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={field.handleChange}
              />
            )}
          </form.Field>
        </CardContent>
        <CardFooter>
          <Button type="submit" disabled={createDataset.isPending}>
            {createDataset.isPending ? (
              <>
                <Spinner data-icon="inline-start" aria-hidden />
                Curating…
              </>
            ) : (
              'Add dataset'
            )}
          </Button>
        </CardFooter>
      </Card>
    </form>
  )
}
