import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import { Providers } from './providers'
import { Toaster } from 'react-hot-toast'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Jaseci Learning Companion',
  description: 'Enterprise-grade multi-agent learning platform for Jaseci programming language',
  authors: [
    {
      name: 'Cavin Otieno',
      url: 'https://www.linkedin.com/in/cavin-otieno-9a841260/'
    }
  ],
  keywords: [
    'Jaseci',
    'Programming',
    'Learning',
    'AI',
    'Multi-Agent System',
    'Code Analysis',
    'Educational Platform'
  ],
  openGraph: {
    title: 'Jaseci Learning Companion',
    description: 'Learn Jaseci programming language with AI-powered agents',
    type: 'website',
    url: 'https://github.com/OumaCavin/jaseci-learning-companion',
    siteName: 'Jaseci Learning Companion'
  },
  twitter: {
    card: 'summary_large_image',
    title: 'Jaseci Learning Companion',
    description: 'Learn Jaseci programming language with AI-powered agents',
  },
  robots: {
    index: true,
    follow: true,
  },
  viewport: {
    width: 'device-width',
    initialScale: 1,
    maximumScale: 1,
  },
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#ffffff' },
    { media: '(prefers-color-scheme: dark)', color: '#1a1a1a' }
  ]
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <head>
        <link rel="icon" href="/favicon.ico" />
        <link rel="apple-touch-icon" href="/apple-touch-icon.png" />
        <meta name="theme-color" content="#000000" />
      </head>
      <body className={inter.className}>
        <Providers>
          {children}
          <Toaster
            position="top-right"
            toastOptions={{
              duration: 4000,
              style: {
                background: '#363636',
                color: '#fff',
              },
              success: {
                duration: 3000,
                iconTheme: {
                  primary: '#4ade80',
                  secondary: '#fff',
                },
              },
              error: {
                duration: 5000,
                iconTheme: {
                  primary: '#ef4444',
                  secondary: '#fff',
                },
              },
            }}
          />
        </Providers>
      </body>
    </html>
  )
}