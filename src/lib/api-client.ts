export class ApiError extends Error {
  status: number
  detail: string

  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

async function readDetail(response: Response): Promise<string> {
  const body: unknown = await response.json().catch(() => null)
  if (
    body !== null &&
    typeof body === 'object' &&
    'detail' in body &&
    typeof body.detail === 'string'
  ) {
    return body.detail
  }
  return response.statusText
}

export async function apiRequest<T>(path: string, init?: RequestInit): Promise<T> {
  const headers = new Headers(init?.headers)
  headers.set('Content-Type', 'application/json')

  const response = await fetch(path, {
    credentials: 'same-origin',
    ...init,
    headers,
  })

  if (!response.ok) {
    throw new ApiError(response.status, await readDetail(response))
  }

  if (response.status === 204) {
    return undefined as T
  }

  return (await response.json()) as T
}
