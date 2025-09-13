// app/layout.tsx
import './globals.css'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Goal-based Investment Planner',
  description: 'Plan your investments to reach your goals with smart portfolio recommendations.',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className="font-sans bg-gray-50">{children}</body>
    </html>
  )
}
