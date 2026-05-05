import { useState } from "react"
import { Link } from "react-router-dom"
import { apiJson } from "@/lib/api"
import { BRAND_TAGLINE } from "@/lib/brand"
import { formatShortDate } from "@/lib/format"
import { useAuth } from "@/auth/AuthContext"
import { FetchErrorPanel } from "@/components/blocks/FetchErrorPanel"
import { PageShell } from "@/components/blocks/PageShell"
import { PageHeader } from "@/components/blocks/PageHeader"
import { EmptyState } from "@/components/blocks/EmptyState"
import { LoadingSpinner } from "@/components/blocks/LoadingSpinner"
import { useRemoteQuery } from "@/hooks/useRemoteQuery"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"

/** Matches GET /api/products — minimal fields for the index. */
type Product = {
  id: string
  name: string
  any_in_stock?: boolean
  last_updated: string | null
}

function parseProductList(raw: unknown): Product[] {
  if (!Array.isArray(raw)) return []
  return raw.map((row) => {
    const p = row as Product
    return {
      id: p.id,
      name: p.name,
      any_in_stock: Boolean(p.any_in_stock),
      last_updated: p.last_updated ?? null,
    }
  })
}

export function CatalogPage() {
  const { me } = useAuth()
  const [sort, setSort] = useState("updated")
  const [searchQuery, setSearchQuery] = useState("")
  const addProductTo = me ? "/request" : "/login?next=%2Frequest"

  const { query, retry } = useRemoteQuery(
    `catalog:${sort}`,
    async (signal) =>
      parseProductList(
        await apiJson<unknown>(`/api/products?sort=${encodeURIComponent(sort)}`, { signal }),
      ),
    { fallbackMessage: "Failed to load products" },
  )

  if (query.status === "loading") {
    return (
      <PageShell>
        <div className="flex justify-center py-16">
          <LoadingSpinner label="Loading tracker" size="lg" />
        </div>
      </PageShell>
    )
  }

  if (query.status === "error") {
    return (
      <PageShell className="space-y-4">
        <PageHeader title="Live Availability" description={BRAND_TAGLINE} />
        <FetchErrorPanel
          title={"Couldn't load products"}
          message={query.message}
          onRetry={retry}
          actions={
            <Button size="sm" variant="outline" asChild>
              <Link to="/">Back to home</Link>
            </Button>
          }
        />
      </PageShell>
    )
  }

  if (query.status !== "success") return null

  const items = query.data
  const searchLower = searchQuery.toLowerCase()
  const filteredItems = searchQuery
    ? items.filter((p) => p.name.toLowerCase().includes(searchLower))
    : items

  const inStock = filteredItems.filter((p) => p.any_in_stock).length

  return (
    <PageShell className="space-y-6">
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-3 sm:flex-row sm:items-end sm:justify-between">
          <PageHeader
            title="Live Availability"
            description={BRAND_TAGLINE}
          />
          <div className="flex flex-wrap items-center gap-2">
            <Input
              type="text"
              placeholder="Search by name…"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full sm:w-48 h-8 text-xs"
            />
            <div className="flex items-center gap-2">
              <span className="text-xs text-muted-foreground font-medium">Sort</span>
              <Select value={sort} onValueChange={setSort}>
                <SelectTrigger
                  className="w-[140px] h-8 text-xs bg-muted/60 border-border/80 hover:bg-muted/80"
                  size="sm"
                >
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="updated">Last updated</SelectItem>
                  <SelectItem value="name">Name</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </div>

      <Card className="border-border/60 bg-white dark:bg-slate-950">
        <div className="p-4 grid grid-cols-2 gap-4 sm:grid-cols-4">
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground font-medium">In Stock</p>
            <p className="text-2xl font-bold text-primary">{inStock}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground font-medium">Out of Stock</p>
            <p className="text-2xl font-bold text-sidebar-accent">
              {filteredItems.length - inStock}
            </p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground font-medium">Total Items</p>
            <p className="text-2xl font-bold text-foreground">{filteredItems.length}</p>
          </div>
          <div className="space-y-1">
            <p className="text-xs text-muted-foreground font-medium">Stock Rate</p>
            <p className="text-2xl font-bold text-primary">
              {filteredItems.length > 0 ? Math.round((inStock / filteredItems.length) * 100) : 0}%
            </p>
          </div>
        </div>
      </Card>

      {filteredItems.length === 0 ? (
        <EmptyState title={searchQuery ? "No matches" : "No products tracked yet"}>
          <p className="text-sm text-muted-foreground mb-4">
            {searchQuery ? "Try a different search." : "Start tracking products to see availability across major retailers."}
          </p>
          <Button size="xs" asChild className="gap-1">
            <Link to={addProductTo}>Add Your First Product</Link>
          </Button>
        </EmptyState>
      ) : (
        <section aria-label="Product tracker list" className="space-y-4">
          <div className="overflow-hidden rounded-lg border border-border/60 shadow-sm">
            <Table>
              <TableHeader>
                <TableRow className="bg-muted/50 hover:bg-muted/60 border-b border-border/60">
                  <TableHead className="w-[100px] text-foreground font-semibold" scope="col">
                    Status
                  </TableHead>
                  <TableHead scope="col">Product</TableHead>
                  <TableHead scope="col" className="hidden sm:table-cell whitespace-nowrap">
                    Last signal
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredItems.map((p) => (
                  <TableRow
                    key={p.id}
                    className={cn(
                      "border-l-4 transition-colors duration-150 hover:bg-muted/40",
                      p.any_in_stock ? "border-primary" : "border-border/70"
                    )}
                  >
                    <TableCell className="align-middle">
                      {p.any_in_stock ? (
                        <Badge className="border-0 bg-primary text-white hover:bg-primary/90 gap-1 shadow-lg shadow-primary/40 font-semibold">
                          <span className="h-2 w-2 rounded-full bg-white/80 animate-pulse" />
                          In stock
                        </Badge>
                      ) : (
                        <Badge className="border-0 font-semibold bg-accent text-accent-foreground">
                          Out
                        </Badge>
                      )}
                    </TableCell>
                    <TableCell className="align-middle">
                      <Link
                        to={`/product/${encodeURIComponent(p.id)}`}
                        prefetch="none"
                        className="font-semibold text-foreground underline-offset-2 hover:text-primary hover:underline transition-colors"
                      >
                        {p.name}
                      </Link>
                    </TableCell>
                    <TableCell className="align-middle text-xs text-muted-foreground whitespace-nowrap hidden sm:table-cell">
                      {formatShortDate(p.last_updated)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        </section>
      )}
    </PageShell>
  )
}
