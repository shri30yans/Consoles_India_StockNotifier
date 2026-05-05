import { useEffect, useState } from "react"
import { apiJson } from "@/lib/api"
import { PageShell } from "@/components/blocks/PageShell"
import { LoadingSpinner } from "@/components/blocks/LoadingSpinner"
import { PageHeader } from "@/components/blocks/PageHeader"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

type Deal = {
  id: number
  product_url: string
  product_id: string | null
  retailer: string
  price_inr: number
  mrp_inr: number | null
  discount_pct: number | null
  score: number
  score_reasons: string[]
  product_title: string | null
  image_url: string | null
  is_active: boolean
  first_seen_at: string
  last_confirmed_at: string
}

const RETAILERS = ["All", "amazon", "flipkart", "ajio", "myntra"]
const DISCOUNT_FILTERS = ["All", "10%", "20%", "30%", "50%"]

export function DealsPage() {
  const [deals, setDeals] = useState<Deal[]>([])
  const [loading, setLoading] = useState(true)
  const [retailer, setRetailer] = useState("All")
  const [minDiscount, setMinDiscount] = useState("All")
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const loadDeals = async () => {
    try {
      setLoading(true)
      const minDiscountValue = minDiscount === "All" ? 0 : parseInt(minDiscount) / 100
      const retailerParam = retailer === "All" ? undefined : retailer

      const params = new URLSearchParams()
      if (retailerParam) params.append("retailer", retailerParam)
      if (minDiscountValue > 0) params.append("min_discount", minDiscountValue.toString())
      params.append("limit", "50")

      const data = await apiJson<Deal[]>(`/api/deals?${params.toString()}`)
      setDeals(Array.isArray(data) ? data : [])
      setLastRefresh(new Date())
    } catch (error) {
      console.error("Failed to load deals:", error)
      setDeals([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDeals()
    const interval = setInterval(loadDeals, 90000) // Refresh every 90 seconds
    return () => clearInterval(interval)
  }, [retailer, minDiscount])

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "bg-green-500"
    if (score >= 0.6) return "bg-blue-500"
    if (score >= 0.4) return "bg-yellow-500"
    return "bg-red-500"
  }

  const getRetailerColor = (retailer: string) => {
    const colors: Record<string, string> = {
      amazon: "bg-orange-100 text-orange-800",
      flipkart: "bg-blue-100 text-blue-800",
      ajio: "bg-purple-100 text-purple-800",
      myntra: "bg-pink-100 text-pink-800",
    }
    return colors[retailer] || "bg-gray-100 text-gray-800"
  }

  return (
    <PageShell>
      <PageHeader
        title="Live Deals"
        description="Best deals discovered from major retailers"
      />

      <div className="space-y-6">
        {/* Filters */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Filters</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 md:grid-cols-4">
              <div>
                <label className="text-xs font-semibold text-muted-foreground mb-2 block">Retailer</label>
                <Select value={retailer} onValueChange={setRetailer}>
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {RETAILERS.map((r) => (
                      <SelectItem key={r} value={r}>
                        {r}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-xs font-semibold text-muted-foreground mb-2 block">Min Discount</label>
                <Select value={minDiscount} onValueChange={setMinDiscount}>
                  <SelectTrigger className="h-9">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    {DISCOUNT_FILTERS.map((d) => (
                      <SelectItem key={d} value={d}>
                        {d}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="col-span-2 sm:col-span-1 md:col-span-2 flex items-end">
                <Button onClick={loadDeals} variant="outline" className="w-full h-9">
                  Refresh
                </Button>
              </div>
            </div>
            {lastRefresh && (
              <p className="text-xs text-muted-foreground mt-3">
                Last updated: {lastRefresh.toLocaleTimeString()}
              </p>
            )}
          </CardContent>
        </Card>

        {/* Deals Grid */}
        {loading ? (
          <Card>
            <CardContent className="flex justify-center py-10">
              <LoadingSpinner label="Loading deals" />
            </CardContent>
          </Card>
        ) : deals.length === 0 ? (
          <Card>
            <CardContent className="flex justify-center py-10">
              <p className="text-muted-foreground">No deals found matching your criteria</p>
            </CardContent>
          </Card>
        ) : (
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {deals.map((deal) => (
              <Card key={deal.id} className="overflow-hidden hover:shadow-lg transition-shadow">
                {deal.image_url && (
                  <div className="h-40 bg-gray-200 overflow-hidden flex items-center justify-center">
                    <img
                      src={deal.image_url}
                      alt={deal.product_title || "Product"}
                      className="h-full w-full object-cover"
                      onError={(e) => {
                        e.currentTarget.style.display = "none"
                      }}
                    />
                  </div>
                )}
                <CardContent className="p-4 space-y-3">
                  {/* Retailer & Score */}
                  <div className="flex items-start justify-between gap-2">
                    <Badge className={getRetailerColor(deal.retailer)}>
                      {deal.retailer.toUpperCase()}
                    </Badge>
                    <div className="flex items-center gap-1">
                      <div className={`h-2 w-12 rounded ${getScoreColor(deal.score)}`} />
                      <span className="text-xs font-semibold">{Math.round(deal.score * 100)}%</span>
                    </div>
                  </div>

                  {/* Title */}
                  <div>
                    <p className="font-semibold text-sm line-clamp-2">
                      {deal.product_title || "Unknown Product"}
                    </p>
                  </div>

                  {/* Price & Discount */}
                  <div className="space-y-1">
                    <div className="flex items-baseline gap-2">
                      <p className="text-xl font-bold">₹{(deal.price_inr / 1).toLocaleString('en-IN')}</p>
                      {deal.mrp_inr && (
                        <p className="text-sm line-through text-muted-foreground">
                          ₹{(deal.mrp_inr / 1).toLocaleString('en-IN')}
                        </p>
                      )}
                    </div>
                    {deal.discount_pct !== null && (
                      <p className="text-sm font-semibold text-green-600">
                        {Math.round(deal.discount_pct * 100)}% off
                      </p>
                    )}
                  </div>

                  {/* Score Reasons */}
                  {deal.score_reasons.length > 0 && (
                    <div className="text-xs text-muted-foreground space-y-1">
                      {deal.score_reasons.slice(0, 2).map((reason, i) => (
                        <p key={i} className="flex items-center gap-1">
                          <span className="text-green-600">•</span> {reason}
                        </p>
                      ))}
                    </div>
                  )}

                  {/* Buy Button */}
                  <a
                    href={deal.product_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <Button className="w-full" size="sm">
                      Buy on {deal.retailer.charAt(0).toUpperCase() + deal.retailer.slice(1)} →
                    </Button>
                  </a>

                  {/* Meta */}
                  <p className="text-xs text-muted-foreground">
                    Seen {Math.round((Date.now() - new Date(deal.first_seen_at).getTime()) / 60000)} min ago
                  </p>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </PageShell>
  )
}
