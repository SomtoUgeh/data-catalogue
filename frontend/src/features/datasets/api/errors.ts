export class ApiError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

function messageFromBody(error: unknown, status: number): string {
  if (error && typeof error === 'object' && 'error' in error && typeof error.error === 'string') {
    return error.error
  }
  if (error instanceof Error && error.message) {
    return error.message
  }
  return `Request failed (${status})`
}

export function toApiError(error: unknown, status = 0): ApiError {
  if (error instanceof ApiError) {
    return error
  }
  return new ApiError(messageFromBody(error, status), status)
}

export async function unwrapResponse<T>(
  result: Promise<{ data?: T; error?: unknown; response?: Response }>,
): Promise<T> {
  const { data, error, response } = await result
  if (error || data === undefined) {
    throw toApiError(error, response?.status ?? 0)
  }
  return data
}
