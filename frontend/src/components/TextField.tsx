import type { ChangeEvent } from 'react'

type TextFieldProps = {
  id: string
  label: string
  value: string
  onChange: (value: string) => void
  error?: string
  required?: boolean
  multiline?: boolean
}

export function TextField({ id, label, value, onChange, error, required, multiline }: TextFieldProps) {
  const errorId = `${id}-error`
  const controlProps = {
    id,
    name: id,
    value,
    required,
    'aria-invalid': error ? true : undefined,
    'aria-describedby': error ? errorId : undefined,
    onChange: (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange(event.target.value),
  }

  return (
    <div className="field">
      <label htmlFor={id}>{label}</label>
      {multiline ? <textarea rows={3} {...controlProps} /> : <input type="text" {...controlProps} />}
      {error && (
        <p id={errorId} className="error">
          {error}
        </p>
      )}
    </div>
  )
}
