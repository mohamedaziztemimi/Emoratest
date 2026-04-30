/* ────────────────────────────────────────────────
   Footer - Clean, organized footer
   ──────────────────────────────────────────────── */

"use client";

const FOOTER_LINKS = {
  product: [
    { label: "Features", href: "/#features" },
    { label: "Pricing", href: "/#pricing" },
    { label: "Integrations", href: "/#integrations" },
  ],
  resources: [
    { label: "Documentation", href: "/docs" },
  ],
  legal: [
    { label: "Privacy Policy", href: "/privacy" },
    { label: "Terms of Service", href: "/terms" },
    { label: "Impressum", href: "/impressum" },
  ],
};

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="bg-white border-t border-gray-200">
      {/* Main footer content */}
      <div className="max-w-[1200px] mx-auto px-6" style={{ paddingTop: "60px", paddingBottom: "40px" }}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-8">
          {/* Brand column */}
          <div className="col-span-2 md:col-span-1">
            {/* Logo */}
            <a href="/" className="flex items-center gap-2.5 mb-4">
              <img src="/logo2.png" alt="EmoraTest" className="h-10 w-auto" />
            </a>

            {/* Tagline */}
            <p className="text-sm text-[#6B7280] mb-6 max-w-xs">
              EmoraTest. Emotion tracking for websites.
            </p>
          </div>

          {/* Product links */}
          <div>
            <h4 className="text-sm font-semibold text-[#111318] mb-4">Product</h4>
            <ul className="space-y-3">
              {FOOTER_LINKS.product.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="text-sm text-[#6B7280] hover:text-[#007BFF] transition-colors">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Resources links */}
          <div>
            <h4 className="text-sm font-semibold text-[#111318] mb-4">Resources</h4>
            <ul className="space-y-3">
              {FOOTER_LINKS.resources.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="text-sm text-[#6B7280] hover:text-[#007BFF] transition-colors">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          {/* Legal links */}
          <div>
            <h4 className="text-sm font-semibold text-[#111318] mb-4">Legal</h4>
            <ul className="space-y-3">
              {FOOTER_LINKS.legal.map((link) => (
                <li key={link.label}>
                  <a href={link.href} className="text-sm text-[#6B7280] hover:text-[#007BFF] transition-colors">
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom bar */}
        <div className="pt-8 border-t border-gray-200 flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="text-xs text-[#9CA3AF]">
            © {currentYear} EmoraTest. All rights reserved.
          </p>

          <p className="text-xs text-[#9CA3AF]">
            Made with care in Germany
          </p>
        </div>
      </div>
    </footer>
  );
}
