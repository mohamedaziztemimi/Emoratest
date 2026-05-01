/* ────────────────────────────────────────────────────────
   Robots.txt - Search engine crawling rules
   ──────────────────────────────────────────────────────── */

import type { MetadataRoute } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "https://emoratest.com";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: [
      {
        userAgent: "*",
        allow: ["/", "/static/sdk/"],
        disallow: ["/api/", "/dashboard/"],
      },
    ],
    sitemap: `${BASE_URL}/sitemap.xml`,
  };
}
