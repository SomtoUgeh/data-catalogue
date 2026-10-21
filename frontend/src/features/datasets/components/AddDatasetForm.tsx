import { useForm } from '@tanstack/react-form'

import { TextAreaField, TextField } from '@/components/form-field'
import { StatusBanner } from '@/components/status-banner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import {
  firstErrorMessage,
  getErrorMessage,
  getFieldErrors,
  isValidationError,
  parseApiError,
} from '../api/errors'
import { datasetCreateFormSchema } from '../api/formSchema'
import { useCreateDatasetMutation } from '../api/mutations'
import { curationBanner } from '../curationBanner'

const FORM_FIELDS = ['name', 'owner', 'description'] as const

function isFormField(field: string): field is (typeof FORM_FIELDS)[number] {
  return (FORM_FIELDS as readonly string[]).includes(field)
}

export function AddDatasetForm() {
  const createDataset = useCreateDatasetMutation()

  const form = useForm({
    defaultValues: {
      name: '',
      owner: '',
      description: '',
    },
    validators: {
      onChange: datasetCreateFormSchema,
      onSubmit: datasetCreateFormSchema,
    },
    onSubmit: async ({ value }) => {
      const parsed = datasetCreateFormSchema.safeParse(value)
      if (!parsed.success) return
      try {
        await createDataset.mutateAsync(parsed.data)
        form.reset()
      } catch (error) {
        const apiError = parseApiError(error)
        if (!isValidationError(apiError)) return
        for (const [field, message] of Object.entries(getFieldErrors(apiError))) {
          if (!isFormField(field)) continue
          form.setFieldMeta(field, (prev) => ({
            ...prev,
            errorMap: { ...prev.errorMap, onSubmit: message },
          }))
        }
      }
    },
  })

  const requestError =
    createDataset.isError && !isValidationError(parseApiError(createDataset.error))
      ? getErrorMessage(createDataset.error)
      : null

  const curationWarning =
    createDataset.isSuccess ? curationBanner(createDataset.data) : null

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
          <CardDescription>Name, owner, and description are required.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div aria-live="polite" className="flex flex-col gap-2 empty:hidden">
            {requestError ? <StatusBanner>{requestError}</StatusBanner> : null}
            {curationWarning ? <StatusBanner tone="warning">{curationWarning}</StatusBanner> : null}
          </div>

          <form.Field name="name">
            {(field) => (
              <TextField
                id="name"
                label="Name"
                error={firstErrorMessage(field.state.meta.errors)}
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={field.handleChange}
              />
            )}
          </form.Field>

          <form.Field name="owner">
            {(field) => (
              <TextField
                id="owner"
                label="Owner"
                error={firstErrorMessage(field.state.meta.errors)}
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={field.handleChange}
              />
            )}
          </form.Field>

          <form.Field name="description">
            {(field) => (
              <TextAreaField
                id="description"
                label="Description"
                error={firstErrorMessage(field.state.meta.errors)}
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
