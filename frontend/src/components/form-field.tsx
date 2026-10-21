import type { ReactNode } from 'react'

import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Textarea } from '@/components/ui/textarea'

type FieldProps = {
  id: string
  name: string
  label: string
  error?: string
  value: string
  onBlur: () => void
  onChange: (value: string) => void
}

/** Props that tie a control to its label and inline error. */
function controlProps({ id, name, error, value, onBlur }: FieldProps) {
  return {
    id,
    name,
    value,
    onBlur,
    'aria-invalid': error ? true : undefined,
    'aria-describedby': error ? `${id}-error` : undefined,
  }
}

function FormField({
  id,
  label,
  error,
  children,
}: Pick<FieldProps, 'id' | 'label' | 'error'> & { children: ReactNode }) {
  // The error is linked to the control with aria-describedby, so a screen reader reads it on focus.
  // It is not a live region: announcing every keystroke's validation result is noise.
  return (
    <div className="flex flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
      {error ? (
        <p id={`${id}-error`} className="text-sm text-destructive">
          {error}
        </p>
      ) : null}
    </div>
  )
}

export function TextField(props: FieldProps) {
  return (
    <FormField {...props}>
      <Input
        {...controlProps(props)}
        onChange={(event) => props.onChange(event.target.value)}
        autoComplete="off"
      />
    </FormField>
  )
}

export function TextAreaField(props: FieldProps) {
  return (
    <FormField {...props}>
      <Textarea
        {...controlProps(props)}
        onChange={(event) => props.onChange(event.target.value)}
        rows={3}
      />
    </FormField>
  )
}
