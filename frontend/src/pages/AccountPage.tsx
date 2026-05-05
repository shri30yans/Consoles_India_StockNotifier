import { useEffect, useState } from "react"
import { Link, Navigate } from "react-router-dom"
import { useAuth } from "@/auth/AuthContext"
import { ApiError, api, ensureOk } from "@/lib/api"
import { formatShortDate } from "@/lib/format"
import { PageShell } from "@/components/blocks/PageShell"
import { PageHeader } from "@/components/blocks/PageHeader"
import { StatCard } from "@/components/blocks/StatCard"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { LoadingSpinner } from "@/components/blocks/LoadingSpinner"

type Row = {
  id: number
  raw_url: string
  status: string
  created_at: string
  admin_note: string | null
  promoted_product_id: string | null
}

export function AccountPage() {
  const { me, loading } = useAuth()
  const [rows, setRows] = useState<Row[] | null>(null)
  const [rowsError, setRowsError] = useState<string | null>(null)
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    if (!me) return
    let c = false
    setRowsError(null)
    setRows(null)
    void (async () => {
      try {
        const r = await api("/api/me/requests")
        await ensureOk(r)
        if (c) return
        setRows((await r.json()) as Row[])
      } catch (e) {
        if (c) return
        setRowsError(e instanceof ApiError ? e.message : "Failed to load requests")
      }
    })()
    return () => {
      c = true
    }
  }, [me, reloadToken])

  if (!loading && !me) {
    return <Navigate to="/login" replace />
  }

  if (loading || !me) {
    return (
      <PageShell>
        <div className="flex justify-center py-16">
          <LoadingSpinner label="Loading account" size="lg" />
        </div>
      </PageShell>
    )
  }

  const pending = (rows ?? []).filter((r) => r.status === "pending").length

  return (
    <PageShell className="space-y-8">
      <PageHeader
        title="Your requests"
        description={`Signed in as ${me.email}. Tracking submissions appear below with reviewer status.`}
      />

      {rows ? (
        <section aria-label="Request summary" className="grid gap-3 sm:grid-cols-3">
          <StatCard label="Total requests" value={rows.length} />
          <StatCard label="Pending review" value={pending} />
          <StatCard
            label="Approved"
            value={rows.filter((r) => r.status === "approved").length}
          />
        </section>
      ) : null}

      <section aria-label="Request history">
        <h2 className="mb-3 font-heading text-sm font-medium">History</h2>
        {rowsError ? (
          <div className="rounded-lg border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm">
            <p className="font-medium text-destructive">Couldn&apos;t load requests</p>
            <p className="mt-1 text-muted-foreground">{rowsError}</p>
            <Button
              type="button"
              size="sm"
              variant="secondary"
              className="mt-3"
              onClick={() => {
                setRowsError(null)
                setReloadToken((t) => t + 1)
              }}
            >
              Try again
            </Button>
          </div>
        ) : !rows ? (
          <div className="flex justify-center py-10">
            <LoadingSpinner label="Loading requests" />
          </div>
        ) : rows.length === 0 ? (
          <p className="text-muted-foreground text-sm">No requests yet.</p>
        ) : (
          <div className="overflow-hidden rounded-lg border border-border/80">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead scope="col">ID</TableHead>
                  <TableHead scope="col">URL</TableHead>
                  <TableHead scope="col">Status</TableHead>
                  <TableHead scope="col">When</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((x) => (
                  <TableRow key={x.id}>
                    <TableCell className="tabular-nums">{x.id}</TableCell>
                    <TableCell>
                      <a
                        href={x.raw_url}
                        className="text-primary text-xs break-all underline-offset-4 hover:underline"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        link
                      </a>
                    </TableCell>
                    <TableCell>
                      <Badge variant={x.status === "approved" ? "default" : "secondary"}>{x.status}</Badge>
                    </TableCell>
                    <TableCell className="text-[0.65rem] text-muted-foreground">
                      {formatShortDate(x.created_at)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      <p className="text-muted-foreground text-xs">
        <Link to="/request" className="text-primary underline-offset-4 hover:underline">
          Submit another product URL →
        </Link>
      </p>
    </PageShell>
  )
}
