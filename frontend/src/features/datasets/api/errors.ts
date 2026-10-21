import * as z from 'zod'

import type { FieldError } from './generated/types.gen'
import { zErrorResponse, zValidationErrorResponse } from './generated/zod.gen'

export class ApiError extends Error {
  readonly status: number
  readonly fields: FieldError[]

  constructor(message: string, status = 0, fields: FieldError[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fields = fields
  }
}

const issueMessageSchema = z.object({ message: z.string() })

function isNetworkFailure(error: unknown): boolean {
  if (!(error instanceof Error)) return false
  const message = error.message.toLowerCase()
  return (
    error.name === 'TypeError' ||
    error.name === 'AbortError' ||
    message.includes('failed to fetch') ||
    message.includes('networkerror') ||
    message.includes('network request failed') ||
    message.includes('load failed')
  )
}

export function parseApiError(error: unknown, status = 0): ApiError {
  if (error instanceof ApiError) return error

  const validation = zValidationErrorResponse.safeParse(error)
  if (validation.success) {
    return new ApiError(validation.data.error, status || 400, validation.data.fields)
  }

  const generic = zErrorResponse.safeParse(error)
  if (generic.success) {
    const inferred = /not found/i.test(generic.data.error) ? 404 : status
    return new ApiError(generic.data.error, inferred || status)
  }

  if (isNetworkFailure(error)) {
    return new ApiError('Could not reach the catalogue.', 0)
  }

  if (error instanceof z.ZodError) {
    return new ApiError('The server returned an unexpected response.', status)
  }

  if (error instanceof Error) {
    return new ApiError(error.message || 'Something went wrong.', status)
  }

  return new ApiError(status ? `Request failed (${status})` : 'Something went wrong.', status)
}

export function isValidationError(error: unknown): error is ApiError {
  return error instanceof ApiError && error.status === 400 && error.fields.length > 0
}

export function isNotFoundError(error: unknown): error is ApiError {
  return error instanceof ApiError && error.status === 404
}

export function getFieldErrors(apiError: ApiError): Record<string, string> {
  const result: Record<string, string> = {}
  for (const item of apiError.fields) {
    result[item.field] = item.message
  }
  return result
}

export function zodIssuesToFieldErrors(zodError: z.ZodError): Record<string, string> {
  const { fieldErrors } = z.flattenError(zodError)
  const result: Record<string, string> = {}
  for (const [field, messages] of Object.entries(fieldErrors)) {
    const message = Array.isArray(messages) ? messages[0] : undefined
    if (field && message) result[field] = message
  }
  return result
}

export function getErrorMessage(error: unknown): string {
  return parseApiError(error).message
}

export function firstErrorMessage(errors: unknown[]): string | undefined {
  const first = errors[0]
  if (first == null) return undefined
  if (typeof first === 'string') return first
  const parsed = issueMessageSchema.safeParse(first)
  return parsed.success ? parsed.data.message : undefined
}

export async function unwrapResponse<T>(
  result: Promise<{ data?: T; error?: unknown; response?: Response }>,
): Promise<T> {
  try {
    const { data, error, response } = await result
    if (error || data === undefined) {
      throw parseApiError(error, response?.status ?? 0)
    }
    return data
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw parseApiError(error)
  }
}
