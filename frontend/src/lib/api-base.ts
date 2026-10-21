export function getApiBaseUrl(): string {
  if (typeof process !== 'undefined' && process.env.API_BASE_URL) {
    return process.env.API_BASE_URL.replace(/\/$/, '')
  }
  const fromVite = import.meta.env.VITE_API_BASE_URL
  return (typeof fromVite === 'string' && fromVite ? fromVite : 'http://127.0.0.1:8000').replace(
    /\/$/,
    '',
  )
}
