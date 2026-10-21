import { cleanup } from '@testing-library/react'
import { afterAll, afterEach, beforeAll } from 'vitest'

import { server } from '@/features/datasets/mocks/server'
import { resetDatasetStore } from '@/features/datasets/mocks/store'

import '@testing-library/jest-dom/vitest'

beforeAll(() => {
  server.listen({ onUnhandledRequest: 'error' })
})

afterEach(() => {
  server.resetHandlers()
  resetDatasetStore()
  cleanup()
})

afterAll(() => {
  server.close()
})
