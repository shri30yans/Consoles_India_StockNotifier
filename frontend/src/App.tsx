import { HashRouter, Navigate, Route, Routes } from "react-router-dom"
import { AuthProvider } from "@/auth/AuthContext"
import { AppShell } from "@/components/blocks/AppShell"
import { CatalogPage } from "@/pages/CatalogPage"
import { ProductPage } from "@/pages/ProductPage"
import { LoginPage } from "@/pages/LoginPage"
import { RegisterPage } from "@/pages/RegisterPage"
import { AccountPage } from "@/pages/AccountPage"
import { RequestPage } from "@/pages/RequestPage"
import { AdminPage } from "@/pages/AdminPage"

export default function App() {
  return (
    <AuthProvider>
      <HashRouter>
        <Routes>
          <Route element={<AppShell />}>
            <Route index element={<CatalogPage />} />
            <Route path="product/:id" element={<ProductPage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="account" element={<AccountPage />} />
            <Route path="request" element={<RequestPage />} />
            <Route path="admin" element={<AdminPage />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </HashRouter>
    </AuthProvider>
  )
}
