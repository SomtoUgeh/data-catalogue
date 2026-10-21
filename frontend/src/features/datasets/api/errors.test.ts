import { describe, expect, it } from 'vitest'
import * as z from 'zod'

import {
  getErrorMessage,
  getFieldErrors,
  isNotFoundError,
  isValidationError,
  parseApiError,
  zodIssuesToFieldErrors,
} from './errors'
import { zDatasetCreate } from './generated/zod.gen'

describe('parseApiError', () => {
  it('safeParses a validation error body', () => {
    const error = parseApiError({
      error: 'Validation failed',
      fields: [{ field: 'name', message: 'name is required' }],
    })

    expect(error.message).toBe('Validation failed')
    expect(error.status).toBe(400)
    expect(isValidationError(error)).toBe(true)
    expect(getFieldErrors(error)).toEqual({ name: 'name is required' })
  })

  it('safeParses a not-found body', () => {
    const error = parseApiError({ error: "Dataset with id '1' was not found." })

    expect(isNotFoundError(error)).toBe(true)
    expect(getErrorMessage(error)).toBe("Dataset with id '1' was not found.")
  })

  it('falls back for an unknown shape', () => {
    const error = parseApiError({ oops: true })

    expect(error.message).toBe('Something went wrong.')
    expect(isValidationError(error)).toBe(false)
    expect(isNotFoundError(error)).toBe(false)
  })

  it('maps a network failure without leaking the raw error', () => {
    const error = parseApiError(new TypeError('Failed to fetch'))

    expect(error.message).toBe('Could not reach the catalogue.')
    expect(error.status).toBe(0)
  })
})

describe('zodIssuesToFieldErrors', () => {
  it('flattens Zod issues to field messages', () => {
    const parsed = zDatasetCreate.safeParse({ name: '', description: '' })
    expect(parsed.success).toBe(false)
    if (parsed.success) return

    const fields = zodIssuesToFieldErrors(parsed.error)
    expect(fields.name).toBeTruthy()
    expect(fields.description).toBeTruthy()
  })

  it('keeps custom issue messages', () => {
    const schema = z.object({
      name: z.string().min(1, 'Name is required'),
    })
    const parsed = schema.safeParse({ name: '' })
    expect(parsed.success).toBe(false)
    if (parsed.success) return

    expect(zodIssuesToFieldErrors(parsed.error)).toEqual({ name: 'Name is required' })
  })
})
