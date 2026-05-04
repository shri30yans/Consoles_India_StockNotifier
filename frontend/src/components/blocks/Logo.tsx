import { BRAND_INITIAL } from "@/lib/brand"

export function Logo({ className = "size-9" }: { className?: string }) {
  return (
    <div className={`relative overflow-hidden rounded-lg shadow-sm ring-1 ring-primary/20 bg-primary ${className}`}>
      {/* Text overlay */}
      <div className="relative flex h-full w-full items-center justify-center text-sm font-bold text-primary-foreground">
        {BRAND_INITIAL}
      </div>
    </div>
  )
}
