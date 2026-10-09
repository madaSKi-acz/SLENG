/**
 * Purpose: Minimal fetch wrapper: base URL, JSON bodies, and one error type for every failure.
 * Layer:   web/api
 * Exports: HttpClient, ApiError, jsonBody, apiBase
 * Depends: fetch (browser)
 */
export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly kind: string,
  ) {
    super(message);
    this.name = 'ApiError';
  }

  get offline(): boolean {
    return this.kind === 'NetworkError';
  }
}

export class HttpClient {
  constructor(private readonly base: string) {}

  async json<T>(path: string, init?: RequestInit): Promise<T> {
    const response = await this.send(path, init);
    return (await response.json()) as T;
  }

  async blob(path: string, init?: RequestInit): Promise<Blob> {
    return (await this.send(path, init)).blob();
  }

  async send(path: string, init: RequestInit = {}): Promise<Response> {
    let response: Response;
    try {
      response = await fetch(this.base + path, init);
    } catch {
      throw new ApiError('The engine is not reachable.', 0, 'NetworkError');
    }
    if (!response.ok) throw await toApiError(response);
    return response;
  }
}

export function jsonBody(body: unknown, method = 'POST'): RequestInit {
  return { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) };
}

/** Where the engine API lives: same origin by default, or VITE_API_BASE for desktop builds. */
export function apiBase(): string {
  return import.meta.env.VITE_API_BASE ?? '/api/v1';
}

async function toApiError(response: Response): Promise<ApiError> {
  const fallback = response.statusText || `HTTP ${response.status}`;
  try {
    const body = (await response.json()) as { error?: string; type?: string };
    return new ApiError(body.error ?? fallback, response.status, body.type ?? 'HttpError');
  } catch {
    return new ApiError(fallback, response.status, 'HttpError');
  }
}
