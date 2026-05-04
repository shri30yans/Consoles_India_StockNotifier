import { useState } from "react"
import { Link, Navigate } from "react-router-dom"
import { api, readErrorMessage } from "@/lib/api"
import { useAuth } from "@/auth/AuthContext"
import { PageShell } from "@/components/blocks/PageShell"
import { LoadingSpinner } from "@/components/blocks/LoadingSpinner"
import { PageHeader } from "@/components/blocks/PageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"

export function RequestPage() {
  const { me, loading } = useAuth()
  const [url, setUrl] = useState("")
  const [name, setName] = useState("")
  const [note, setNote] = useState("")
  const [err, setErr] = useState<string | null>(null)
  const [done, setDone] = useState(false)

  if (!loading && !me) {
    return <Navigate to="/login?next=%2Frequest" replace />
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault()
    setErr(null)
    const r = await api("/api/requests", {
      method: "POST",
      body: JSON.stringify({
        url,
        desired_product_name: name || null,
        note: note || null,
      }),
    })
    if (!r.ok) {
      setErr(await readErrorMessage(r))
      return
    }
    setDone(true)
  }

  if (loading || !me) {
    return (
      <PageShell>
        <div className="flex justify-center py-16">
          <LoadingSpinner label="Loading" size="lg" />
        </div>
      </PageShell>
    )
  }

  if (done) {
    return (
      <PageShell className="max-w-lg space-y-4">
        <PageHeader title="Thanks" description="Request received. You can track status under Account." />
        <Button variant="outline" asChild>
          <Link to="/account">View your requests</Link>
        </Button>
      </PageShell>
    )
  }

  return (
    <PageShell className="max-w-lg space-y-6">
      <PageHeader
        title="Add a product to the tracker"
        description="Paste an Amazon.in or Flipkart product link. An operator approves it before scrapes run — same flow as classic stock-tracking directories."
      />
      <form onSubmit={onSubmit} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="url">Product URL (https)</Label>
          <Input
            id="url"
            type="url"
            required
            placeholder="https://www.amazon.in/dp/…"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
          />
        </div>
        <div className="space-y-2">
          <Label htmlFor="pname">Display name (optional)</Label>
          <Input id="pname" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="space-y-2">
          <Label htmlFor="note">Note (optional)</Label>
          <Textarea id="note" rows={3} value={note} onChange={(e) => setNote(e.target.value)} />
        </div>
        {err ? <p className="text-destructive text-xs">{err}</p> : null}
        <Button type="submit">Submit for review</Button>
      </form>
    </PageShell>
  )
}
