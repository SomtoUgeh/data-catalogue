import { useForm } from '@tanstack/react-form'

import { TextAreaField, TextField } from '@/components/form-field'
import { StatusBanner } from '@/components/status-banner'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Spinner } from '@/components/ui/spinner'
import { ApiError } from '../api/errors'
import { useCreateDatasetMutation } from '../api/mutations'

function requiredMessage(field: string, value: string): string | undefined {
  return value.trim() ? undefined : `${field} is required`
}

export function AddDatasetForm() {
  const createDataset = useCreateDatasetMutation()

  const form = useForm({
    defaultValues: {
      name: '',
      owner: '',
      description: '',
    },
    onSubmit: async ({ value }) => {
      try {
        await createDataset.mutateAsync({
          name: value.name.trim(),
          owner: value.owner.trim(),
          description: value.description.trim(),
        })
        form.reset()
      } catch (error) {
        if (error instanceof ApiError && error.status === 400) {
          if (/name/i.test(error.message)) {
            form.setFieldMeta('name', (prev) => ({
              ...prev,
              errorMap: { ...prev.errorMap, onSubmit: error.message },
            }))
          }
          if (/description/i.test(error.message)) {
            form.setFieldMeta('description', (prev) => ({
              ...prev,
              errorMap: { ...prev.errorMap, onSubmit: error.message },
            }))
          }
        }
      }
    },
  })

  const requestError =
    createDataset.isError && createDataset.error instanceof ApiError && createDataset.error.status !== 400
      ? createDataset.error.message
      : createDataset.isError && !(createDataset.error instanceof ApiError)
        ? 'Could not save the dataset.'
        : null

  const curationWarning =
    createDataset.isSuccess && createDataset.data.curation_status === 'failed'
      ? 'Curation fell back to placeholders. The dataset was still saved.'
      : null

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
          <CardDescription>Name and description are required. Owner is optional.</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-4">
          <div aria-live="polite" className="flex flex-col gap-2 empty:hidden">
            {requestError ? <StatusBanner>{requestError}</StatusBanner> : null}
            {curationWarning ? <StatusBanner tone="warning">{curationWarning}</StatusBanner> : null}
          </div>

          <form.Field
            name="name"
            validators={{
              onSubmit: ({ value }) => requiredMessage('Name', value),
            }}
          >
            {(field) => (
              <TextField
                id="name"
                label="Name"
                error={field.state.meta.errors[0] ? String(field.state.meta.errors[0]) : undefined}
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
                value={field.state.value}
                onBlur={field.handleBlur}
                onChange={field.handleChange}
              />
            )}
          </form.Field>

          <form.Field
            name="description"
            validators={{
              onSubmit: ({ value }) => requiredMessage('Description', value),
            }}
          >
            {(field) => (
              <TextAreaField
                id="description"
                label="Description"
                error={field.state.meta.errors[0] ? String(field.state.meta.errors[0]) : undefined}
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
