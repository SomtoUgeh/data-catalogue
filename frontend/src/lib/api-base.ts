/** Same-origin by default so Vite can proxy `/datasets` to FastAPI. */
export function getApiBaseUrl(): string {
  const fromVite = import.meta.env.VITE_API_BASE_URL
  if (typeof fromVite === 'string' && fromVite.trim()) {
    return fromVite.replace(/\/$/, '')
  }
  if (typeof window !== 'undefined' && window.location?.origin) {
    return window.location.origin
  }
  return ''
}
