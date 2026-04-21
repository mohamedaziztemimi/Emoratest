import type { Metadata, Viewport } from "next";
import Script from "next/script";
import { AuthProvider } from "@/lib/auth";
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
    default: "EmoraTest",
    template: "%s | EmoraTest",

  },

  description: "See why users quit with emotion-powered heatmaps and AI insights. Real-time emotion ML, auto-variant generation, and statistically sound A/B testing.",
  keywords: [
    "emotion detection",
    "A/B testing",
    "conversion optimization",
    "user behavior analytics",
    "emotion heatmap",
    "session replay",
    "bandit testing",
    "emotion ML",
    "UX research",
  ],
  authors: [{ name: "EmoraTest" }],
  creator: "EmoraTest",
  publisher: "EmoraTest",
  metadataBase: new URL(BASE_URL),
  alternates: {
    canonical: "/",
  },
  openGraph: {
    title: "EmoraTest — Emotion ML A/B Testing",
    description: "See why users quit with emotion-powered heatmaps and AI insights.",
    type: "website",
    url: BASE_URL,
    siteName: "EmoraTest",
    images: [
      {
        url: `${BASE_URL}/og-image.png`,
        width: 1200,
        height: 630,
        alt: "EmoraTest - Unlock Emotions, Win Tests",
      },
    ],
    locale: "en_US",
  },
  twitter: {
    card: "summary_large_image",
    title: "EmoraTest — Emotion ML A/B Testing",
    description: "See why users quit with emotion-powered heatmaps and AI insights.",
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
    icon: "/logo2.png",
    shortcut: "/logo2.png",
    apple: "/logo2.png",
  },
  // JSON-LD structured data
  other: {
    "application/ld+json": JSON.stringify({
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
      description: "Emotion ML + A/B Testing Platform. See why users quit with emotion-powered heatmaps and AI insights.",
      url: BASE_URL,
      author: {
        "@type": "Organization",
        name: "EmoraTest",
        url: BASE_URL,
      },
      aggregateRating: {
        "@type": "AggregateRating",
        ratingValue: "4.8",
        ratingCount: "2400",
        bestRating: "5",
        worstRating: "1",
      },
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
    <html lang="en" className="dark-mode" suppressHydrationWarning>
      <head>
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
      </head>
      <body className={`${inter.variable} ${figtree.variable} font-sans antialiased`}>
        <AuthProvider>{children}</AuthProvider>

        {/* EmoraTest SDK - loads on all pages, client-side only */}
        {EMORATEST_SDK_KEY && (
          <>
            <Script
              src="https://emoratest.com/static/sdk/emoratest.umd.js"
              strategy="afterInteractive"
              onLoad={() => {
                // SDK loaded, safe to initialize
                if (typeof window !== "undefined" && (window as any).EmoraTest) {
                  (window as any).EmoraTest.init({
                    sdkKey: EMORATEST_SDK_KEY,
                    apiUrl: "https://emoratest.com",
                  });
                }
              }}
            />
          </>
        )}
      </body>
    </html>
  );
}
