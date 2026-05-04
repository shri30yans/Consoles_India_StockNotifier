import { useCallback, useEffect, useState } from "react"
import { Link, useParams } from "react-router-dom"
import { api } from "@/lib/api"
import { formatInr, formatShortDate } from "@/lib/format"
import { PageShell } from "@/components/blocks/PageShell"
import { PageHeader } from "@/components/blocks/PageHeader"
import { Badge } from "@/components/ui/badge"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"
import { LoadingSpinner } from "@/components/blocks/LoadingSpinner"

type Detail = {
  id: string
  name: string
  brand: string | null
  category: string
  emoji: string | null
  image_url: string | null
  watches: { source: string; poll_seconds: number; url: string }[]
}

type StatusRow = {
  retailer: string
  in_stock: boolean | null
  price_inr: number | null
  last_scrape_at: string | null
}

const STATUS_POLL_MS = 60_000

export function ProductPage() {
  const { id: rawId } = useParams()
  const id = rawId ? decodeURIComponent(rawId) : ""
  const [detail, setDetail] = useState<Detail | null>(null)
  const [status, setStatus] = useState<StatusRow[] | null>(null)
  const [err, setErr] = useState(false)
  const [loading, setLoading] = useState(true)
  const [statusLoading, setStatusLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)

  useEffect(() => {
    if (!id) {
      setLoading(false)
      setStatusLoading(false)
      return
    }
    let c = false
    setLoading(true)
    setStatusLoading(true)
    setErr(false)
    setStatus(null)
    void (async () => {
      const r1 = await api("/api/products/" + encodeURIComponent(id))
      if (c) return
      if (!r1.ok) {
        setErr(true)
        setDetail(null)
        setLoading(false)
        setStatusLoading(false)
        return
      }
      setDetail((await r1.json()) as Detail)
      setLoading(false)
      setErr(false)

      const r2 = await api("/api/products/" + encodeURIComponent(id) + "/status")
      if (c) return
      setStatus(r2.ok ? ((await r2.json()) as { retailers: StatusRow[] }).retailers : [])
      setStatusLoading(false)
    })()
    return () => {
      c = true
    }
  }, [id])

  const refreshData = useCallback(async () => {
    if (!id) return
    setRefreshing(true)
    try {
      const r1 = await api("/api/products/" + encodeURIComponent(id))
      if (r1.ok) setDetail((await r1.json()) as Detail)
      const r2 = await api("/api/products/" + encodeURIComponent(id) + "/status")
      setStatus(r2.ok ? ((await r2.json()) as { retailers: StatusRow[] }).retailers : [])
    } finally {
      setRefreshing(false)
    }
  }, [id])

  useEffect(() => {
    if (!id || !detail) return
    const run = () => {
      if (document.hidden) return
      void (async () => {
        const r2 = await api("/api/products/" + encodeURIComponent(id) + "/status")
        setStatus(r2.ok ? ((await r2.json()) as { retailers: StatusRow[] }).retailers : [])
      })()
    }
    const t = setInterval(run, STATUS_POLL_MS)
    return () => clearInterval(t)
  }, [id, detail])

  if (!rawId) {
    return (
      <PageShell>
        <p className="text-destructive text-sm">Missing product id.</p>
        <Button variant="link" className="mt-2 px-0" asChild>
          <Link to="/">← Back to tracker</Link>
        </Button>
      </PageShell>
    )
  }

  if (loading) {
    return (
      <PageShell>
        <div className="flex justify-center py-16">
          <LoadingSpinner label="Loading product" size="lg" />
        </div>
      </PageShell>
    )
  }

  if (err || !detail) {
    return (
      <PageShell>
        <p className="text-destructive text-sm">Product not found.</p>
        <Button variant="link" className="mt-2 px-0" asChild>
          <Link to="/">← Back to tracker</Link>
        </Button>
      </PageShell>
    )
  }

  const byRet = Object.fromEntries((status ?? []).map((x) => [x.retailer, x]))
  const anyInStock = statusLoading
    ? false
    : detail.watches.some((w) => byRet[w.source]?.in_stock === true)
  const bestPrice = statusLoading
    ? null
    : detail.watches.reduce<number | null>((best, w) => {
        const pr = byRet[w.source]?.price_inr
        if (pr == null || pr <= 0) return best
        if (best == null || pr < best) return pr
        return best
      }, null)

  return (
    <PageShell className="space-y-8">
      <div className="flex flex-wrap items-center gap-3">
        <Button variant="outline" size="sm" className="w-fit shrink-0" asChild>
          <Link to="/">← Tracker</Link>
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          className="ml-auto w-fit"
          onClick={() => void refreshData()}
          disabled={refreshing || loading}
        >
          {refreshing ? (
            <span className="inline-flex items-center gap-2">
              <LoadingSpinner size="sm" label="Refreshing" />
              Refreshing…
            </span>
          ) : (
            "Refresh"
          )}
        </Button>
      </div>

      <div
        className={cn(
          "rounded-xl border-2 px-5 py-4 shadow-sm",
          statusLoading
            ? "border-border/80 bg-muted/30"
            : anyInStock
              ? "border-emerald-500/60 bg-emerald-500/9"
              : "border-border/80 bg-muted/40",
        )}
      >
        <p className="text-[0.65rem] font-medium uppercase tracking-wide text-muted-foreground">Latest signal</p>
        <p className="mt-1 flex min-h-7 items-center gap-2 font-heading text-lg font-semibold tracking-tight">
          {statusLoading ? (
            <LoadingSpinner size="sm" label="Loading latest store checks" />
          ) : anyInStock ? (
            "In stock — at least one listing"
          ) : (
            "Not in stock or unknown — check each store below"
          )}
        </p>
        <div className="mt-2 flex flex-wrap gap-3 text-sm">
          <span>
            <span className="text-muted-foreground">Best seen price: </span>
            <span className="tabular-nums font-semibold">
              {statusLoading ? "—" : formatInr(bestPrice)}
            </span>
          </span>
        </div>
      </div>

      <div className="flex flex-col gap-6 sm:flex-row sm:items-start">
        {detail.image_url ? (
          <img
            src={detail.image_url}
            alt=""
            className="mx-auto w-full max-w-[220px] rounded-xl border border-border object-contain shadow-sm sm:mx-0"
          />
        ) : (
          <div className="flex size-[128px] items-center justify-center rounded-xl border border-border bg-muted text-4xl shadow-sm">
            {detail.emoji || "📦"}
          </div>
        )}
        <div className="min-w-0 flex-1 space-y-2">
          <PageHeader
            title={`${detail.emoji ? detail.emoji + " " : ""}${detail.name}`}
            description={[detail.brand, detail.category].filter(Boolean).join(" · ") || detail.category}
          />
        </div>
      </div>

      <section aria-label="Per-store status">
        <h2 className="mb-3 font-heading text-sm font-semibold">Where it&apos;s tracked</h2>
        <p className="mb-3 text-[0.7rem] text-muted-foreground">
          Stock and price per retailer — the fields people care about before opening a buy link.
        </p>
        <div className="overflow-hidden rounded-xl border border-border/80 shadow-sm">
          <Table>
            <TableHeader>
              <TableRow className="bg-muted/40 hover:bg-muted/40">
                <TableHead scope="col">Store</TableHead>
                <TableHead scope="col">Stock</TableHead>
                <TableHead scope="col">Price</TableHead>
                <TableHead scope="col">Last check</TableHead>
                <TableHead scope="col">Buy</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {detail.watches.map((w) => {
                const st = byRet[w.source]
                const stock = statusLoading ? undefined : st?.in_stock
                return (
                  <TableRow key={w.source}>
                    <TableCell className="font-medium capitalize">{w.source}</TableCell>
                    <TableCell>
                      {statusLoading ? (
                        <LoadingSpinner size="sm" label="Loading stock status" />
                      ) : stock === true ? (
                        <Badge className="border-0 bg-emerald-600 text-white hover:bg-emerald-600">In stock</Badge>
                      ) : stock === false ? (
                        <Badge variant="secondary">Out</Badge>
                      ) : (
                        <Badge variant="outline">Unknown</Badge>
                      )}
                    </TableCell>
                    <TableCell className="tabular-nums font-medium">
                      {statusLoading ? "—" : formatInr(st?.price_inr ?? null)}
                    </TableCell>
                    <TableCell className="text-[0.65rem] text-muted-foreground">
                      {statusLoading ? "—" : formatShortDate(st?.last_scrape_at ?? null)}
                    </TableCell>
                    <TableCell>
                      <a
                        href={w.url}
                        className="text-primary text-xs font-medium underline-offset-4 hover:underline"
                        target="_blank"
                        rel="noopener noreferrer"
                      >
                        Open listing →
                      </a>
                    </TableCell>
                  </TableRow>
                )
              })}
            </TableBody>
          </Table>
        </div>
      </section>
    </PageShell>
  )
}
