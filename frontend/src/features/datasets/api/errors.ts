import * as z from 'zod'

import type { FieldError } from './generated/types.gen'
import { zErrorResponse, zValidationErrorResponse } from './generated/zod.gen'

/** Every failed API call becomes an ApiError. `status` is 0 when no response arrived. */
export class ApiError extends Error {
  readonly status: number
  readonly fields: FieldError[]

  constructor(message: string, status: number, fields: FieldError[] = []) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.fields = fields
  }
}

type ClientResult<T> = { data?: T; error?: unknown; response?: Response }

/**
 * Returns the data from a generated client call made with `throwOnError: false`, or throws an ApiError.
 * The client reports three failures: no response (network failure or abort), a response that fails
 * the generated Zod validator, and an error status with the parsed JSON body.
 */
export async function unwrapResponse<T>(request: Promise<ClientResult<T>>): Promise<T> {
  const { data, error, response } = await request
  if (error === undefined && data !== undefined) return data

  if (!response) {
    // TanStack Query cancels queries with an AbortError; rethrow it so it is not shown as an error.
    if (error instanceof DOMException && error.name === 'AbortError') throw error
    throw new ApiError('Could not reach the catalogue.', 0)
  }
  if (error instanceof z.ZodError) {
    throw new ApiError('The server returned an unexpected response.', response.status)
  }

  const validation = zValidationErrorResponse.safeParse(error)
  if (validation.success) {
    throw new ApiError(validation.data.error, response.status, validation.data.fields)
  }
  const generic = zErrorResponse.safeParse(error)
  throw new ApiError(
    generic.success ? generic.data.error : `Request failed (${response.status}).`,
    response.status,
  )
}

export function isValidationError(error: unknown): error is ApiError {
  return error instanceof ApiError && error.fields.length > 0
}

export function getErrorMessage(error: unknown): string {
  return error instanceof ApiError ? error.message : 'Something went wrong.'
}

const issueSchema = z.object({ message: z.string() })

/** TanStack Form keeps strings (server errors) and Standard Schema issues (Zod errors) in one list. */
export function firstErrorMessage(errors: unknown[]): string | undefined {
  const first = errors[0]
  if (typeof first === 'string') return first
  const issue = issueSchema.safeParse(first)
  return issue.success ? issue.data.message : undefined
}
