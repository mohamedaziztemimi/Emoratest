/* ────────────────────────────────────────────────
   Footer - Clean, organized footer
   ──────────────────────────────────────────────── */

"use client";

import { useState } from "react";

const FOOTER_LINKS = {
  product: [
    { label: "Features", href: "/#features" },
    { label: "Pricing", href: "/#pricing" },
    { label: "Integrations", href: "/#integrations" },
  ],
  resources: [
    { label: "Documentation", href: "/docs" },
    { label: "Blog", href: "/blog" },
    { label: "Help Center", href: "/help" },
  ],
  company: [
    { label: "About", href: "/about" },
    { label: "Careers", href: "/careers" },
    { label: "Contact", href: "/contact" },
  ],
  legal: [
    { label: "Privacy Policy", href: "/privacy" },
    { label: "Terms of Service", href: "/terms" },
    { label: "Security", href: "/security" },
  ],
};

const SOCIAL = [
  { name: "Twitter", icon: "𝕏", url: "https://twitter.com/emoratest" },
  { name: "LinkedIn", icon: "in", url: "https://linkedin.com/company/emoratest" },
  { name: "GitHub", icon: "🐙", url: "https://github.com/emoratest" },
];

export function Footer() {
  const [email, setEmail] = useState("");
  const [subscribed, setSubscribed] = useState(false);

  const handleSubscribe = (e: React.FormEvent) => {
    e.preventDefault();
    if (email.trim()) {
      setSubscribed(true);
    }
  };

  return (
    <footer className="bg-white border-t border-gray-200">
      {/* Email Capture Section */}
      <div className="border-b border-gray-100" style={{ paddingTop: "80px", paddingBottom: "80px", borderTop: "1px solid #E5E7EB" }}>
        <div className="max-w-[1200px] mx-auto px-6 text-center">
          <h3 className="text-xl font-bold text-[#111318] mb-2">
            Get Weekly Emotion Insights
          </h3>
          <p className="text-sm text-[#6B7280] mb-6">
            Conversion tips, emotion ML research, and product updates. No spam. Unsubscribe anytime.
          </p>

          {!subscribed ? (
            <form onSubmit={handleSubscribe} className="flex flex-wrap items-center justify-center gap-3 mb-3">
              <input
                type="email"
                placeholder="your@company.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                style={{
                  border: "1px solid #E5E7EB",
                  borderRadius: "9999px",
                  padding: "12px 20px",
                  width: "280px",
                  fontSize: "14px",
                }}
              />
              <button
                type="submit"
                style={{
                  background: "linear-gradient(135deg, #007BFF, #7C3AED)",
                  color: "white",
                  borderRadius: "9999px",
                  padding: "12px 24px",
                  fontSize: "14px",
                  fontWeight: 600,
                  border: "none",
                  cursor: "pointer",
                }}
              >
                Subscribe →
              </button>
            </form>
          ) : (
            <p className="text-[#10B981] font-semibold mb-3">
              Thanks! Check your inbox.
            </p>
          )}

          <p className="text-xs text-[#9CA3AF]">
            Join 2,400+ growth teams. No spam ever.
          </p>
        </div>
      </div>

      {/* Main footer content */}
      <div className="max-w-[1200px] mx-auto px-6" style={{ paddingTop: "60px" }}>
        <div className="grid grid-cols-2 md:grid-cols-5 gap-8 mb-12">
          {/* Brand column - spans 2 on mobile, 1 on desktop */}
          <div className="col-span-2 md:col-span-1">
            {/* Logo */}
            <a href="/" className="flex items-center gap-2.5 mb-4">
              <img src="/logo2.png" alt="EmoraTest" className="h-10 w-auto" />
            </a>

            {/* Tagline */}
            <p className="text-sm text-[#6B7280] mb-6 max-w-xs">
              Unlock Emotions, Win Tests. See what your users actually feel.
            </p>

            {/* Social icons */}
            <div className="flex gap-2">
              {SOCIAL.map((social) => (
                <a
                  key={social.name}
                  href={social.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="w-9 h-9 rounded-lg bg-gray-100 flex items-center justify-center hover:bg-[#007BFF]/10 hover:border-[#007BFF]/30 border border-transparent transition-all text-sm"
                  title={social.name}
                >
                  {social.icon}
                </a>
              ))}
            </div>
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

          {/* Company links */}
          <div>
            <h4 className="text-sm font-semibold text-[#111318] mb-4">Company</h4>
            <ul className="space-y-3">
              {FOOTER_LINKS.company.map((link) => (
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
            © {new Date().getFullYear()} EmoraTest. All rights reserved.
          </p>

          <div className="flex items-center gap-6 text-xs text-[#9CA3AF]">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-[#10B981]"></span>
              All systems operational
            </span>
            <span>•</span>
            <span>🔒 GDPR Compliant</span>
            <span>•</span>
            <span>🇺🇸/🇪🇺 SOC 2 Ready</span>
          </div>
        </div>
      </div>
    </footer>
  );
}
