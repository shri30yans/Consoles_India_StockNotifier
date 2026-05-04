import { HugeiconsIcon } from "@hugeicons/react"
import { Loading02Icon } from "@hugeicons/core-free-icons"
import { cn } from "@/lib/utils"

const sizeClasses = {
  sm: "size-5",
  md: "size-8",
  lg: "size-10",
} as const

type Size = keyof typeof sizeClasses

type LoadingSpinnerProps = {
  /** Screen reader / `aria-label` text */
  label?: string
  size?: Size
  className?: string
  iconClassName?: string
}

/**
 * Spinner using {@link https://hugeicons.com/docs/icons/core-free-icons | Hugeicons} `Loading02Icon`
 * (same icon set as the rest of the UI). Pair with `animate-spin` for motion.
 */
export function LoadingSpinner({
  label = "Loading",
  size = "md",
  className,
  iconClassName,
}: LoadingSpinnerProps) {
  return (
    <div
      className={cn("inline-flex items-center justify-center", className)}
      role="status"
      aria-live="polite"
      aria-label={label}
    >
      <HugeiconsIcon
        icon={Loading02Icon}
        strokeWidth={2}
        className={cn(sizeClasses[size], "animate-spin text-primary", iconClassName)}
        aria-hidden
      />
    </div>
  )
}
