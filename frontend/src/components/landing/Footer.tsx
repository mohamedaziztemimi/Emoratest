/* ────────────────────────────────────────────────
   Footer - Professional footer with navigation
   ──────────────────────────────────────────────── */

"use client";

const NAVIGATION = [
  { label: "Product", links: [{ label: "Features", href: "/#features" }, { label: "Pricing", href: "/#pricing" }] },
  { label: "Resources", links: [{ label: "Documentation", href: "/docs" }, { label: "Blog", href: "/blog" }, { label: "Help Center", href: "/help" }] },
  { label: "Company", links: [{ label: "About", href: "/about" }, { label: "Careers", href: "/careers" }] },
];

const SOCIAL = [
  { name: "Twitter", icon: "𝕏", url: "https://twitter.com/emoratest" },
  { name: "LinkedIn", icon: "in", url: "https://linkedin.com/company/emoratest" },
  { name: "GitHub", icon: "🐙", url: "https://github.com/emoratest" },
  { name: "Product Hunt", icon: "🎯", url: "https://producthunt.com/posts/emoratest" },
];

export function Footer() {
  return (
    <footer className="bg-white border-t border-gray-200 py-12">
      <div className="max-w-[1200px] mx-auto px-6">
        <div className="grid md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="md:col-span-1">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#007BFF] to-[#7C3AED] flex items-center justify-center text-white font-bold text-xl">
                E
              </div>
              <div>
                <h3 className="text-xl font-bold text-[#111318]">EmoraTest</h3>
                <p className="text-xs text-[#6B7280]">
                  Unlock Emotions, Win Tests
                </p>
              </div>
            </div>

            {/* Newsletter */}
            <div className="flex gap-2">
              <input
                type="email"
                placeholder="Enter your email"
                className="flex-1 px-4 py-2.5 rounded-lg border border-gray-300 bg-white text-[#111318] text-sm focus:outline-none focus:border-[#007BFF]/50 transition-colors"
              />
              <button className="px-6 py-2.5 rounded-lg bg-gradient-to-r from-[#007BFF] to-[#7C3AED] text-white font-semibold text-sm hover:opacity-90 transition-opacity">
                Subscribe
              </button>
            </div>
          </div>

          {/* Navigation Columns */}
          <div className="md:col-span-3 grid grid-cols-3 gap-8">
            {NAVIGATION.map((nav) => (
              <div key={nav.label}>
                <h4 className="font-semibold text-[#111318] mb-4 text-xs uppercase tracking-wider">
                  {nav.label}
                </h4>
                <ul className="space-y-2">
                  {nav.links.map((link) => (
                    <li key={link.label}>
                      <a
                        href={link.href}
                        className="text-sm text-[#4B5563] hover:text-[#007BFF] transition-colors"
                      >
                        {link.label}
                      </a>
                    </li>
                  ))}
                </ul>
              </div>
            ))}

            {/* Legal */}
            <div>
              <h4 className="font-semibold text-[#111318] mb-4 text-xs uppercase tracking-wider">
                Legal
              </h4>
              <ul className="space-y-2">
                <li>
                  <a href="/privacy" className="text-sm text-[#4B5563] hover:text-[#007BFF] transition-colors">
                    Privacy Policy
                  </a>
                </li>
                <li>
                  <a href="/terms" className="text-sm text-[#4B5563] hover:text-[#007BFF] transition-colors">
                    Terms of Service
                  </a>
                </li>
                <li>
                  <a href="/security" className="text-sm text-[#4B5563] hover:text-[#007BFF] transition-colors">
                    Security
                  </a>
                </li>
              </ul>
            </div>
          </div>
        </div>

        {/* Bottom Bar */}
        <div className="mt-8 pt-8 border-t border-gray-200">
          <div className="flex flex-col md:flex-row items-center justify-between gap-4">
            {/* Copyright */}
            <div className="text-xs text-[#6B7280]">
              © {new Date().getFullYear()} EmoraTest. All rights reserved.
            </div>

            {/* Social Icons */}
            <div className="flex gap-4">
              {SOCIAL.map((social) => (
                <a
                  key={social.name}
                  href={social.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center border border-gray-200 hover:bg-gray-200 hover:border-[#007BFF]/50 transition-all text-sm"
                  title={social.name}
                >
                  {social.icon}
                </a>
              ))}
            </div>
          </div>
        </div>
      </div>
    </footer>
  );
}
