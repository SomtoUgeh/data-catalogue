import { setupWorker } from 'msw/browser'

import { datasetsHandlers } from './handlers'

export const worker = setupWorker(...datasetsHandlers)
