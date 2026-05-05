import { useCallback, useEffect, useState } from "react"
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

type AuthSettings = {
  config_path: string
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
  has_catalog_row: boolean
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
  category?: string
  url?: string | null
  seed_urls?: string[]
  subreddits?: string[]
}

type IngestionConfig = {
  config_path: string
  config_reload_seconds: number
  defaults_poll_seconds: number
  platform_sources: PlatformSourceRow[]
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

export function AdminPage() {
  const { me, loading } = useAuth()
  const [tab, setTab] = useState<Tab>("catalog")

  const [authSettings, setAuthSettings] = useState<AuthSettings | null>(null)

  const [catalogData, setCatalogData] = useState<{ config_path: string; products: AdminProduct[] } | null>(null)
  const [ingestionConfig, setIngestionConfig] = useState<IngestionConfig | null>(null)
  const [selectedId, setSelectedId] = useState("")
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

  const [nwSource, setNwSource] = useState("amazon")
  const [nwUrl, setNwUrl] = useState("")
  const [nwAsin, setNwAsin] = useState("")
  const [nwAff, setNwAff] = useState("")
  const [nwPoll, setNwPoll] = useState("")

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
    const j = (await r.json()) as { config_path: string; products: AdminProduct[] }
    setCatalogData(j)
    setSelectedId((prev) => {
      if (prev && j.products.some((p) => p.id === prev)) return prev
      return j.products[0]?.id ?? ""
    })
  }, [])

  const loadIngestionConfig = useCallback(async () => {
    const r = await api("/api/admin/ingestion-config")
    if (!r.ok) return
    const data = (await r.json()) as IngestionConfig
    setIngestionConfig({
      ...data,
      platform_sources: data.platform_sources.map((src, idx) => {
        const priorSame = data.platform_sources.slice(0, idx).filter((x) => x.type === src.type).length
        return { ...src, ordinal: priorSame }
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
    setCatalogMsg("Saved. Workers reload merged config on their schedule.")
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
        })),
      }),
    })
    if (!r.ok) {
      setCatalogMsg(await readErrorMessage(r))
      return
    }
    setCatalogMsg("Ingestion config saved.")
    await loadIngestionConfig()
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

  async function addWatch() {
    if (!selectedId || !nwUrl.trim()) return
    setCatalogMsg(null)
    const poll =
      nwPoll.trim() === "" ? null : (() => {
        const n = parseInt(nwPoll, 10)
        return Number.isNaN(n) ? null : n
      })()
    const r = await api(`/api/admin/catalog/products/${encodeURIComponent(selectedId)}/watches`, {
      method: "POST",
      body: JSON.stringify({
        source: nwSource.trim(),
        url: nwUrl.trim(),
        asin: nwAsin.trim() || null,
        affiliate_tag: nwAff.trim() || null,
        poll_seconds: poll,
      }),
    })
    if (!r.ok) {
      setCatalogMsg(await readErrorMessage(r))
      return
    }
    setNwUrl("")
    setNwAsin("")
    setNwAff("")
    setNwPoll("")
    setCatalogMsg("Watch added to SQLite overlay.")
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
                <strong>not</strong> the same as scrape schedules in your YAML file. The path below is the{" "}
                <strong>platform config file</strong> path this server was started with (workers should use the same file).
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
                    <p className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
                      Platform config file (path)
                    </p>
                    <p className="font-mono text-xs break-all text-foreground">{authSettings.config_path}</p>
                  </div>
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
            <strong>Products &amp; listings:</strong> edits below write to the <strong>database catalog</strong>. They merge
            with your platform YAML for display and polling. Each listing can have its own{" "}
            <strong>poll interval</strong> (seconds between scrapes).{" "}
            <strong>Deal pipelines</strong> (Amazon SERP, DesiDime, Reddit, etc.) are configured in the same YAML and can
            be edited below from this page.
          </p>
          {ingestionConfig && ingestionConfig.platform_sources.length > 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Deal ingestion (YAML)</CardTitle>
                <CardDescription>
                  Schedules for site-wide deal scrapers in{" "}
                  <span className="font-mono break-all">{ingestionConfig.config_path}</span>. Reload every{" "}
                  {ingestionConfig.config_reload_seconds}s.
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4 overflow-x-auto">
                <div className="grid gap-3 sm:grid-cols-2">
                  <div className="space-y-2">
                    <Label>Config reload interval (seconds)</Label>
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
                    <Label>Default watch poll (seconds)</Label>
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
                      {formatPollInterval(ingestionConfig.defaults_poll_seconds)} when a listing omits poll seconds.
                    </p>
                  </div>
                </div>
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Source type</TableHead>
                      <TableHead>Interval</TableHead>
                      <TableHead className="hidden md:table-cell">Detail</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {ingestionConfig.platform_sources.map((src, i) => (
                      <TableRow key={`${src.type}-${i}`}>
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
                          <span className="ml-2 text-xs text-muted-foreground">{formatPollInterval(src.poll_seconds)}</span>
                        </TableCell>
                        <TableCell className="hidden max-w-md font-mono text-[0.65rem] text-muted-foreground md:table-cell">
                          {summarizePlatformSource(src)}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                <div>
                  <Button type="button" size="sm" onClick={() => void saveIngestionConfig()}>
                    Save ingestion config
                  </Button>
                </div>
              </CardContent>
            </Card>
          ) : ingestionConfig && ingestionConfig.platform_sources.length === 0 ? (
            <Card>
              <CardHeader>
                <CardTitle className="text-base">Deal ingestion (YAML)</CardTitle>
                <CardDescription>
                  No <span className="font-mono">platform_sources</span> entries in{" "}
                  <span className="font-mono break-all">{ingestionConfig.config_path}</span>. Add pipelines there to
                  control aggregator / SERP scrape rates.
                </CardDescription>
              </CardHeader>
            </Card>
          ) : null}
          {!catalogData ? (
            <div className="flex justify-center py-10">
              <LoadingSpinner label="Loading catalog" />
            </div>
          ) : (
            <>
              <div className="text-[0.7rem] text-muted-foreground">
                Merged from <span className="font-mono">{catalogData.config_path}</span>
              </div>
              <div className="flex flex-wrap items-end gap-3">
                <div className="space-y-2">
                  <Label>Product</Label>
                  <select
                    className="flex h-8 w-[min(100%,280px)] rounded-md border border-input bg-input/20 px-2 text-xs"
                    value={selectedId}
                    onChange={(e) => setSelectedId(e.target.value)}
                  >
                    {catalogData.products.map((p) => (
                      <option key={p.id} value={p.id}>
                        {p.id} — {p.name}
                      </option>
                    ))}
                  </select>
                </div>
                {selected ? (
                  <Badge variant={selected.has_catalog_row ? "secondary" : "outline"}>
                    {selected.has_catalog_row ? "Has DB row" : "YAML metadata only"}
                  </Badge>
                ) : null}
              </div>

              {selected ? (
                <Card size="sm">
                  <CardHeader>
                    <CardTitle>Product fields</CardTitle>
                    <CardDescription>Slug <span className="font-mono">{selected.id}</span> cannot be changed here.</CardDescription>
                  </CardHeader>
                  <CardContent className="grid max-w-2xl gap-3 sm:grid-cols-2">
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="adm-name">Name</Label>
                      <Input id="adm-name" value={pName} onChange={(e) => setPName(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="adm-cat">Category</Label>
                      <Input id="adm-cat" value={pCategory} onChange={(e) => setPCategory(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="adm-brand">Brand</Label>
                      <Input id="adm-brand" value={pBrand} onChange={(e) => setPBrand(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="adm-emoji">Emoji</Label>
                      <Input id="adm-emoji" value={pEmoji} onChange={(e) => setPEmoji(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label htmlFor="adm-colour">Colour (integer)</Label>
                      <Input id="adm-colour" value={pColour} onChange={(e) => setPColour(e.target.value)} />
                    </div>
                    <div className="space-y-2 sm:col-span-2">
                      <Label htmlFor="adm-img">Image URL</Label>
                      <Input id="adm-img" type="url" value={pImage} onChange={(e) => setPImage(e.target.value)} />
                    </div>
                    <div className="sm:col-span-2">
                      <Button type="button" size="sm" onClick={() => void saveProductMeta()}>
                        Save product fields
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ) : null}

              {selected && selected.watches.length > 0 ? (
                <div className="space-y-2">
                  <h3 className="font-heading text-sm font-semibold">Listings</h3>
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
                </div>
              ) : null}

              {selected ? (
                <Card size="sm">
                  <CardHeader>
                    <CardTitle>Add listing (SQLite)</CardTitle>
                    <CardDescription>Creates a catalog row for this product first if needed.</CardDescription>
                  </CardHeader>
                  <CardContent className="grid max-w-2xl gap-3 sm:grid-cols-2">
                    <div className="space-y-2">
                      <Label>Source</Label>
                      <Input value={nwSource} onChange={(e) => setNwSource(e.target.value)} placeholder="amazon" />
                    </div>
                    <div className="space-y-2 sm:col-span-2">
                      <Label>Product URL</Label>
                      <Input value={nwUrl} onChange={(e) => setNwUrl(e.target.value)} type="url" required />
                    </div>
                    <div className="space-y-2">
                      <Label>ASIN (optional)</Label>
                      <Input value={nwAsin} onChange={(e) => setNwAsin(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label>Affiliate tag (optional)</Label>
                      <Input value={nwAff} onChange={(e) => setNwAff(e.target.value)} />
                    </div>
                    <div className="space-y-2">
                      <Label>Poll seconds (optional)</Label>
                      <Input value={nwPoll} onChange={(e) => setNwPoll(e.target.value)} type="number" />
                    </div>
                    <div className="sm:col-span-2">
                      <Button type="button" size="sm" onClick={() => void addWatch()}>
                        Add watch
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ) : null}

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
        {editable ? (
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
