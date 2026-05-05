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

export function RegisterPage() {
  const nav = useNavigate()
  const [searchParams] = useSearchParams()
  const next = safeNextPath(searchParams.get("next"))
  const { refresh } = useAuth()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [passwordConfirm, setPasswordConfirm] = useState("")
  const [err, setErr] = useState<string | null>(null)

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr(null)
    if (password !== passwordConfirm) {
      setErr("Passwords do not match")
      return
    }
    const r = await api("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, password, password_confirm: passwordConfirm }),
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
        title="Create account"
        description="Join to request product tracking and never miss a restock again."
      />
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="remail">Email</Label>
          <Input
            id="remail"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="rpass">Password (8+ characters)</Label>
          <Input
            id="rpass"
            type="password"
            autoComplete="new-password"
            minLength={8}
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="rpass-confirm">Confirm Password</Label>
          <Input
            id="rpass-confirm"
            type="password"
            autoComplete="new-password"
            minLength={8}
            required
            value={passwordConfirm}
            onChange={(e) => setPasswordConfirm(e.target.value)}
          />
        </div>
        {err ? <p className="text-destructive text-xs">{err}</p> : null}
        <Button type="submit" className="w-full sm:w-auto">
          Register
        </Button>
      </form>
      <p className="text-muted-foreground text-xs">
        Already have an account?{" "}
        <Link
          to={`/login?next=${encodeURIComponent(next)}`}
          className="text-primary underline-offset-4 hover:underline"
        >
          Log in
        </Link>
      </p>
    </PageShell>
  )
}
