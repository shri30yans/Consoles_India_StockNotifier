import type { ReactNode } from "react"

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col items-center justify-center rounded-lg border border-dashed border-border/80 py-14 text-center">
      <p className="text-sm font-medium text-muted-foreground">{title}</p>
      {children ? <div className="mt-3">{children}</div> : null}
    </div>
  )
}
