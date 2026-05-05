const TOKEN_KEY = "token"

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

export function setToken(t: string | null): void {
  if (t) localStorage.setItem(TOKEN_KEY, t)
  else localStorage.removeItem(TOKEN_KEY)
}

export async function api(path: string, opts: RequestInit = {}): Promise<Response> {
  const headers = new Headers(opts.headers)
  const t = getToken()
  if (t) headers.set("Authorization", `Bearer ${t}`)
  if (opts.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json")
  }
  return fetch(path, { ...opts, headers })
}

/** Thrown when {@link ensureOk} receives a non-OK response (4xx/5xx). */
export class ApiError extends Error {
  readonly status: number
  readonly response: Response

  constructor(status: number, message: string, response: Response) {
    super(message)
    this.name = "ApiError"
    this.status = status
    this.response = response
  }
}

/** Throws {@link ApiError} if the response is not OK; otherwise returns the same response. */
export async function ensureOk(r: Response): Promise<Response> {
  if (r.ok) return r
  const msg = await readErrorMessage(r)
  throw new ApiError(r.status, msg, r)
}

export async function readErrorMessage(r: Response): Promise<string> {
  try {
    const j: unknown = await r.json()
    if (j && typeof j === "object" && "detail" in j) {
      const d = (j as { detail: unknown }).detail
      if (typeof d === "string") return d
      if (Array.isArray(d)) {
        return d
          .map((x) =>
            x && typeof x === "object" && "msg" in x ? String((x as { msg: unknown }).msg) : String(x),
          )
          .join(", ")
      }
    }
  } catch {
    /* ignore */
  }
  return "Request failed"
}
