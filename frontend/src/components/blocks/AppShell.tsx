import { NavLink, Outlet } from "react-router-dom"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { useAuth } from "@/auth/AuthContext"
import { BRAND_NAME, BRAND_TAGLINE } from "@/lib/brand"
import { Logo } from "@/components/blocks/Logo"

const navClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    "rounded-md px-3 py-1.5 text-xs font-semibold transition-all duration-200",
    isActive
      ? "bg-primary text-white shadow-lg shadow-primary/40"
      : "text-muted-foreground hover:bg-primary/15 hover:text-primary",
  )

export function AppShell() {
  const { me, logout } = useAuth()
  const addProductTo = me ? "/request" : "/login?next=%2Frequest"

  return (
    <div className="flex min-h-svh flex-col bg-background">
      <header className="sticky top-0 z-40 border-b border-border bg-white dark:bg-slate-900 shadow-sm">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center justify-between gap-3 px-4 py-3 sm:px-6">
          <div className="flex min-w-0 items-center gap-3">
            <NavLink to="/" className="group flex items-center gap-2.5 rounded-lg outline-none focus-visible:ring-2 focus-visible:ring-ring hover:opacity-80 transition-opacity">
              <Logo className="size-9 shrink-0" />
              <span className="flex min-w-0 flex-col leading-tight">
                <span className="font-heading text-sm font-semibold tracking-tight text-foreground">{BRAND_NAME}</span>
                <span className="hidden max-w-[220px] truncate text-[0.65rem] text-muted-foreground sm:block">
                  {BRAND_TAGLINE}
                </span>
              </span>
            </NavLink>
            <Separator orientation="vertical" className="hidden h-8 sm:block" />
            <nav className="hidden items-center gap-1 sm:flex" aria-label="Main">
              <NavLink to="/" className={navClass} end>
                Tracker
              </NavLink>
              {me ? (
                <>
                  <NavLink to="/account" className={navClass}>
                    Account
                  </NavLink>
                  {me.role === "admin" ? (
                    <NavLink to="/admin" className={navClass}>
                      Admin
                    </NavLink>
                  ) : null}
                </>
              ) : null}
            </nav>
          </div>
          <div className="flex items-center gap-2">
            <Button type="button" size="sm" asChild>
              <NavLink to={addProductTo}>+ Add product</NavLink>
            </Button>
            {me ? (
              <>
                <span className="hidden max-w-[200px] truncate text-[0.7rem] text-muted-foreground md:inline">
                  {me.email}
                  {me.role === "admin" ? " · admin" : ""}
                </span>
                <Button type="button" variant="outline" size="sm" onClick={() => logout()}>
                  Log out
                </Button>
              </>
            ) : (
              <Button type="button" size="sm" variant="outline" asChild>
                <NavLink to="/login">Log in</NavLink>
              </Button>
            )}
          </div>
        </div>
        <nav className="flex flex-wrap gap-1 border-t border-border/50 px-4 py-2 sm:hidden" aria-label="Main mobile">
          <NavLink to="/" className={navClass} end>
            Tracker
          </NavLink>
          {me ? (
            <>
              <NavLink to="/account" className={navClass}>
                Account
              </NavLink>
              {me.role === "admin" ? (
                <NavLink to="/admin" className={navClass}>
                  Admin
                </NavLink>
              ) : null}
            </>
          ) : null}
        </nav>
      </header>

      <main id="main-content" className="flex-1">
        <Outlet />
      </main>

      <footer className="border-t border-border bg-muted py-8 text-center text-[0.7rem] text-muted-foreground">
        <p className="font-medium text-foreground/80">{BRAND_NAME}</p>
        <p className="mx-auto mt-1 max-w-md leading-relaxed">
          Monitors public product pages only. Not affiliated with Amazon, Flipkart, or other retailers.
        </p>
      </footer>
    </div>
  )
}
