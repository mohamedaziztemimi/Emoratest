/* ────────────────────────────────────────────────
   Forgot Password Page - Request Reset Link
   ──────────────────────────────────────────────── */

"use client";

import { useState } from "react";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess(false);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        throw new Error("Failed to request password reset");
      }

      setSuccess(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "An error occurred");
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

      {/* Form Card */}
      <div
        style={{
          background: "white",
          border: "1px solid #E5E7EB",
          borderRadius: "20px",
          padding: "36px 40px",
          width: "100%",
        }}
      >
        {/* Header */}
        <h1
          style={{
            fontSize: "24px",
            fontWeight: "700",
            color: "#111318",
            margin: "0 0 6px 0",
            letterSpacing: "-0.3px",
          }}
        >
          Forgot your password?
        </h1>
        <p
          style={{
            fontSize: "14px",
            color: "#6B7280",
            margin: "0 0 28px 0",
          }}
        >
          Enter your email and we'll send you a reset link
        </p>

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
          </div>
        )}

        {/* Success banner */}
        {success && (
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
            If an account exists with that email, a password reset link has been sent.
          </div>
        )}

        {!success ? (
          /* Form */
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
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
              {loading ? "Sending..." : "Send Reset Link"}
            </button>
          </form>
        ) : (
          /* Resend link */
          <div style={{ textAlign: "center", marginTop: "8px" }}>
            <p
              style={{
                fontSize: "13px",
                color: "#6B7280",
                marginBottom: "16px",
              }}
            >
              Didn't receive the email? Check your spam folder or request a new link.
            </p>
            <button
              onClick={handleSubmit}
              disabled={loading}
              style={{
                background: "white",
                border: "1.5px solid #E5E7EB",
                color: "#374151",
                borderRadius: "10px",
                padding: "11px 16px",
                fontSize: "14px",
                fontWeight: "500",
                cursor: loading ? "not-allowed" : "pointer",
                opacity: loading ? 0.6 : 1,
                transition: "opacity 150ms ease",
              }}
            >
              {loading ? "Sending..." : "Resend Email"}
            </button>
          </div>
        )}
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
        Remember your password?{" "}
        <a
          href="/login"
          style={{
            color: "#007BFF",
            fontWeight: "600",
            textDecoration: "none",
          }}
        >
          Sign in →
        </a>
      </p>
    </div>
  );
}
