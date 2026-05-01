"use client";

import { useCallback, useEffect, useState } from "react";
import Sidebar from "./Sidebar";
import clsx from "clsx";
import Link from "next/link";
import { useRouter } from "next/navigation";

interface SearchResult {
  id: string;
  type: "session" | "page";
  title: string;
  url?: string;
  emotion?: string;
}

export default function DashboardShell({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [dark, setDark] = useState(false);
  const [searchQuery, setSearchQuery] = useState("");
  const [searchFocused, setSearchFocused] = useState(false);
  const [searchResults, setSearchResults] = useState<SearchResult[]>([]);
  const [searching, setSearching] = useState(false);

  useEffect(() => {
    const saved = localStorage.getItem("emoratest_theme");
    if (saved === "dark" || (!saved && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      setDark(true);
      document.documentElement.classList.add("dark");
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setDark((d) => {
      const next = !d;
      document.documentElement.classList.toggle("dark", next);
      localStorage.setItem("emoratest_theme", next ? "dark" : "light");
      return next;
    });
  }, []);

  // Search functionality
  useEffect(() => {
    const performSearch = async () => {
      if (searchQuery.trim().length < 2) {
        setSearchResults([]);
        return;
      }

      setSearching(true);
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

        // Search sessions by visitor ID or page URL
        const sessionsRes = await fetch(`${apiUrl}/api/v1/dashboard/sessions?search=${encodeURIComponent(searchQuery)}&page_size=5`, {
          credentials: "include",
        });

        if (sessionsRes.ok) {
          const data = await sessionsRes.json();
          const results: SearchResult[] = (data.sessions || []).map((s: any) => ({
            id: s.id,
            type: "session" as const,
            title: s.visitor_id || s.id.slice(0, 8),
            url: s.page_url,
            emotion: s.primary_emotion,
          }));
          setSearchResults(results);
        } else {
          setSearchResults([]);
        }
      } catch {
        setSearchResults([]);
      } finally {
        setSearching(false);
      }
    };

    const debounceTimer = setTimeout(performSearch, 300);
    return () => clearTimeout(debounceTimer);
  }, [searchQuery]);

  const clearSearch = useCallback(() => {
    setSearchQuery("");
    setSearchResults([]);
  }, []);

  const handleResultClick = useCallback((result: SearchResult) => {
    clearSearch();
    if (result.type === "session") {
      router.push(`/dashboard/sessions/${result.id}`);
    }
  }, [router, clearSearch]);

  return (
    <div className="flex h-screen overflow-hidden">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/40 backdrop-blur-sm transition-opacity lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <div
        className={clsx(
          "fixed inset-y-0 left-0 z-40 transition-transform duration-300 ease-out lg:static lg:z-auto",
          sidebarOpen ? "translate-x-0" : "-translate-x-full lg:translate-x-0"
        )}
      >
        <Sidebar onClose={() => setSidebarOpen(false)} />
      </div>

      {/* Main area */}
      <div className="flex flex-1 flex-col overflow-hidden">
        {/* Top header */}
        <header className="flex h-16 items-center justify-between border-b border-[hsl(var(--border))] bg-[hsl(var(--card))] px-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => setSidebarOpen(true)}
              className="rounded-lg p-2 text-[hsl(var(--muted-foreground))] transition-colors hover:bg-[hsl(var(--accent))] hover:text-[hsl(var(--foreground))] lg:hidden"
              aria-label="Open sidebar"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5" />
              </svg>
            </button>

            {/* Search */}
            <div className="relative hidden sm:block">
              <div className={`flex items-center gap-2 rounded-xl border transition-all ${
                searchFocused || searchResults.length > 0 ? 'border-[hsl(var(--primary))] bg-[hsl(var(--card))]' : 'border-transparent bg-[hsl(var(--secondary))]'
              } px-3 py-2`}>
                <svg className="h-4 w-4 text-[hsl(var(--muted-foreground))]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search sessions..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onFocus={() => setSearchFocused(true)}
                  onBlur={() => setTimeout(() => setSearchFocused(false), 200)}
                  className="flex-1 bg-transparent border-none outline-none text-[13px] text-[hsl(var(--foreground))] placeholder:text-[hsl(var(--muted-foreground))] min-w-[200px]"
                />
                {searchQuery && (
                  <button
                    onClick={clearSearch}
                    className="text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
                  >
                    <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                )}
              </div>

              {/* Search Results Dropdown */}
              {searchFocused && searchResults.length > 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl border border-[hsl(var(--border))] shadow-lg overflow-hidden z-50">
                  {searching && (
                    <div className="px-4 py-3 text-sm text-[hsl(var(--muted-foreground))]">Searching...</div>
                  )}
                  {!searching && searchResults.map((result) => (
                    <button
                      key={result.id}
                      onClick={() => handleResultClick(result)}
                      className="w-full px-4 py-3 text-left hover:bg-[hsl(var(--accent))] transition-colors border-b border-[hsl(var(--border))] last:border-b-0"
                    >
                      <div className="flex items-center gap-3">
                        <span className="font-mono text-xs text-[hsl(var(--primary))]">{result.title}</span>
                        {result.url && <span className="text-sm text-[hsl(var(--foreground))] truncate">{result.url}</span>}
                        {result.emotion && (
                          <span className="text-xs capitalize px-2 py-0.5 rounded-full bg-[hsl(var(--secondary))]">{result.emotion}</span>
                        )}
                      </div>
                    </button>
                  ))}
                </div>
              )}

              {/* No Results */}
              {searchFocused && searchQuery.length >= 2 && !searching && searchResults.length === 0 && (
                <div className="absolute top-full left-0 right-0 mt-2 bg-white rounded-xl border border-[hsl(var(--border))] shadow-lg p-4 z-50">
                  <p className="text-sm text-[hsl(var(--muted-foreground))]">No sessions found matching "{searchQuery}"</p>
                </div>
              )}
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Theme toggle */}
            <button
              onClick={toggleTheme}
              className="rounded-lg p-2 text-[hsl(var(--muted-foreground))] transition-all hover:bg-[hsl(var(--accent))] hover:text-[hsl(var(--foreground))]"
              aria-label="Toggle theme"
            >
              {dark ? (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z" />
                </svg>
              ) : (
                <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z" />
                </svg>
              )}
            </button>

            {/* Notification bell */}
            <button className="relative rounded-lg p-2 text-[hsl(var(--muted-foreground))] transition-all hover:bg-[hsl(var(--accent))] hover:text-[hsl(var(--foreground))]">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M14.857 17.082a23.848 23.848 0 005.454-1.31A8.967 8.967 0 0118 9.75v-.7V9A6 6 0 006 9v.75a8.967 8.967 0 01-2.312 6.022c1.733.64 3.56 1.085 5.455 1.31m5.714 0a24.255 24.255 0 01-5.714 0m5.714 0a3 3 0 11-5.714 0" />
              </svg>
            </button>

            {/* Avatar - clickable, goes to settings */}
            <Link href="/dashboard/settings" className="h-7 w-7 rounded-lg bg-gradient-to-br from-[hsl(var(--primary))] to-[#4CAF50] flex items-center justify-center text-[11px] font-semibold text-white hover:opacity-80 transition-opacity">
              M
            </Link>
          </div>
        </header>

        {/* Page content */}
        <main className="flex-1 overflow-y-auto bg-[hsl(var(--background))] p-6">
          <div className="animate-fade-in">{children}</div>
        </main>
      </div>
    </div>
  );
}
