/* ────────────────────────────────────────────────
   Login Page - Sign in to EmoraTest
   ──────────────────────────────────────────────── */

"use client";

import { useState, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { authLogin } from "@/lib/api";

function LoginForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const verified = searchParams.get("verified"); // true, false, expired

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [showResend, setShowResend] = useState(false);
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  // Show verification success message from URL param
  useEffect(() => {
    if (verified === "true") {
      setResendSuccess(true);
      setTimeout(() => setResendSuccess(false), 5000);
    }
  }, [verified]);

  const handleResendVerification = async () => {
    if (!email) {
      setError("Please enter your email address first");
      return;
    }

    setResendLoading(true);
    setError("");

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) throw new Error("API URL not configured");

      const res = await fetch(`${apiUrl}/api/v1/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Failed to resend verification email");
      }

      setResendSuccess(true);
      setTimeout(() => setResendSuccess(false), 5000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend verification email");
    } finally {
      setResendLoading(false);
    }
  };

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setShowResend(false);

    try {
      const data = await authLogin({ email, password });

      // Wait for cookie to be set, then redirect
      // Use router for client-side navigation instead of hard navigation
      await new Promise(resolve => setTimeout(resolve, 300));

      // Redirect based on onboarding status
      if (!data.onboarding_completed) {
        window.location.href = "/dashboard/welcome";
      } else {
        window.location.href = "/dashboard";
      }
    } catch (err) {
      if (err && typeof err === "object" && "detail" in err) {
        const detail = (err as any).detail;
        if (detail === "email_not_verified" || detail.includes("verify your email")) {
          setError("Please verify your email before logging in. Check your inbox for the verification link.");
          setShowResend(true);
        } else {
          setError(detail);
        }
      } else {
        setError(err instanceof Error ? err.message : "Login failed");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ width: "100%", maxWidth: "400px", display: "flex", flexDirection: "column", alignItems: "center", gap: 0 }}>
      {/* Logo Block */}
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          gap: "8px",
          marginBottom: "40px",
        }}
      >
        <a href="/" style={{ textDecoration: "none", lineHeight: 0 }}>
          <img src="/logo2.png" alt="EmoraTest" style={{ height: "80px", width: "auto" }} />
        </a>
        <span
          style={{
            fontSize: "24px",
            fontWeight: "700",
            color: "#111318",
            letterSpacing: "-0.3px",
          }}
        >
          EmoraTest
        </span>
      </div>

      {/* Form Card */}
      <div
        style={{
          background: "white",
          border: "1px solid #E5E7EB",
          borderRadius: "24px",
          padding: "48px",
          width: "100%",
          boxShadow: "0 4px 24px rgba(0,0,0,0.06)",
        }}
      >
        {/* Header */}
        <h1
          style={{
            fontSize: "28px",
            fontWeight: "700",
            color: "#111318",
            margin: "0 0 8px 0",
            letterSpacing: "-0.5px",
          }}
        >
          Welcome back
        </h1>
        <p
          style={{
            fontSize: "15px",
            color: "#6B7280",
            margin: "0 0 32px 0",
          }}
        >
          Sign in to your workspace to continue
        </p>

        {/* Success banner (email verified) */}
        {resendSuccess && (
          <div
            style={{
              background: "#F0FDF4",
              border: "1px solid #BBF7D0",
              borderRadius: "10px",
              padding: "12px 16px",
              fontSize: "14px",
              color: "#16A34A",
              marginBottom: "16px",
            }}
          >
            {verified === "true" ? "Email verified successfully! Please log in." : "Verification email sent. Please check your inbox."}
          </div>
        )}

        {/* Error banner */}
        {error && (
          <div
            style={{
              background: "#FEF2F2",
              border: "1px solid #FECACA",
              borderRadius: "10px",
              padding: "12px 16px",
              fontSize: "14px",
              color: "#DC2626",
              marginBottom: "16px",
            }}
          >
            {error}
            {showResend && (
              <button
                onClick={handleResendVerification}
                disabled={resendLoading}
                style={{
                  background: "transparent",
                  border: "none",
                  color: "#007BFF",
                  textDecoration: "underline",
                  fontSize: "13px",
                  fontWeight: "500",
                  cursor: resendLoading ? "not-allowed" : "pointer",
                  marginTop: "8px",
                  padding: 0,
                }}
              >
                {resendLoading ? "Sending..." : "Resend verification email"}
              </button>
            )}
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleLogin} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Email */}
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label
              htmlFor="email"
              style={{
                fontSize: "13px",
                fontWeight: "500",
                color: "#374151",
              }}
            >
              Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              disabled={loading}
              autoComplete="email"
              style={{
                background: "#F9FAFB",
                border: "1.5px solid #E5E7EB",
                borderRadius: "10px",
                padding: "11px 14px",
                fontSize: "15px",
                color: "#111318",
                width: "100%",
                outline: "none",
                transition: "all 150ms ease",
                boxSizing: "border-box",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "#7C3AED";
                e.currentTarget.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.08)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "#E5E7EB";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          {/* Password */}
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <div
              style={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
              }}
            >
              <label
                htmlFor="password"
                style={{
                  fontSize: "13px",
                  fontWeight: "500",
                  color: "#374151",
                }}
              >
                Password
              </label>
              <a
                href="/forgot-password"
                style={{
                  fontSize: "13px",
                  color: "#007BFF",
                  textDecoration: "none",
                }}
              >
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
              disabled={loading}
              autoComplete="current-password"
              style={{
                background: "#F9FAFB",
                border: "1.5px solid #E5E7EB",
                borderRadius: "10px",
                padding: "11px 14px",
                fontSize: "15px",
                color: "#111318",
                width: "100%",
                outline: "none",
                transition: "all 150ms ease",
                boxSizing: "border-box",
              }}
              onFocus={(e) => {
                e.currentTarget.style.borderColor = "#7C3AED";
                e.currentTarget.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.08)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.borderColor = "#E5E7EB";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            style={{
              background: "linear-gradient(135deg, #007BFF, #7C3AED)",
              color: "white",
              border: "none",
              borderRadius: "10px",
              padding: "13px",
              fontSize: "15px",
              fontWeight: "600",
              width: "100%",
              cursor: loading ? "not-allowed" : "pointer",
              opacity: loading ? 0.6 : 1,
              marginTop: "8px",
              transition: "opacity 150ms ease, transform 150ms ease",
              boxSizing: "border-box",
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                e.currentTarget.style.opacity = "0.88";
                e.currentTarget.style.transform = "translateY(-1px)";
              }
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.opacity = loading ? "0.6" : "1";
              e.currentTarget.style.transform = "translateY(0)";
            }}
          >
            {loading ? "Signing in..." : "Sign In"}
          </button>
        </form>
      </div>

      {/* Below card */}
      <p
        style={{
          marginTop: "20px",
          fontSize: "14px",
          color: "#6B7280",
          textAlign: "center",
        }}
      >
        Don&apos;t have an account?{" "}
        <a
          href="/signup"
          style={{
            color: "#007BFF",
            fontWeight: "600",
            textDecoration: "none",
          }}
        >
          Start free →
        </a>
      </p>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={
      <div style={{ width: "100%", maxWidth: "400px", display: "flex", flexDirection: "column", alignItems: "center", gap: 0 }}>
        <div
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            gap: "4px",
            marginBottom: "32px",
          }}
        >
          <a href="/" style={{ textDecoration: "none", lineHeight: 0 }}>
            <img src="/logo2.png" alt="EmoraTest" style={{ height: "64px", width: "auto" }} />
          </a>
          <span
            style={{
              fontSize: "20px",
              fontWeight: "700",
              color: "#111318",
              letterSpacing: "-0.3px",
            }}
          >
            EmoraTest
          </span>
        </div>
        <div style={{ textAlign: "center", color: "#6B7280" }}>Loading...</div>
      </div>
    }>
      <LoginForm />
    </Suspense>
  );
}
