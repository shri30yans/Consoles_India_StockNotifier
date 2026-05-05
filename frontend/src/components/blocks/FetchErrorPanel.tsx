import type { ReactNode } from "react"
import { Button } from "@/components/ui/button"

export function FetchErrorPanel(props: {
  title: string
  message: string
  onRetry?: () => void
  actions?: ReactNode
}) {
  const { title, message, onRetry, actions } = props
  const showActions = onRetry != null || actions != null

  return (
    <div className="rounded-lg border border-destructive/40 bg-destructive/5 px-4 py-3 text-sm">
      <p className="font-medium text-destructive">{title}</p>
      <p className="mt-1 text-muted-foreground">{message}</p>
      {showActions ? (
        <div className="mt-3 flex flex-wrap gap-2">
          {onRetry != null ? (
            <Button type="button" size="sm" variant="secondary" onClick={onRetry}>
              Try again
            </Button>
          ) : null}
          {actions}
        </div>
      ) : null}
    </div>
  )
}
