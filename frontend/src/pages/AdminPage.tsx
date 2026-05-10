import { useCallback, useEffect, useMemo, useRef, useState } from "react"
import { Link, Navigate } from "react-router-dom"
import { api, readErrorMessage } from "@/lib/api"
import { useAuth } from "@/auth/AuthContext"
import { formatShortDate } from "@/lib/format"
import { PageShell } from "@/components/blocks/PageShell"
import { LoadingSpinner } from "@/components/blocks/LoadingSpinner"
import { PageHeader } from "@/components/blocks/PageHeader"
import { StatCard } from "@/components/blocks/StatCard"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { HugeiconsIcon } from "@hugeicons/react"
import { Edit02Icon } from "@hugeicons/core-free-icons"

type AuthSettings = {
  jwt_algorithm: string
  jwt_expire_seconds: number
  open_registration: boolean
  bootstrap_admin_env_configured: boolean
  requests_per_hour_per_ip: number
  cors_origins: string
  using_default_jwt_secret: boolean
  registered_users: number
  note: string
}

type AdminWatch = {
  source: string
  url: string
  asin: string | null
  affiliate_tag: string | null
  poll_seconds: number | null
  db_watch_id: number | null
}

type AdminProduct = {
  id: string
  name: string
  brand: string | null
  category: string
  emoji: string | null
  colour: number | null
  image_url: string | null
  watches: AdminWatch[]
}

type ReqRow = {
  id: number
  user_id: number
  raw_url: string
  desired_product_name: string | null
  created_at: string
}

type PlatformSourceRow = {
  type: string
  poll_seconds: number
  ordinal: number
  enabled?: boolean
  category?: string
  url?: string | null
  seed_urls?: string[]
  subreddits?: string[]
}

type StockFetchSettings = {
  jitter_max_seconds: number
  max_concurrent_requests: number
  max_concurrent_playwright: number
  playwright_stealth: boolean
  playwright_locale: string
  playwright_timezone_id: string
}

type IngestionConfig = {
  config_reload_seconds: number
  defaults_poll_seconds: number
  platform_sources: PlatformSourceRow[]
  stock_fetch: StockFetchSettings
}

type Tab = "queue" | "catalog" | "auth"

function formatPollInterval(seconds: number): string {
  if (seconds < 120) return `${seconds}s`
  if (seconds < 3600) return `${Math.round(seconds / 60)} min`
  if (seconds < 86400) return `${Math.round(seconds / 3600)} hr`
  return `${Math.round(seconds / 86400)} d`
}

function summarizePlatformSource(src: PlatformSourceRow): string {
  if (src.url) return src.url.length > 72 ? `${src.url.slice(0, 69)}…` : src.url
  const seeds = src.seed_urls?.length ?? 0
  if (seeds > 0) return `${seeds} search seed${seeds === 1 ? "" : "s"}`
  const subs = src.subreddits?.length ?? 0
  if (subs > 0)
    return `${src.subreddits!.slice(0, 3).map((s) => `r/${s}`).join(", ")}${subs > 3 ? "…" : ""}`
  return "—"
}

function watchPollLabel(pollSeconds: number | null, defaultSeconds: number): string {
  if (pollSeconds != null) return `${pollSeconds}s`
  return `default (${defaultSeconds}s)`
}

/** Keep the previous slug when still present; otherwise first product. If `products` is empty, keep `previousId` (may be ""). */
function resolveCatalogSelection(products: AdminProduct[], previousId: string): string {
  if (products.length === 0) return previousId
  if (previousId && products.some((p) => p.id === previousId)) return previousId
  return products[0].id
}

type AdminCatalogApiJson = {
  defaults_poll_seconds?: number
  products?: AdminProduct[]
}

type AdminCatalogStateSlice = {
  defaults_poll_seconds: number
  products: AdminProduct[]
}

/** Normalizes GET /api/admin/catalog JSON and computes the next selection in one place. */
function applyAdminCatalogResponse(
  json: AdminCatalogApiJson,
  previousSelectedId: string,
): { catalogData: AdminCatalogStateSlice; selectedId: string } {
  const products = json.products ?? []
  const catalogData: AdminCatalogStateSlice = {
    defaults_poll_seconds: json.defaults_poll_seconds ?? 60,
    products,
  }
  return {
    catalogData,
    selectedId: resolveCatalogSelection(products, previousSelectedId),
  }
}

/** One line of badges: each listing = retailer + poll (or default). */
function ProductListingsSummary({
  product,
  defaultPollSeconds,
}: {
  product: AdminProduct
  defaultPollSeconds: number
}) {
  if (product.watches.length === 0) {
    return <span className="text-xs text-muted-foreground">No retailer URLs</span>
  }
  return (
    <div className="flex max-w-[min(100%,520px)] flex-wrap gap-1">
      {product.watches.map((w, i) => (
        <Badge
          key={w.db_watch_id != null ? `w-${w.db_watch_id}` : `u-${i}-${w.url.slice(0, 24)}`}
          variant="outline"
          className="max-w-full truncate font-normal text-[0.65rem]"
          title={`${w.source} — ${w.url}`}
        >
          {w.source}: {watchPollLabel(w.poll_seconds, defaultPollSeconds)}
        </Badge>
      ))}
    </div>
  )
}

