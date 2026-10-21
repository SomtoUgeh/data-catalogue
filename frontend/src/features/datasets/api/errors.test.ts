import { describe, expect, it } from 'vitest'
import * as z from 'zod'

import { ApiError, unwrapResponse } from './errors'

function rejection(result: { data?: unknown; error?: unknown; response?: Response }) {
  return unwrapResponse(Promise.resolve(result)).catch((error: unknown) => error)
}

const status = (code: number) => new Response(null, { status: code })

describe('unwrapResponse', () => {
  it('returns the data of a successful call', async () => {
    await expect(
      unwrapResponse(Promise.resolve({ data: [], response: status(200) })),
    ).resolves.toEqual([])
  })

  it('keeps the field errors of a 400', async () => {
    const error = await rejection({
      error: {
        error: 'Validation failed',
        fields: [{ field: 'name', message: 'name is required' }],
      },
      response: status(400),
    })

    expect(error).toEqual(
      new ApiError('Validation failed', 400, [{ field: 'name', message: 'name is required' }]),
    )
  })

  it('uses the server message of other error statuses', async () => {
    const error = await rejection({
      error: { error: "Dataset '1' not found" },
      response: status(404),
    })

    expect(error).toEqual(new ApiError("Dataset '1' not found", 404))
  })

  it('falls back to the status for an unknown error body', async () => {
    const error = await rejection({ error: 'Bad gateway', response: status(502) })

    expect(error).toEqual(new ApiError('Request failed (502).', 502))
  })

  it('reports a failed request without exposing the raw error', async () => {
    const error = await rejection({ error: new TypeError('Failed to fetch') })

    expect(error).toEqual(new ApiError('Could not reach the catalogue.', 0))
  })

  it('reports a response that fails the generated schema', async () => {
    const parsed = z.object({ id: z.string() }).safeParse({})
    const error = await rejection({ error: parsed.error, response: status(200) })

    expect(error).toEqual(new ApiError('The server returned an unexpected response.', 200))
  })

  it('rethrows an aborted request so TanStack Query can ignore it', async () => {
    const abort = new DOMException('The operation was aborted.', 'AbortError')

    expect(await rejection({ error: abort })).toBe(abort)
  })
})
