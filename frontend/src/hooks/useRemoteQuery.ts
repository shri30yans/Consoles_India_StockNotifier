import { useCallback, useEffect, useRef, useState } from "react"
import { getErrorMessage } from "@/lib/api"

/** Discriminated union for one async resource — avoids ambiguous null + error pairs. */
export type RemoteQuery<T> =
  | { status: "idle" }
  | { status: "loading" }
  | { status: "error"; message: string }
  | { status: "success"; data: T }

/**
 * Loads data when `queryKey` or `retry()` changes; aborts in-flight requests on key change or unmount.
 * Uses a ref for `fetcher` so callers can close over fresh values without listing a function in deps.
 */
export function useRemoteQuery<T>(
  queryKey: string,
  fetcher: (signal: AbortSignal) => Promise<T>,
  options?: { enabled?: boolean; fallbackMessage?: string },
): { query: RemoteQuery<T>; retry: () => void } {
  const enabled = options?.enabled !== false
  const fallbackRef = useRef(options?.fallbackMessage ?? "Request failed")
  fallbackRef.current = options?.fallbackMessage ?? "Request failed"

  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  const [retryEpoch, setRetryEpoch] = useState(0)
  const retry = useCallback(() => setRetryEpoch((n) => n + 1), [])

  const [query, setQuery] = useState<RemoteQuery<T>>(() =>
    enabled ? { status: "loading" } : { status: "idle" },
  )

  useEffect(() => {
    if (!enabled) {
      setQuery({ status: "idle" })
      return
    }

    const ac = new AbortController()
    setQuery({ status: "loading" })

    void (async () => {
      try {
        const data = await fetcherRef.current(ac.signal)
        if (ac.signal.aborted) return
        setQuery({ status: "success", data })
      } catch (e) {
        if (ac.signal.aborted) return
        setQuery({
          status: "error",
          message: getErrorMessage(e, fallbackRef.current),
        })
      }
    })()

    return () => ac.abort()
  }, [queryKey, retryEpoch, enabled])

  return { query, retry }
}
