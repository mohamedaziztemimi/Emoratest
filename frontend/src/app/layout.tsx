import type { Metadata, Viewport } from "next";
import { AuthProvider } from "@/lib/auth";
import EmoraTestScript from "@/components/EmoraTestScript";
import { CookieConsent } from "@/components/CookieConsent";
import { Inter, Figtree } from "next/font/google";
import "./globals.css";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
  display: "swap",
});

const figtree = Figtree({
  subsets: ["latin"],
  variable: "--font-figtree",
  display: "swap",
});

// Get base URL from env or fallback
const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "https://emoratest.com";
const EMORATEST_SDK_KEY = process.env.NEXT_PUBLIC_EMORATEST_KEY || "";

export const metadata: Metadata = {

  title: {
    default: "EmoraTest — Detect User Emotions from Mouse Behavior | Emotion Analytics for Websites",
    template: "%s | EmoraTest",

  },

  description: "EmoraTest uses ML to detect 8 emotions including frustration, confusion, and delight from mouse behavior. Find conversion killers with emotion-based A/B testing. Free plan available.",
  keywords: [
    "emotion analytics",
    "user emotion detection",
    "mouse behavior analysis",
    "A/B testing",
    "conversion optimization",
    "UX analytics",
    "frustration detection",
    "rage click detection",
    "user experience testing",
    "website emotion tracking",
    "behavioral analytics",
    "CRO tool",
  ],
  authors: [{ name: "EmoraTest" }],
  creator: "EmoraTest",
  publisher: "EmoraTest",
  metadataBase: new URL(BASE_URL),
  alternates: {
    canonical: BASE_URL,
  },
  openGraph: {
    title: "EmoraTest — Detect User Emotions from Mouse Behavior",
    description: "EmoraTest uses ML to detect 8 emotions including frustration, confusion, and delight from mouse behavior. Find conversion killers with emotion-based A/B testing. Free plan available.",
    type: "website",
    url: BASE_URL,
    siteName: "EmoraTest",
    images: [
      {
        url: `${BASE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: "EmoraTest - Detect User Emotions from Mouse Behavior",
      },
    ],
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "EmoraTest — Detect User Emotions from Mouse Behavior",
    description: "EmoraTest uses ML to detect 8 emotions including frustration, confusion, and delight from mouse behavior. Find conversion killers with emotion-based A/B testing.",
    images: [`${BASE_URL}/og-image.png`],
    creator: "@emoratest",
  },
  robots: {
    index: true,
    follow: true,
    googleBot: {
      index: true,
      follow: true,
      "max-video-preview": -1,
      "max-image-preview": "large",
      "max-snippet": -1,
    },
  },
  manifest: "/manifest.json",
  icons: {
    icon: [
      { url: "/favicon.png", sizes: "32x32", type: "image/png" },
      { url: "/favicon.png", sizes: "64x64", type: "image/png" },
      { url: "/favicon.png", sizes: "128x128", type: "image/png" },
      { url: "/favicon.png", sizes: "256x256", type: "image/png" },
      { url: "/favicon.png", sizes: "512x512", type: "image/png" },
    ],
    shortcut: "/favicon.png",
    apple: "/apple-icon.png",
  },
  // JSON-LD structured data - Organization schema
  other: {
    "application/ld+json": JSON.stringify({
      "@context": "https://schema.org",
      "@type": "Organization",
      name: "EmoraTest",
      url: BASE_URL,
      logo: `${BASE_URL}/logo2.png`,
      description: "Emotion analytics platform that detects user emotions from mouse behavior",
      foundingDate: "2025",
      address: {
        "@type": "PostalAddress",
        addressCountry: "DE",
      },
      sameAs: [],
    }),
  },
};

export const viewport: Viewport = {
  themeColor: "#007BFF",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{
            __html: JSON.stringify({
              "@context": "https://schema.org",
              "@type": "SoftwareApplication",
              name: "EmoraTest",
              applicationCategory: "BusinessApplication",
              operatingSystem: "Web",
              offers: {
                "@type": "Offer",
                price: "0",
                priceCurrency: "USD",
              },
              description: "Detect 8 emotions from mouse behavior on your website using ML",
              url: BASE_URL,
            }),
          }}
        />
      </head>
      <body className={`${inter.variable} ${figtree.variable} font-sans antialiased`}>
        <AuthProvider>{children}</AuthProvider>

        {/* EmoraTest SDK - loads on all pages, client-side only */}
        <EmoraTestScript sdkKey={EMORATEST_SDK_KEY} />

        {/* Cookie Consent Banner - GDPR required */}
        <CookieConsent />
      </body>
    </html>
  );
}
