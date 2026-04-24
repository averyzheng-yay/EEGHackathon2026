import { Header } from "@/components/header"
import { AuthProvider } from "@/components/auth-provider"

export default function MainLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <AuthProvider>
      <div className="min-h-screen flex flex-col">
        <Header />
        <main className="flex-1 container mx-auto px-4 py-6">{children}</main>
      </div>
    </AuthProvider>
  )
}
