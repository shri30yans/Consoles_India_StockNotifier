import { Link, Navigate } from "react-router-dom"
import { useAuth } from "@/auth/AuthContext"
import { apiJson } from "@/lib/api"
import { formatShortDate } from "@/lib/format"
import { FetchErrorPanel } from "@/components/blocks/FetchErrorPanel"
import { PageShell } from "@/components/blocks/PageShell"
import { PageHeader } from "@/components/blocks/PageHeader"
import { StatCard } from "@/components/blocks/StatCard"
import type { RemoteQuery } from "@/hooks/useRemoteQuery"
import { useRemoteQuery } from "@/hooks/useRemoteQuery"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { LoadingSpinner } from "@/components/blocks/LoadingSpinner"

type Row = {
  id: number
  raw_url: string
  status: string
  created_at: string
  admin_note: string | null
  promoted_product_id: string | null
}

function AccountRequestHistory(props: {
  query: RemoteQuery<Row[]>
  onRetry: () => void
}) {
  const { query, onRetry } = props

  switch (query.status) {
    case "idle":
      return null
    case "loading":
      return (
        <div className="flex justify-center py-10">
          <LoadingSpinner label="Loading requests" />
        </div>
      )
    case "error":
      return (
        <FetchErrorPanel
          title="Couldn&apos;t load requests"
          message={query.message}
          onRetry={onRetry}
        />
      )
    case "success":
      if (query.data.length === 0) {
        return <p className="text-muted-foreground text-sm">No requests yet.</p>
      }
      return (
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
              {query.data.map((x) => (
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
      )
  }
}

export function AccountPage() {
  const { me, loading } = useAuth()

  const { query: requestsQuery, retry: retryRequests } = useRemoteQuery(
    `me-requests:${me?.email ?? ""}`,
    (signal) => apiJson<Row[]>("/api/me/requests", { signal }),
    { enabled: Boolean(me), fallbackMessage: "Failed to load requests" },
  )

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

  const pending =
    requestsQuery.status === "success"
      ? requestsQuery.data.filter((r) => r.status === "pending").length
      : 0

  return (
    <PageShell className="space-y-8">
      <PageHeader
        title="Your requests"
        description={`Signed in as ${me.email}. Tracking submissions appear below with reviewer status.`}
      />

      {requestsQuery.status === "success" ? (
        <section aria-label="Request summary" className="grid gap-3 sm:grid-cols-3">
          <StatCard label="Total requests" value={requestsQuery.data.length} />
          <StatCard label="Pending review" value={pending} />
          <StatCard
            label="Approved"
            value={requestsQuery.data.filter((r) => r.status === "approved").length}
          />
        </section>
      ) : null}

      <section aria-label="Request history">
        <h2 className="mb-3 font-heading text-sm font-medium">History</h2>
        <AccountRequestHistory query={requestsQuery} onRetry={retryRequests} />
      </section>

      <p className="text-muted-foreground text-xs">
        <Link to="/request" className="text-primary underline-offset-4 hover:underline">
          Submit another product URL →
        </Link>
      </p>
    </PageShell>
  )
}