export function AdminPage() {
  const { me, loading } = useAuth()
  const [tab, setTab] = useState<Tab>("catalog")

  const [authSettings, setAuthSettings] = useState<AuthSettings | null>(null)

  const [catalogData, setCatalogData] = useState<{
    defaults_poll_seconds: number
    products: AdminProduct[]
  } | null>(null)
  const [ingestionConfig, setIngestionConfig] = useState<IngestionConfig | null>(null)
  const [catalogSearch, setCatalogSearch] = useState("")
  const [catalogDetailOpen, setCatalogDetailOpen] = useState(false)
  const [selectedId, setSelectedId] = useState("")
  const selectedIdRef = useRef(selectedId)
  selectedIdRef.current = selectedId
  const [pName, setPName] = useState("")
  const [pCategory, setPCategory] = useState("")
  const [pBrand, setPBrand] = useState("")
  const [pEmoji, setPEmoji] = useState("")
  const [pColour, setPColour] = useState("")
  const [pImage, setPImage] = useState("")
  const [catalogMsg, setCatalogMsg] = useState<string | null>(null)

  const [rows, setRows] = useState<ReqRow[] | null>(null)
  const [pick, setPick] = useState<ReqRow | null>(null)
  const [productId, setProductId] = useState("")
  const [name, setName] = useState("")
  const [category, setCategory] = useState("tech")
  const [brand, setBrand] = useState("")
  const [pollSeconds, setPollSeconds] = useState("")
  const [imageUrl, setImageUrl] = useState("")
  const [affiliateTag, setAffiliateTag] = useState("")
  const [formErr, setFormErr] = useState<string | null>(null)
  const [approvePrefillBusy, setApprovePrefillBusy] = useState(false)
  const [approvePrefillNote, setApprovePrefillNote] = useState<string | null>(null)
  const [approvePrefillPrice, setApprovePrefillPrice] = useState<number | null>(null)
  const [approvePrefillMrp, setApprovePrefillMrp] = useState<number | null>(null)
  const [approvePrefillStock, setApprovePrefillStock] = useState<boolean | null>(null)

  const [bulkPollSeconds, setBulkPollSeconds] = useState("")

  const loadQueue = useCallback(async () => {
    const r = await api("/api/admin/requests?status=pending")
    if (!r.ok) return
    setRows((await r.json()) as ReqRow[])
  }, [])

  const loadAuth = useCallback(async () => {
    const r = await api("/api/admin/settings/auth")
    if (!r.ok) return
    setAuthSettings((await r.json()) as AuthSettings)
  }, [])

  const loadCatalog = useCallback(async () => {
    const r = await api("/api/admin/catalog")
    if (!r.ok) return
    const j = (await r.json()) as AdminCatalogApiJson
    const { catalogData, selectedId: nextId } = applyAdminCatalogResponse(j, selectedIdRef.current)
    setCatalogData(catalogData)
    setSelectedId(nextId)
  }, [])

  const loadIngestionConfig = useCallback(async () => {
    const r = await api("/api/admin/ingestion-config")
    if (!r.ok) return
    const data = (await r.json()) as Partial<IngestionConfig> & {
      platform_sources: PlatformSourceRow[]
      stock_fetch?: StockFetchSettings
    }
    const stock_fetch = data.stock_fetch ?? {
      jitter_max_seconds: 3,
      max_concurrent_requests: 4,
      max_concurrent_playwright: 2,
      playwright_stealth: true,
      playwright_locale: "en-IN",
      playwright_timezone_id: "Asia/Kolkata",
    }
    setIngestionConfig({
      config_reload_seconds: data.config_reload_seconds ?? 60,
      defaults_poll_seconds: data.defaults_poll_seconds ?? 60,
      stock_fetch,
      platform_sources: (data.platform_sources ?? []).map((src, idx) => {
        const priorSame = (data.platform_sources ?? []).slice(0, idx).filter((x) => x.type === src.type).length
        return { ...src, ordinal: priorSame, enabled: src.enabled !== false }
      }),
    })
  }, [])

  useEffect(() => {
    if (me?.role !== "admin") return
    void loadQueue()
  }, [me?.role, loadQueue])

  useEffect(() => {
    if (me?.role !== "admin" || tab !== "auth") return
    void loadAuth()
  }, [me?.role, tab, loadAuth])

  useEffect(() => {
    if (me?.role !== "admin" || tab !== "catalog") return
    void loadCatalog()
    void loadIngestionConfig()
  }, [me?.role, tab, loadCatalog, loadIngestionConfig])

  const selected = catalogData?.products.find((p) => p.id === selectedId)

  const defaultsPollSeconds = catalogData?.defaults_poll_seconds ?? 60

  const filteredCatalogProducts = useMemo(() => {
    if (!catalogData?.products.length) return []
    const q = catalogSearch.trim().toLowerCase()
    if (!q) return catalogData.products
    return catalogData.products.filter((p) => {
      const brand = (p.brand ?? "").toLowerCase()
      return (
        p.id.toLowerCase().includes(q) ||
        p.name.toLowerCase().includes(q) ||
        p.category.toLowerCase().includes(q) ||
        brand.includes(q) ||
        p.watches.some(
          (w) =>
            w.source.toLowerCase().includes(q) ||
            w.url.toLowerCase().includes(q) ||
            (w.asin ?? "").toLowerCase().includes(q),
        )
      )
    })
  }, [catalogData, catalogSearch])

  useEffect(() => {
    if (!selected) return
    setPName(selected.name)
    setPCategory(selected.category)
    setPBrand(selected.brand ?? "")
    setPEmoji(selected.emoji ?? "")
    setPColour(selected.colour != null ? String(selected.colour) : "")
    setPImage(selected.image_url ?? "")
  }, [selected])

  if (!loading && !me) {
    return <Navigate to="/login" replace />
  }

  if (!loading && me && me.role !== "admin") {
    return (
      <PageShell>
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <p className="text-lg font-semibold text-destructive">Access Denied</p>
          <p className="mt-2 text-sm text-muted-foreground">
            Your account does not have admin privileges.
          </p>
          <p className="mt-1 text-xs text-muted-foreground">
            Current role: <span className="font-mono">{me.role}</span>
          </p>
        </div>
      </PageShell>
    )
  }

  if (loading || !me) {
    return (
      <PageShell>
        <div className="flex justify-center py-16">
          <LoadingSpinner label="Loading admin" size="lg" />
        </div>
      </PageShell>
    )
  }

  const loadListingPreview = useCallback(async (row: ReqRow) => {
    setApprovePrefillBusy(true)
    setApprovePrefillNote(null)
    try {
      const r = await api(`/api/admin/requests/${row.id}/listing-preview`)
      const j = (await r.json()) as {
        ok?: boolean
        reason?: string
        suggested_product_id?: string | null
        name?: string | null
        brand?: string | null
        image_url?: string | null
        price_inr?: number | null
        mrp_inr?: number | null
        in_stock?: boolean | null
      }
      if (!r.ok) {
        setApprovePrefillNote(await readErrorMessage(r))
        setApprovePrefillPrice(null)
        setApprovePrefillMrp(null)
        setApprovePrefillStock(null)
        return
      }
      if (j.ok === false && j.reason) {
        setApprovePrefillNote(j.reason)
        setApprovePrefillPrice(null)
        setApprovePrefillMrp(null)
        setApprovePrefillStock(null)
        return
      }
      if (j.suggested_product_id) setProductId(j.suggested_product_id)
      if (j.name?.trim()) setName(j.name.trim())
      if (j.brand?.trim()) setBrand(j.brand.trim())
      if (j.image_url?.trim()) setImageUrl(j.image_url.trim())
      setApprovePrefillPrice(typeof j.price_inr === "number" ? j.price_inr : null)
      setApprovePrefillMrp(typeof j.mrp_inr === "number" ? j.mrp_inr : null)
      setApprovePrefillStock(typeof j.in_stock === "boolean" ? j.in_stock : null)
    } finally {
      setApprovePrefillBusy(false)
    }
  }, [])

  function openApprove(row: ReqRow) {
    setPick(row)
    setProductId("")
    setName(row.desired_product_name ?? "")
    setCategory("tech")
    setBrand("")
    setPollSeconds("")
    setImageUrl("")
    setAffiliateTag("")
    setFormErr(null)
    setApprovePrefillNote(null)
    setApprovePrefillPrice(null)
    setApprovePrefillMrp(null)
    setApprovePrefillStock(null)
    void loadListingPreview(row)
  }

  async function submitApprove(e: React.FormEvent) {
    e.preventDefault()
    if (!pick) return
    setFormErr(null)
    const body: Record<string, unknown> = {
      product_id: productId.toLowerCase(),
      name,
      category: category || "tech",
    }
    if (brand.trim()) body.brand = brand.trim()
    if (pollSeconds.trim()) {
      const n = parseInt(pollSeconds, 10)
      if (!Number.isNaN(n)) body.poll_seconds = n
    }
    if (imageUrl.trim()) body.image_url = imageUrl.trim()
    if (affiliateTag.trim()) body.affiliate_tag = affiliateTag.trim()
    const r = await api(`/api/admin/requests/${pick.id}/approve`, {
      method: "POST",
      body: JSON.stringify(body),
    })
    if (!r.ok) {
      setFormErr(await readErrorMessage(r))
      return
    }
    setPick(null)
    await loadQueue()
    await loadCatalog()
  }

  async function reject(row: ReqRow) {
    const note = window.prompt("Rejection note (optional)") ?? ""
    await api(`/api/admin/requests/${row.id}/reject`, {
      method: "POST",
      body: JSON.stringify({ admin_note: note || null }),
    })
    await loadQueue()
    if (pick?.id === row.id) setPick(null)
  }

  async function saveProductMeta() {
    if (!selectedId) return
    setCatalogMsg(null)
    const colour =
      pColour.trim() === "" ? null : (() => {
        const n = parseInt(pColour, 10)
        return Number.isNaN(n) ? null : n
      })()
    const r = await api(`/api/admin/catalog/products/${encodeURIComponent(selectedId)}`, {
      method: "PATCH",
      body: JSON.stringify({
        name: pName,
        category: pCategory || "tech",
        brand: pBrand.trim() || null,
        emoji: pEmoji.trim() || null,
        colour,
        image_url: pImage.trim() || null,
      }),
    })
    if (!r.ok) {
      setCatalogMsg(await readErrorMessage(r))
      return
    }
    setCatalogMsg("Saved. Workers pick up DB changes on reload.")
    await loadCatalog()
  }

  async function saveWatch(w: AdminWatch) {
    if (!selectedId) return
    setCatalogMsg(null)
    const payload = {
      source: w.source,
      url: w.url,
      asin: w.asin || null,
      affiliate_tag: w.affiliate_tag || null,
      poll_seconds: w.poll_seconds ?? null,
    }
    const r =
      w.db_watch_id == null
        ? await api(`/api/admin/catalog/products/${encodeURIComponent(selectedId)}/watches/override`, {
            method: "POST",
            body: JSON.stringify(payload),
          })
        : await api(`/api/admin/catalog/watches/${w.db_watch_id}`, {
            method: "PATCH",
            body: JSON.stringify(payload),
          })
    if (!r.ok) {
      setCatalogMsg(await readErrorMessage(r))
      return
    }
    setCatalogMsg("Watch updated.")
    await loadCatalog()
  }

  async function saveIngestionConfig() {
    if (!ingestionConfig) return
    setCatalogMsg(null)
    const r = await api("/api/admin/ingestion-config", {
      method: "PATCH",
      body: JSON.stringify({
        config_reload_seconds: ingestionConfig.config_reload_seconds,
        defaults_poll_seconds: ingestionConfig.defaults_poll_seconds,
        platform_sources: ingestionConfig.platform_sources.map((src) => ({
          type: src.type,
          poll_seconds: src.poll_seconds,
          enabled: src.enabled !== false,
        })),
        stock_fetch: ingestionConfig.stock_fetch,
      }),
    })
    if (!r.ok) {
      setCatalogMsg(await readErrorMessage(r))
      return
    }
    setCatalogMsg("Scrape settings saved to platform config. Workers pick them up on reload.")
    await loadIngestionConfig()
  }

  async function applyPollAllWatches(useYamlDefaultOnly: boolean) {
    setCatalogMsg(null)
    let poll_seconds: number | null = null
    if (!useYamlDefaultOnly) {
      const n = parseInt(bulkPollSeconds.trim(), 10)
      if (Number.isNaN(n) || n < 10) {
        setCatalogMsg("Enter a poll interval of at least 10 seconds, or use “Use YAML default”.")
        return
      }
      poll_seconds = n
    }
    const r = await api("/api/admin/catalog/watches/poll-all", {
      method: "POST",
      body: JSON.stringify({ poll_seconds }),
    })
    if (!r.ok) {
      setCatalogMsg(await readErrorMessage(r))
      return
    }
    const j = (await r.json()) as { updated?: number }
    setCatalogMsg(`Updated ${j.updated ?? 0} listing(s). Reload catalog to see effective intervals.`)
    await loadCatalog()
  }

  async function deleteWatch(id: number) {
    if (!window.confirm("Remove this listing from the database overlay?")) return
    setCatalogMsg(null)
    const r = await api(`/api/admin/catalog/watches/${id}`, { method: "DELETE" })
    if (!r.ok) {
      setCatalogMsg(await readErrorMessage(r))
      return
    }
    setCatalogMsg("Watch removed.")
    await loadCatalog()
  }

  const pending = rows?.length ?? 0

  return (
    <PageShell className="space-y-6">
      <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
        <PageHeader
          title="Admin Dashboard"
          description="Catalog and stock watches (poll intervals), request queue, and web API security readouts."
        />
        <Button type="button" variant="outline" size="sm" asChild>
          <Link to="/">← Back to Tracker</Link>
        </Button>
      </div>

      <Tabs value={tab} onValueChange={(v) => setTab(v as Tab)} className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="catalog" className="flex items-center gap-2">
            <span className="hidden sm:inline">{"Catalog & scraping"}</span>
            <span className="sm:hidden">Catalog</span>
          </TabsTrigger>
          <TabsTrigger value="queue" className="flex items-center gap-2">
            <span className="hidden sm:inline">Request Queue</span>
            <span className="sm:hidden">Queue</span>
            {pending > 0 && <Badge className="ml-1 h-5 min-w-5 rounded-full p-0 text-center text-[10px]">{pending}</Badge>}
          </TabsTrigger>
          <TabsTrigger value="auth" className="flex items-center gap-2">
            <span className="hidden sm:inline">Web API</span>
            <span className="sm:hidden">API</span>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="auth" className="space-y-4">
          {!authSettings ? (
            <Card>
              <CardContent className="flex justify-center py-10">
                <LoadingSpinner label="Loading settings" />
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              <p className="text-[0.75rem] leading-relaxed text-muted-foreground">
                These values come from <strong>environment variables</strong> (<span className="font-mono">WEB_*</span>) —
                they control the HTTP API (logins, registration, browser rate limits). They are{" "}
                <strong>not</strong> the same as scrape schedules in your platform config file.
              </p>
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    Web API security &amp; limits
                  </CardTitle>
                  <CardDescription>{authSettings.note}</CardDescription>
                </CardHeader>
                <CardContent className="grid gap-4 sm:grid-cols-2">
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Registered Users</p>
                    <p className="text-sm font-semibold text-foreground">{authSettings.registered_users}</p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">JWT Config</p>
                    <p className="text-sm text-foreground">
                      {authSettings.jwt_algorithm} · {Math.round(authSettings.jwt_expire_seconds / 3600)}h expiry
                    </p>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Open Registration</p>
                    <Badge variant={authSettings.open_registration ? "default" : "secondary"} className="w-fit">
                      {authSettings.open_registration ? "Enabled" : "Disabled"}
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Admin Bootstrap</p>
                    <Badge
                      variant={authSettings.bootstrap_admin_env_configured ? "default" : "secondary"}
                      className="w-fit"
                    >
                      {authSettings.bootstrap_admin_env_configured ? "Configured" : "Not set"}
                    </Badge>
                  </div>
                  <div className="space-y-1">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">Rate Limit</p>
                    <p className="text-sm text-foreground">{authSettings.requests_per_hour_per_ip}/hr per IP</p>
                  </div>
                  <div className="space-y-1 sm:col-span-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">CORS Origins</p>
                    <p className="font-mono text-xs break-all text-foreground">{authSettings.cors_origins}</p>
                  </div>
                  <div className="space-y-1 sm:col-span-2">
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">JWT Secret</p>
                    <Badge
                      variant={authSettings.using_default_jwt_secret ? "destructive" : "secondary"}
                      className="w-fit"
                    >
                      {authSettings.using_default_jwt_secret
                        ? "⚠️ Using default secret — change WEB_JWT_SECRET"
                        : "✓ Custom secret configured"}
                    </Badge>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}
        </TabsContent>

        <TabsContent value="catalog" className="space-y-6">
          <p className="text-[0.75rem] leading-relaxed text-muted-foreground">
            <strong>Product</strong> = one catalog item (name, image, category, slug). <strong>Listings</strong> = one row
            per retailer URL the worker polls (Amazon product page, Flipkart page, wishlist watch, etc.). One product can
            have many listings, each with its own poll interval. Below: global scrape limits; then the full product
            directory. <strong>Deal pipelines</strong> are separate site-wide jobs (aggregators / SERP).
          </p>
          {!ingestionConfig ? (
            <Card>
              <CardContent className="flex justify-center py-10">
                <LoadingSpinner label="Loading scrape settings" />
              </CardContent>
            </Card>
          ) : (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Scraping &amp; rate limits</CardTitle>
                <CardDescription>
                  Saves to your platform config file. Stock worker reloads on{" "}
                  {formatPollInterval(ingestionConfig.config_reload_seconds)}.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6 overflow-x-auto">
                <div>
                  <h3 className="mb-2 font-heading text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Timing
                  </h3>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Config reload (seconds)</Label>
                      <Input
                        type="number"
                        value={ingestionConfig.config_reload_seconds}
                        onChange={(e) =>
                          setIngestionConfig((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  config_reload_seconds: Number.parseInt(e.target.value || "0", 10) || 0,
                                }
                              : prev,
                          )
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Default listing poll (seconds)</Label>
                      <Input
                        type="number"
                        value={ingestionConfig.defaults_poll_seconds}
                        onChange={(e) =>
                          setIngestionConfig((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  defaults_poll_seconds: Number.parseInt(e.target.value || "0", 10) || 0,
                                }
                              : prev,
                          )
                        }
                      />
                      <p className="text-xs text-muted-foreground">
                        Used when a DB listing has no poll override ({formatPollInterval(ingestionConfig.defaults_poll_seconds)}).
                      </p>
                    </div>
                  </div>
                </div>

                <div className="rounded-lg border border-border/70 bg-muted/20 p-4 space-y-3">
                  <h3 className="font-heading text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    All tracked listings (bulk)
                  </h3>
                  <p className="text-xs text-muted-foreground">
                    Applies to every retailer URL for every product in the database. Use “YAML default” to clear per-row
                    overrides so the default above applies everywhere.
                  </p>
                  <div className="flex flex-wrap items-end gap-2">
                    <div className="space-y-1">
                      <Label htmlFor="bulk-poll">Seconds (≥10)</Label>
                      <Input
                        id="bulk-poll"
                        className="h-8 w-32 text-xs"
                        type="number"
                        min={10}
                        placeholder="e.g. 120"
                        value={bulkPollSeconds}
                        onChange={(e) => setBulkPollSeconds(e.target.value)}
                      />
                    </div>
                    <Button type="button" size="sm" onClick={() => void applyPollAllWatches(false)}>
                      Set all listings
                    </Button>
                    <Button type="button" size="sm" variant="outline" onClick={() => void applyPollAllWatches(true)}>
                      Use YAML default only
                    </Button>
                  </div>
                </div>

                <div>
                  <h3 className="mb-2 font-heading text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Fetcher / concurrency (stock scrapes)
                  </h3>
                  <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
                    <div className="space-y-2">
                      <Label>Jitter max (seconds)</Label>
                      <Input
                        type="number"
                        step="0.5"
                        value={ingestionConfig.stock_fetch.jitter_max_seconds}
                        onChange={(e) =>
                          setIngestionConfig((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  stock_fetch: {
                                    ...prev.stock_fetch,
                                    jitter_max_seconds: Number.parseFloat(e.target.value || "0") || 0,
                                  },
                                }
                              : prev,
                          )
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Max concurrent HTTP</Label>
                      <Input
                        type="number"
                        value={ingestionConfig.stock_fetch.max_concurrent_requests}
                        onChange={(e) =>
                          setIngestionConfig((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  stock_fetch: {
                                    ...prev.stock_fetch,
                                    max_concurrent_requests: Number.parseInt(e.target.value || "0", 10) || 1,
                                  },
                                }
                              : prev,
                          )
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <Label>Max concurrent Playwright</Label>
                      <Input
                        type="number"
                        value={ingestionConfig.stock_fetch.max_concurrent_playwright}
                        onChange={(e) =>
                          setIngestionConfig((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  stock_fetch: {
                                    ...prev.stock_fetch,
                                    max_concurrent_playwright: Number.parseInt(e.target.value || "0", 10) || 1,
                                  },
                                }
                              : prev,
                          )
                        }
                      />
                    </div>
                    <div className="flex items-center gap-2 pt-6">
                      <input
                        id="pw-stealth"
                        type="checkbox"
                        className="size-4 accent-primary"
                        checked={ingestionConfig.stock_fetch.playwright_stealth}
                        onChange={(e) =>
                          setIngestionConfig((prev) =>
                            prev
                              ? {
                                  ...prev,
                                  stock_fetch: { ...prev.stock_fetch, playwright_stealth: e.target.checked },
                                }
                              : prev,
                          )
                        }
                      />
                      <Label htmlFor="pw-stealth" className="font-normal">
                        Playwright stealth
                      </Label>
                    </div>
                  </div>
                </div>

                <div>
                  <h3 className="mb-2 font-heading text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                    Deal pipelines
                  </h3>
                  {ingestionConfig.platform_sources.length === 0 ? (
                    <p className="text-sm text-muted-foreground">
                      No <span className="font-mono">platform_sources</span> in config — add pipelines in YAML for
                      aggregator / SERP discovery.
                    </p>
                  ) : (
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-14">On</TableHead>
                          <TableHead>Source</TableHead>
                          <TableHead>Interval</TableHead>
                          <TableHead className="hidden md:table-cell">Detail</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {ingestionConfig.platform_sources.map((src, i) => (
                          <TableRow key={`${src.type}-${i}`}>
                            <TableCell>
                              <input
                                type="checkbox"
                                className="size-4 accent-primary"
                                checked={src.enabled !== false}
                                onChange={(e) =>
                                  setIngestionConfig((prev) => {
                                    if (!prev) return prev
                                    const nextSources = [...prev.platform_sources]
                                    nextSources[i] = { ...nextSources[i], enabled: e.target.checked }
                                    return { ...prev, platform_sources: nextSources }
                                  })
                                }
                              />
                            </TableCell>
                            <TableCell className="font-mono text-xs">{src.type}</TableCell>
                            <TableCell className="text-sm">
                              <Input
                                className="h-8 w-28 text-xs"
                                type="number"
                                value={src.poll_seconds}
                                onChange={(e) =>
                                  setIngestionConfig((prev) => {
                                    if (!prev) return prev
                                    const nextSources = [...prev.platform_sources]
                                    const parsed = Number.parseInt(e.target.value || "0", 10) || 0
                                    nextSources[i] = { ...nextSources[i], poll_seconds: parsed }
                                    return { ...prev, platform_sources: nextSources }
                                  })
                                }
                              />
                              <span className="ml-2 text-xs text-muted-foreground">
                                {formatPollInterval(src.poll_seconds)}
                              </span>
                            </TableCell>
                            <TableCell className="hidden max-w-md font-mono text-[0.65rem] text-muted-foreground md:table-cell">
                              {summarizePlatformSource(src)}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  )}
                </div>

                <div>
                  <Button type="button" size="sm" onClick={() => void saveIngestionConfig()}>
                    Save scrape settings
                  </Button>
                </div>
              </CardContent>
            </Card>
          )}
          {!catalogData ? (
            <div className="flex justify-center py-10">
              <LoadingSpinner label="Loading catalog" />
            </div>
          ) : (
            <>
              <Card>
                <CardHeader>
                  <CardTitle className="text-base">Tracked products</CardTitle>
                  <CardDescription>
                    Each row is one product. The <strong>Listings</strong> column shows every retailer URL and poll
                    interval. Use Edit for full fields and per-URL controls.
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
                    <Input
                      type="search"
                      placeholder="Search slug, name, category, brand, store, URL…"
                      value={catalogSearch}
                      onChange={(e) => setCatalogSearch(e.target.value)}
                      className="max-w-md"
                    />
                    <p className="text-xs text-muted-foreground">
                      {filteredCatalogProducts.length} of {catalogData.products.length} shown
                    </p>
                  </div>
                  <div className="overflow-x-auto rounded-lg border border-border/80">
                    <Table>
                      <TableHeader>
                        <TableRow className="bg-muted/40 hover:bg-muted/40">
                          <TableHead className="w-12 text-center">Edit</TableHead>
                          <TableHead className="w-14"> </TableHead>
                          <TableHead>Slug</TableHead>
                          <TableHead className="min-w-[140px]">Name</TableHead>
                          <TableHead className="hidden lg:table-cell">Category</TableHead>
                          <TableHead className="hidden md:table-cell">Brand</TableHead>
                          <TableHead className="min-w-[200px]">Listings (store · poll)</TableHead>
                          <TableHead className="w-16 text-right tabular-nums">#</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {filteredCatalogProducts.map((p) => (
                          <TableRow key={p.id}>
                            <TableCell className="text-center">
                              <Button
                                type="button"
                                variant="ghost"
                                size="sm"
                                className="h-8 px-2"
                                onClick={() => {
                                  setSelectedId(p.id)
                                  setCatalogDetailOpen(true)
                                }}
                              >
                                <HugeiconsIcon icon={Edit02Icon} strokeWidth={2} className="size-4" aria-hidden />
                                <span className="sr-only">Edit {p.name}</span>
                              </Button>
                            </TableCell>
                            <TableCell className="align-middle">
                              {p.image_url ? (
                                <img
                                  src={p.image_url}
                                  alt=""
                                  className="size-10 rounded-md border border-border object-cover"
                                  loading="lazy"
                                />
                              ) : (
                                <div className="size-10 rounded-md border border-dashed border-border bg-muted/50" />
                              )}
                            </TableCell>
                            <TableCell className="align-top font-mono text-[0.7rem]" title={p.id}>
                              <span className="line-clamp-2 max-w-[120px]">{p.id}</span>
                            </TableCell>
                            <TableCell className="align-top text-sm font-medium">
                              <span className="line-clamp-2" title={p.name}>
                                {p.name}
                              </span>
                            </TableCell>
                            <TableCell className="hidden align-top text-xs lg:table-cell">{p.category}</TableCell>
                            <TableCell className="hidden align-top text-xs md:table-cell">{p.brand ?? "—"}</TableCell>
                            <TableCell className="align-top">
                              <ProductListingsSummary
                                product={p}
                                defaultPollSeconds={defaultsPollSeconds}
                              />
                            </TableCell>
                            <TableCell className="align-top text-right text-sm tabular-nums text-muted-foreground">
                              {p.watches.length}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                  {filteredCatalogProducts.length === 0 ? (
                    <p className="text-sm text-muted-foreground">No products match this search.</p>
                  ) : null}
                </CardContent>
              </Card>

              {catalogMsg ? (
                <div className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/30 dark:text-emerald-200">
                  {catalogMsg}
                </div>
              ) : null}
            </>
          )}
        </TabsContent>

        <TabsContent value="queue" className="space-y-6">
          <div className="grid gap-3 sm:grid-cols-2">
            <StatCard label="Pending Requests" value={pending} hint="Approve to add watches via overlay." />
          </div>

          {!rows ? (
            <Card>
              <CardContent className="flex justify-center py-10">
                <LoadingSpinner label="Loading requests" />
              </CardContent>
            </Card>
          ) : rows.length === 0 ? (
            <Card>
              <CardContent className="flex flex-col items-center justify-center gap-2 py-12 text-center">
                                <p className="text-sm font-medium text-foreground">All caught up!</p>
                <p className="text-xs text-muted-foreground">No pending requests to review.</p>
              </CardContent>
            </Card>
          ) : (
            <div className="overflow-hidden rounded-lg border border-border/80">
              <Table>
                <TableHeader>
                  <TableRow className="bg-muted/40 hover:bg-muted/40">
                    <TableHead>ID</TableHead>
                    <TableHead className="hidden sm:table-cell">User</TableHead>
                    <TableHead className="hidden md:table-cell">Product URL</TableHead>
                    <TableHead>Hint</TableHead>
                    <TableHead className="hidden sm:table-cell">When</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {rows.map((x) => (
                    <TableRow key={x.id}>
                      <TableCell className="font-medium">#{x.id}</TableCell>
                      <TableCell className="hidden sm:table-cell text-xs text-muted-foreground">User {x.user_id}</TableCell>
                      <TableCell className="hidden md:table-cell max-w-[200px]">
                        <a
                          href={x.raw_url}
                          className="text-primary text-xs break-all underline-offset-4 hover:underline"
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          View →
                        </a>
                      </TableCell>
                      <TableCell className="text-sm">{x.desired_product_name ?? "—"}</TableCell>
                      <TableCell className="hidden sm:table-cell text-xs text-muted-foreground whitespace-nowrap">
                        {formatShortDate(x.created_at)}
                      </TableCell>
                      <TableCell className="text-right space-x-2 whitespace-nowrap">
                        <Button
                          type="button"
                          size="sm"
                          onClick={() => openApprove(x)}
                          className="gap-1"
                        >
                                                    <span className="hidden sm:inline">Approve</span>
                        </Button>
                        <AlertDialog>
                          <Button
                            type="button"
                            size="sm"
                            variant="outline"
                            className="gap-1"
                            asChild
                          >
                            <span><span className="hidden sm:inline">Reject</span></span>
                          </Button>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Reject Request #{x.id}?</AlertDialogTitle>
                              <AlertDialogDescription>
                                Add an optional note explaining why this request was rejected.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <div className="space-y-2">
                              <Label htmlFor="reject-note">Rejection Note (optional)</Label>
                              <Input id="reject-note" placeholder="Reason for rejection..." />
                            </div>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Cancel</AlertDialogCancel>
                              <AlertDialogAction
                                onClick={() => void reject(x)}
                                className="bg-destructive hover:bg-destructive/90"
                              >
                                Reject
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          )}
        </TabsContent>
      </Tabs>

      <Dialog open={catalogDetailOpen} onOpenChange={setCatalogDetailOpen}>
        <DialogContent className="max-h-[min(92vh,900px)] max-w-3xl gap-4 overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit product</DialogTitle>
            <DialogDescription>
              Slug <span className="font-mono text-foreground">{selected?.id ?? ""}</span> is fixed. Change display fields
              and retailer URLs below.
            </DialogDescription>
          </DialogHeader>
          {selected ? (
            <div className="space-y-6">
              <div className="grid max-w-2xl gap-3 sm:grid-cols-2">
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="adm-name-dlg">Name</Label>
                  <Input id="adm-name-dlg" value={pName} onChange={(e) => setPName(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="adm-cat-dlg">Category</Label>
                  <Input id="adm-cat-dlg" value={pCategory} onChange={(e) => setPCategory(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="adm-brand-dlg">Brand</Label>
                  <Input id="adm-brand-dlg" value={pBrand} onChange={(e) => setPBrand(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="adm-emoji-dlg">Emoji</Label>
                  <Input id="adm-emoji-dlg" value={pEmoji} onChange={(e) => setPEmoji(e.target.value)} />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="adm-colour-dlg">Colour (integer)</Label>
                  <Input id="adm-colour-dlg" value={pColour} onChange={(e) => setPColour(e.target.value)} />
                </div>
                <div className="space-y-2 sm:col-span-2">
                  <Label htmlFor="adm-img-dlg">Image URL</Label>
                  <Input id="adm-img-dlg" type="url" value={pImage} onChange={(e) => setPImage(e.target.value)} />
                </div>
                <div className="sm:col-span-2">
                  <Button type="button" size="sm" onClick={() => void saveProductMeta()}>
                    Save product fields
                  </Button>
                </div>
              </div>

              <div className="space-y-2">
                <h3 className="font-heading text-sm font-semibold">Listings</h3>
                <p className="text-xs text-muted-foreground">
                  Default poll when blank: {watchPollLabel(null, defaultsPollSeconds)} (from scrape settings above).
                </p>
                {selected.watches.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No retailer URLs yet for this product.</p>
                ) : (
                  <div className="overflow-hidden rounded-lg border border-border/80">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Store</TableHead>
                          <TableHead>URL</TableHead>
                          <TableHead>Poll (s)</TableHead>
                          <TableHead>DB id</TableHead>
                          <TableHead />
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selected.watches.map((w, idx) => (
                          <WatchRowEditor
                            key={`${w.url}-${idx}`}
                            watch={w}
                            onSave={(x) => void saveWatch(x)}
                            onDelete={(id) => void deleteWatch(id)}
                          />
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground">Select a product from the table.</p>
          )}
          <DialogFooter className="gap-2 sm:justify-start">
            <Button type="button" variant="outline" onClick={() => setCatalogDetailOpen(false)}>
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={!!pick} onOpenChange={(open) => !open && setPick(null)}>
        <DialogContent className="max-w-lg">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
                            Approve Request #{pick?.id}
            </DialogTitle>
            <DialogDescription>
              Define the catalog slug and product metadata. For Amazon India, Flipkart, and AJIO product links, details are
              filled from the live listing when you open this dialog.
            </DialogDescription>
          </DialogHeader>
          {pick && (
            <form onSubmit={submitApprove} className="space-y-4">
              <div className="flex flex-wrap items-center gap-2">
                {approvePrefillBusy && (
                  <span className="inline-flex items-center gap-2 text-xs text-muted-foreground">
                    <LoadingSpinner size="sm" label="Fetching listing" />
                    Fetching listing…
                  </span>
                )}
                <Button
                  type="button"
                  variant="secondary"
                  size="sm"
                  className="h-8"
                  disabled={approvePrefillBusy}
                  onClick={() => void loadListingPreview(pick)}
                >
                  Refetch from listing
                </Button>
              </div>
              {approvePrefillNote && (
                <p className="text-xs text-muted-foreground">{approvePrefillNote}</p>
              )}
              {(approvePrefillPrice != null || approvePrefillMrp != null || approvePrefillStock != null) && (
                <div className="rounded-md border border-border/70 bg-muted/30 px-3 py-2 text-xs text-muted-foreground">
                  <span className="mr-3">
                    Stock:{" "}
                    {approvePrefillStock == null ? "Unknown" : approvePrefillStock ? "In stock" : "Out of stock"}
                  </span>
                  <span className="mr-3">
                    Price: {approvePrefillPrice == null ? "Unknown" : `Rs ${approvePrefillPrice}`}
                  </span>
                  <span>MRP: {approvePrefillMrp == null ? "Unknown" : `Rs ${approvePrefillMrp}`}</span>
                </div>
              )}
              <div className="space-y-2">
                <Label htmlFor="apid">Product ID (slug)</Label>
                <Input
                  id="apid"
                  required
                  placeholder="e.g., ps5_model_a"
                  value={productId}
                  onChange={(e) => setProductId(e.target.value)}
                  className="font-mono text-sm"
                />
                <p className="text-xs text-muted-foreground">Unique identifier, lowercase with underscores</p>
              </div>
              <div className="space-y-2">
                <Label htmlFor="aname">Display Name</Label>
                <Input
                  id="aname"
                  required
                  placeholder="e.g., PlayStation 5"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="acat">Category</Label>
                  <Input
                    id="acat"
                    placeholder="tech"
                    value={category}
                    onChange={(e) => setCategory(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="abrand">Brand (optional)</Label>
                  <Input
                    id="abrand"
                    placeholder="Sony"
                    value={brand}
                    onChange={(e) => setBrand(e.target.value)}
                  />
                </div>
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="apoll">Poll Interval (seconds)</Label>
                  <Input
                    id="apoll"
                    type="number"
                    placeholder="3600"
                    value={pollSeconds}
                    onChange={(e) => setPollSeconds(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="aatag">Amazon Affiliate Tag</Label>
                  <Input
                    id="aatag"
                    placeholder="tag-20"
                    value={affiliateTag}
                    onChange={(e) => setAffiliateTag(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="aimg">Image URL</Label>
                <Input
                  id="aimg"
                  type="url"
                  placeholder="https://example.com/image.jpg"
                  value={imageUrl}
                  onChange={(e) => setImageUrl(e.target.value)}
                />
              </div>
              {formErr && (
                <div className="rounded-lg border border-destructive/50 bg-destructive/10 p-3 text-sm text-destructive">
                  {formErr}
                </div>
              )}
              <DialogFooter>
                <Button type="button" variant="outline" onClick={() => setPick(null)}>
                  Cancel
                </Button>
                <Button type="submit" className="gap-2">
                                    Approve Request
                </Button>
              </DialogFooter>
            </form>
          )}
        </DialogContent>
      </Dialog>
    </PageShell>
  )
}

function WatchRowEditor({
  watch: initial,
  onSave,
  onDelete,
}: {
  watch: AdminWatch
  onSave: (w: AdminWatch) => void
  onDelete: (id: number) => void
}) {
  const [source, setSource] = useState(initial.source)
  const [url, setUrl] = useState(initial.url)
  const [poll, setPoll] = useState(initial.poll_seconds != null ? String(initial.poll_seconds) : "")
  const [asin, setAsin] = useState(initial.asin ?? "")
  const [aff, setAff] = useState(initial.affiliate_tag ?? "")

  useEffect(() => {
    setSource(initial.source)
    setUrl(initial.url)
    setPoll(initial.poll_seconds != null ? String(initial.poll_seconds) : "")
    setAsin(initial.asin ?? "")
    setAff(initial.affiliate_tag ?? "")
  }, [initial])

  const editable = initial.db_watch_id != null

  return (
    <TableRow>
      <TableCell>
        <Input
          className="h-7 text-xs"
          value={source}
          onChange={(e) => setSource(e.target.value)}
        />
      </TableCell>
      <TableCell className="max-w-[200px]">
        <Input className="h-7 text-xs" value={url} onChange={(e) => setUrl(e.target.value)} />
      </TableCell>
      <TableCell>
        <Input
          className="h-7 w-20 text-xs"
          value={poll}
          onChange={(e) => setPoll(e.target.value)}
        />
      </TableCell>
      <TableCell>
        {editable ? (
          <span className="font-mono text-[0.65rem]">{initial.db_watch_id}</span>
        ) : (
          <Badge variant="secondary" className="text-[0.6rem]">
            YAML only
          </Badge>
        )}
      </TableCell>
      <TableCell className="space-x-1">
        <Button
          type="button"
          size="sm"
          variant="secondary"
          onClick={() =>
            onSave({
              ...initial,
              source,
              url,
              asin: asin.trim() || null,
              affiliate_tag: aff.trim() || null,
              poll_seconds: (() => {
                if (poll.trim() === "") return null
                const n = parseInt(poll, 10)
                return Number.isNaN(n) ? null : n
              })(),
            })
          }
        >
          {editable ? "Save" : "Save override"}
        </Button>
        {editable && (
          <>
            <Button
              type="button"
              size="sm"
              variant="destructive"
              onClick={() => initial.db_watch_id != null && onDelete(initial.db_watch_id)}
            >
              Remove
            </Button>
          </>
        )}
      </TableCell>
    </TableRow>
  )
}
