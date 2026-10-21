import { setupServer } from 'msw/node'

import { datasetsHandlers } from './handlers'

export const server = setupServer(...datasetsHandlers)
