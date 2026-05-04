export function formatInr(n: number | null | undefined): string {
  if (n == null || Number.isNaN(n)) return "—"
  return `₹${Number(n).toLocaleString("en-IN", { maximumFractionDigits: 0 })}`
}

export function formatShortDate(iso: string | null | undefined): string {
  if (!iso) return "—"
  const d = new Date(iso)
  if (Number.isNaN(d.getTime())) return "—"
  return d.toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  })
}
