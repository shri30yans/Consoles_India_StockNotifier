import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react"
import { api, getToken, setToken } from "@/lib/api"

export type Me = { id: number; email: string; role: string }

type AuthState = {
  me: Me | null
  loading: boolean
  refresh: () => Promise<Me | null>
  logout: () => void
}

const AuthContext = createContext<AuthState | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [me, setMe] = useState<Me | null>(null)
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    const t = getToken()
    if (!t) {
      setMe(null)
      setLoading(false)
      return null
    }
    const r = await api("/api/me")
    if (!r.ok) {
      setToken(null)
      setMe(null)
      setLoading(false)
      return null
    }
    const j = (await r.json()) as Me
    setMe(j)
    setLoading(false)
    return j
  }, [])

  useEffect(() => {
    void refresh()
  }, [refresh])

  const logout = useCallback(() => {
    setToken(null)
    setMe(null)
  }, [])

  const value = useMemo(
    () => ({ me, loading, refresh, logout }),
    [me, loading, refresh, logout],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error("useAuth outside AuthProvider")
  return ctx
}
