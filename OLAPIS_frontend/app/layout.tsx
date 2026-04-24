import type { Metadata, Viewport } from "next"
import { Geist, Geist_Mono } from "next/font/google"
import { Analytics } from "@vercel/analytics/next"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/sonner"
import "./globals.css"

const geistSans = Geist({
  subsets: ["latin"],
  variable: "--font-geist-sans",
})

const geistMono = Geist_Mono({
  subsets: ["latin"],
  variable: "--font-geist-mono",
})

export const metadata: Metadata = {
  title: {
    default: "OLAPIS - Reddit for Research",
    template: "%s | OLAPIS",
  },
  description:
    "A platform for research enthusiasts to stay current with the latest findings and discuss them with curious minds.",
  keywords: [
    "research",
    "academic papers",
    "arXiv",
    "science",
    "discussion",
    "AI summaries",
  ],
  authors: [{ name: "OLAPIS" }],
  creator: "OLAPIS",
  openGraph: {
    type: "website",
    locale: "en_US",
    siteName: "OLAPIS",
    title: "OLAPIS - Reddit for Research",
    description:
      "A platform for research enthusiasts to stay current with the latest findings and discuss them with curious minds.",
  },
  twitter: {
    card: "summary_large_image",
    title: "OLAPIS - Reddit for Research",
    description:
      "A platform for research enthusiasts to stay current with the latest findings and discuss them with curious minds.",
  },
  icons: {
    icon: [
      {
        url: "/icon-light-32x32.png",
        media: "(prefers-color-scheme: light)",
      },
      {
        url: "/icon-dark-32x32.png",
        media: "(prefers-color-scheme: dark)",
      },
      {
        url: "/icon.svg",
        type: "image/svg+xml",
      },
    ],
    apple: "/apple-icon.png",
  },
}

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#0d9488" },
    { media: "(prefers-color-scheme: dark)", color: "#14b8a6" },
  ],
  width: "device-width",
  initialScale: 1,
}

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="bg-background">
      <body
        className={`${geistSans.variable} ${geistMono.variable} font-sans antialiased`}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="system"
          enableSystem
          disableTransitionOnChange
        >
          {children}
          <Toaster />
        </ThemeProvider>
        {process.env.NODE_ENV === "production" && <Analytics />}
      </body>
    </html>
  )
}
