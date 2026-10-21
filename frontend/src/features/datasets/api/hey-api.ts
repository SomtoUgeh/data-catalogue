import type { CreateClientConfig } from './generated/client.gen'

// The API is same-origin everywhere: the Worker serves both, and Vite proxies /datasets in dev.
// The generated client builds a URL object from baseUrl, so it needs an absolute origin.
export const createClientConfig: CreateClientConfig = (config) => ({
  ...config,
  baseUrl: window.location.origin,
})
