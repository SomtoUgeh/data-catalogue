import { cloneElement, type ReactElement } from 'react'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

type ControlProps = {
  id?: string
  name?: string
  'aria-invalid'?: boolean
  'aria-describedby'?: string
}

type FormFieldProps = {
  id: string
  label: string
  error?: string
  children: ReactElement<ControlProps>
}

export function FormField({ id, label, error, children }: FormFieldProps) {
  const errorId = `${id}-error`
  const control = cloneElement(children, {
    id,
    name: children.props.name ?? id,
    'aria-invalid': Boolean(error),
    'aria-describedby': error ? errorId : undefined,
  })

  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {control}
      {error ? (
        <p id={errorId} className="text-sm text-destructive" role="alert">
          {error}
        </p>
      ) : null}
    </div>
  )
}

type TextFieldProps = {
  id: string
  label: string
  error?: string
  value: string
  onBlur: () => void
  onChange: (value: string) => void
  autoComplete?: string
}

export function TextField({
  id,
  label,
  error,
  value,
  onBlur,
  onChange,
  autoComplete = 'off',
}: TextFieldProps) {
  return (
    <FormField id={id} label={label} error={error}>
      <Input
        value={value}
        onBlur={onBlur}
        onChange={(event) => onChange(event.target.value)}
        autoComplete={autoComplete}
      />
    </FormField>
  )
}

type TextAreaFieldProps = TextFieldProps & {
  rows?: number
}

export function TextAreaField({
  id,
  label,
  error,
  value,
  onBlur,
  onChange,
  rows = 3,
}: TextAreaFieldProps) {
  return (
    <FormField id={id} label={label} error={error}>
      <Textarea
        value={value}
        onBlur={onBlur}
        onChange={(event) => onChange(event.target.value)}
        rows={rows}
      />
    </FormField>
  )
}
