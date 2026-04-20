/* ────────────────────────────────────────────────
   Navbar - Smooth scroll to sections + progress indicator
   ──────────────────────────────────────────────── */

"use client";

import { useState, useEffect, useCallback } from "react";
import { GradientButton } from "../ui";

interface NavLink {
  label: string;
  targetId: string;
}

const NAV_LINKS: NavLink[] = [
  { label: "Features", targetId: "#features" },
  { label: "How It Works", targetId: "#how-it-works" },
  { label: "Integrations", targetId: "#integrations" },
  { label: "Pricing", targetId: "#pricing" },
  { label: "FAQ", targetId: "#faq" },
];

export function Navbar() {
  const [isScrolled, setIsScrolled] = useState(false);
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [activeSection, setActiveSection] = useState<string>("hero");
  const [scrollProgress, setScrollProgress] = useState(0);
  const [authState, setAuthState] = useState<"loading" | "logged-in" | "logged-out">("loading");

  // Check auth status on mount
  useEffect(() => {
    const checkAuth = async () => {
      try {
        const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/v1/auth/me`, {
          credentials: "include",
        });
        setAuthState(res.ok ? "logged-in" : "logged-out");
      } catch {
        setAuthState("logged-out");
      }
    };
    checkAuth();
  }, []);

  // Handle scroll state and active section
  useEffect(() => {
    const handleScroll = () => {
      const scrollY = window.scrollY;
      setIsScrolled(scrollY > 50);

      // Calculate scroll progress (0 to 100)
      const docHeight = document.documentElement.scrollHeight - window.innerHeight;
      const progress = Math.min((scrollY / docHeight) * 100, 100);
      setScrollProgress(progress);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    return () => window.removeEventListener("scroll", handleScroll);
  }, []);

  // IntersectionObserver to detect active section
  useEffect(() => {
    const sections = NAV_LINKS.map((link) => ({
      id: link.targetId.slice(1),
      element: document.getElementById(link.targetId.slice(1)),
    }));

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            setActiveSection(entry.target.id);
          }
        });
      },
      { threshold: 0.5, rootMargin: "-20% 0px -60% 0px" }
    );

    sections.forEach((section) => {
      if (section.element) observer.observe(section.element);
    });

    return () => observer.disconnect();
  }, []);

  // Smooth scroll to section
  const handleNavClick = (e: React.MouseEvent, targetId: string) => {
    e.preventDefault();
    const target = document.getElementById(targetId.slice(1));
    if (target) {
      target.scrollIntoView({ behavior: "smooth", block: "start" });
      setIsMobileMenuOpen(false);
    }
  };

  return (
    <>
      {/* Fixed navbar */}
      <nav
        className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
          isScrolled ? "bg-white/95 backdrop-blur-md shadow-sm" : "bg-transparent"
        }`}
      >
        <div className="max-w-7xl mx-auto px-6">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <a
              href="/"
              className="flex items-center gap-2"
              onClick={(e) => {
                e.preventDefault();
                window.scrollTo({ top: 0, behavior: "smooth" });
              }}
            >
              <img
                src="/logo2.png"
                alt="EmoraTest"
                className="h-11 w-auto"
                width="44"
                height="44"
              />
              <span className="text-xl font-bold text-gray-900">EmoraTest</span>
            </a>

            {/* Desktop nav links */}
            <div className="hidden md:flex items-center gap-8">
              {NAV_LINKS.map((link) => (
                <a
                  key={link.label}
                  href={link.targetId}
                  onClick={(e) => handleNavClick(e, link.targetId)}
                  className={`relative px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeSection === link.targetId.slice(1)
                      ? "text-blue-600 bg-blue-50"
                      : "text-gray-600 hover:text-gray-900 hover:bg-gray-50"
                  }`}
                >
                  {link.label}
                  {activeSection === link.targetId.slice(1) && (
                    <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-0.5 rounded-full bg-blue-600" />
                  )}
                </a>
              ))}
              <a
                href="/docs"
                className="px-3 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-all duration-200"
              >
                Docs
              </a>
            </div>

            {/* Right side CTAs */}
            <div className="hidden md:flex items-center gap-3">
              {authState === "loading" ? (
                <div style={{ width: "140px" }}></div>
              ) : authState === "logged-in" ? (
                <a
                  href="/dashboard"
                  className="px-4 py-2 rounded-lg text-sm font-medium text-white bg-gradient-to-r from-[#007BFF] to-[#7C3AED] hover:opacity-90 transition-all duration-200"
                >
                  Dashboard →
                </a>
              ) : (
                <>
                  <a
                    href="/login"
                    className="px-4 py-2 rounded-lg text-sm font-medium text-gray-600 hover:text-gray-900 hover:bg-gray-50 transition-all duration-200"
                  >
                    Sign In
                  </a>
                  <GradientButton variant="primary" size="sm" href="/signup" glow>
                    Start Free
                  </GradientButton>
                </>
              )}
            </div>

            {/* Mobile hamburger */}
            <button
              onClick={() => setIsMobileMenuOpen(true)}
              className="md:hidden w-10 h-10 rounded-lg flex items-center justify-center text-gray-600 hover:bg-gray-100 transition-colors"
              aria-label="Open menu"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M4 6h16M4 12h16M4 18h16" />
              </svg>
            </button>
          </div>
        </div>

        {/* Scroll Progress Indicator - Blue line at bottom */}
        <div className="h-0.5 bg-gray-200">
          <div
            className="h-full bg-gradient-to-r from-[#007BFF] to-[#7C3AED] transition-all duration-150 ease-out"
            style={{ width: `${scrollProgress}%` }}
          />
        </div>
      </nav>

      {/* Mobile menu overlay */}
      <div
        className={`fixed inset-0 z-50 transition-all duration-300 md:hidden ${
          isMobileMenuOpen ? "opacity-100 visible" : "opacity-0 invisible pointer-events-none"
        }`}
      >
        {/* Backdrop */}
        <div
          className="absolute inset-0 bg-black/50 backdrop-blur-sm"
          onClick={() => setIsMobileMenuOpen(false)}
        />

        {/* Mobile menu panel */}
        <div
          className={`absolute right-0 top-0 bottom-0 w-80 bg-white shadow-2xl flex flex-col ${
            isMobileMenuOpen ? "translate-x-0" : "translate-x-full"
          } transition-transform duration-300`}
        >
          {/* Mobile menu header */}
          <div className="flex items-center gap-2 p-4 border-b">
            <img
              src="/logo2.png"
              alt="EmoraTest"
              className="h-9 w-auto"
              width="36"
              height="36"
            />
            <span className="text-lg font-bold text-gray-900">EmoraTest</span>
            <button
              onClick={() => setIsMobileMenuOpen(false)}
              className="w-10 h-10 rounded-lg flex items-center justify-center text-gray-600 hover:bg-gray-100"
              aria-label="Close menu"
            >
              <svg className="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>

          {/* Mobile menu links */}
          <div className="flex-1 overflow-y-auto p-4 space-y-2">
            {NAV_LINKS.map((link) => (
              <a
                key={link.label}
                href={link.targetId}
                onClick={(e) => handleNavClick(e, link.targetId)}
                className="block px-4 py-3 rounded-lg text-base font-medium text-gray-900 hover:bg-gray-50 transition-colors"
              >
                {link.label}
              </a>
            ))}
            <a
              href="/docs"
              className="block px-4 py-3 rounded-lg text-base font-medium text-gray-900 hover:bg-gray-50 transition-colors"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Docs
            </a>
          </div>

          {/* Mobile menu footer */}
          <div className="p-4 border-t space-y-3">
            {authState === "loading" ? (
              <div style={{ height: "48px" }}></div>
            ) : authState === "logged-in" ? (
              <a
                href="/dashboard"
                className="block w-full px-4 py-3 rounded-lg text-center font-medium text-white bg-gradient-to-r from-[#007BFF] to-[#7C3AED]"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Dashboard →
              </a>
            ) : (
              <>
                <a
                  href="/login"
                  className="block w-full px-4 py-3 rounded-lg text-center font-medium text-gray-700 hover:bg-gray-50"
                  onClick={() => setIsMobileMenuOpen(false)}
                >
                  Sign In
                </a>
                <GradientButton variant="primary" size="md" glow href="/signup" className="w-full" onClick={() => setIsMobileMenuOpen(false)}>
                  Start Free
                </GradientButton>
              </>
            )}
          </div>
        </div>
      </div>
    </>
  );
}
