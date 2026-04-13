/* ────────────────────────────────────────────────────────
   Sitemap - XML sitemap for EmoraTest
   ──────────────────────────────────────────────────────── */

import type { MetadataRoute } from "next";

const BASE_URL = process.env.NEXT_PUBLIC_BASE_URL || "https://emoratest.com";

export default function sitemap(): MetadataRoute.Sitemap {
  const routes = [
    "",
    "/pricing",
    "/features",
    "/blog",
    "/docs",
    "/demo",
  ];

  const lastModified = new Date();

  return routes.map((route) => ({
    url: `${BASE_URL}${route}`,
    lastModified,
    changeFrequency: route === "" ? "daily" : "weekly",
    priority: route === "" ? 1 : 0.7,
  }));
}
