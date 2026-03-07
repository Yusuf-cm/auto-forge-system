// app/layout.tsx
// Root layout — metadata, font loading, global styles.
// Keep this file minimal. No UI logic here.

import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Volt Coffee | Fuel the Grind',
  description: 'Premium single-origin specialty coffee. Roasted to order, shipped in 48 hours.',
  keywords: ['specialty coffee', 'single origin', 'artisan roaster'],
  openGraph: {
    title: 'Volt Coffee | Fuel the Grind',
    description: 'Premium single-origin specialty coffee roasted to order.',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
