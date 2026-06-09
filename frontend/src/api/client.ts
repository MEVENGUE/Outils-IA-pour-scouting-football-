import { API_URL } from './config'

export function parseApiError(detail: unknown, fallback: string): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => String(item)).join('; ')
  return fallback
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
  timeoutMs = 90_000,
): Promise<T> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), timeoutMs)

  try {
    const response = await fetch(`${API_URL}${path}`, {
      ...options,
      signal: controller.signal,
      headers: {
        'Content-Type': 'application/json',
        ...(options.headers ?? {}),
      },
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(
        parseApiError(
          (errorData as { detail?: unknown }).detail,
          `Erreur ${response.status}: ${response.statusText}`,
        ),
      )
    }

    return (await response.json()) as T
  } finally {
    window.clearTimeout(timeoutId)
  }
}
