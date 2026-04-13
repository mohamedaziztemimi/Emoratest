/* ────────────────────────────────────────────────
   Login Page - Sign in to EmoraTest
   ──────────────────────────────────────────────── */

"use client";

import { useState } from "react";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Login failed");
      }

      window.location.href = "/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[440px]">
      {/* Logo */}
      <div className="flex items-center justify-center gap-2.5 mb-8">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#007BFF] to-[#7C3AED] flex items-center justify-center text-white font-bold text-lg">
          E
        </div>
        <span className="text-xl font-bold bg-gradient-to-r from-[#007BFF] to-[#7C3AED] bg-clip-text text-transparent">
          EmoraTest
        </span>
      </div>

      {/* Card */}
      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-[#111318] mb-1">Welcome back</h2>
          <p className="text-sm text-[#6B7280]">Sign in to your EmoraTest workspace</p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} className="space-y-4">
          {/* Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-[#111318] mb-1.5">
              Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-[#111318] placeholder:text-gray-400 focus:outline-none focus:border-[#007BFF] focus:ring-2 focus:ring-[#007BFF]/20 transition-colors"
              disabled={loading}
            />
          </div>

          {/* Password */}
          <div>
            <div className="flex items-center justify-between mb-1.5">
              <label htmlFor="password" className="block text-sm font-medium text-[#111318]">
                Password
              </label>
              <a href="/forgot-password" className="text-sm text-[#007BFF] hover:underline">
                Forgot password?
              </a>
            </div>
            <input
              id="password"
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full px-4 py-2.5 rounded-lg border border-gray-300 text-[#111318] placeholder:text-gray-400 focus:outline-none focus:border-[#007BFF] focus:ring-2 focus:ring-[#007BFF]/20 transition-colors"
              disabled={loading}
            />
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg bg-gradient-to-r from-[#007BFF] to-[#7C3AED] text-white font-semibold hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>

        {/* Sign up link */}
        <p className="mt-6 text-center text-sm text-[#6B7280]">
          Don't have an account?{" "}
          <a href="/signup" className="text-[#007BFF] font-semibold hover:underline">
            Start free →
          </a>
        </p>
      </div>
    </div>
  );
}
