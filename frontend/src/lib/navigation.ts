/** Internal path only; prevents open redirects via ?next=. */
export function safeNextPath(raw: string | null, fallback = "/account"): string {
  if (!raw || !raw.startsWith("/") || raw.startsWith("//")) return fallback
  return raw
}
