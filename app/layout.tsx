import type { Metadata, Viewport } from 'next'
import { Syne, Outfit } from 'next/font/google'
import { Analytics } from '@vercel/analytics/next'
import './globals.css'

const syne = Syne({
  subsets: ['latin'],
  weight: ['700', '800'],
  variable: '--font-syne',
  display: 'swap',
})

const outfit = Outfit({
  subsets: ['latin'],
  weight: ['300', '400', '600', '700'],
  variable: '--font-outfit',
  display: 'swap',
})

const SITE_URL = 'https://vilketpartitillhorjag.com'
const TITLE = 'Vilket parti tillhör jag?'
const DESCRIPTION =
  'Ta reda på vilket riksdagsparti du egentligen håller med om — baserat på hur partierna faktiskt röstade i riksdagen de senaste fem åren. Gör testet gratis, inga tolkningar, bara fakta.'

export const metadata: Metadata = {
  metadataBase: new URL(SITE_URL),
  title: {
    default: TITLE,
    template: `%s | ${TITLE}`,
  },
  description: DESCRIPTION,
  keywords: [
    'vilket parti tillhör jag',
    'partitest',
    'politiskt quiz',
    'riksdagen',
    'riksdagsval',
    'partikompass',
    'politisk kompass',
    'val test',
    'vilket parti ska jag rösta på',
    'partiröstning',
    'riksdagsomröstning',
    'svenska partier',
  ],
  authors: [{ name: 'mrconter1', url: 'https://github.com/mrconter1' }],
  creator: 'mrconter1',
  publisher: 'mrconter1',
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      'max-image-preview': 'large',
      'max-snippet': -1,
    },
  },
  alternates: {
    canonical: SITE_URL,
  },
  openGraph: {
    type: 'website',
    locale: 'sv_SE',
    url: SITE_URL,
    siteName: TITLE,
    title: TITLE,
    description: DESCRIPTION,
    images: [
      {
        url: '/og.png',
        width: 1200,
        height: 630,
        alt: 'Vilket parti tillhör jag? – Riksdagsquiz baserat på verkliga voteringar',
      },
    ],
  },
  twitter: {
    card: 'summary_large_image',
    title: TITLE,
    description: DESCRIPTION,
    images: ['/og.png'],
  },
  icons: {
    icon: '/favicon.svg',
  },
}

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  themeColor: '#F7F3EC',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="sv" className={`${syne.variable} ${outfit.variable}`}>
      <body>{children}</body>
      <Analytics />
    </html>
  )
}
