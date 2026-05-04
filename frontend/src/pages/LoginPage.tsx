import { useState } from "react"
import { Link, useNavigate, useSearchParams } from "react-router-dom"
import { api, readErrorMessage, setToken } from "@/lib/api"
import { useAuth } from "@/auth/AuthContext"
import { PageShell } from "@/components/blocks/PageShell"
import { PageHeader } from "@/components/blocks/PageHeader"
import { safeNextPath } from "@/lib/navigation"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

export function LoginPage() {
  const nav = useNavigate()
  const [searchParams] = useSearchParams()
  const next = safeNextPath(searchParams.get("next"))
  const { refresh } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [err, setErr] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr(null)
    const r = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ email, password }),
    })
    if (!r.ok) {
      setErr(await readErrorMessage(r))
      return
    }
    const j = (await r.json()) as { access_token: string }
    setToken(j.access_token)
    await refresh()
    nav(next, { replace: true })
  }

  return (
    <PageShell className="max-w-md space-y-6">
      <PageHeader
        title="Log in"
        description="Sign in to add products (Amazon.in / Flipkart URLs) and follow your approval queue."
      />
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="password">Password</Label>
          <Input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        {err ? <p className="text-destructive text-xs">{err}</p> : null}
        <Button type="submit" className="w-full sm:w-auto">
          Log in
        </Button>
      </form>
      <p className="text-muted-foreground text-xs">
        No account?{" "}
        <Link to={`/register?next=${encodeURIComponent(next)}`} className="text-primary underline-offset-4 hover:underline">
          Register
        </Link>
      </p>
    </PageShell>
  )
}
