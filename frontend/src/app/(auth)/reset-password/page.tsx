/* ────────────────────────────────────────────────
   Reset Password Page - Set New Password
   ──────────────────────────────────────────────── */

"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import Link from "next/link";

function ResetPasswordForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState("");
  const [invalidToken, setInvalidToken] = useState(false);

  useEffect(() => {
    if (!token) {
      setInvalidToken(true);
      setError("No reset token provided. Please request a new password reset link.");
    }
  }, [token]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setSuccess(false);

    // Validate passwords match
    if (password !== confirmPassword) {
      setError("Passwords do not match");
      return;
    }

    // Validate password strength
    if (password.length < 8) {
      setError("Password must be at least 8 characters");
      return;
    }
    if (!/[A-Z]/.test(password)) {
      setError("Password must contain at least one uppercase letter");
      return;
    }
    if (!/[a-z]/.test(password)) {
      setError("Password must contain at least one lowercase letter");
      return;
    }
    if (!/\d/.test(password)) {
      setError("Password must contain at least one digit");
      return;
    }

    setLoading(true);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) throw new Error("API URL not configured");
      const res = await fetch(`${apiUrl}/api/v1/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ token: token || "", new_password: password }),
      });

      const data = await res.json();

      if (!res.ok) {
        if (data.detail?.includes("expired") || data.detail?.includes("Invalid")) {
          setInvalidToken(true);
        }
        throw new Error(data.detail || "Failed to reset password");
      }

      setSuccess(true);
      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push("/login");
      }, 3000);
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
          gap: "8px",
          marginBottom: "40px",
        }}
      >
        <Link href="/" style={{ textDecoration: "none", lineHeight: 0 }}>
          <img src="/logo2.png" alt="EmoraTest" style={{ height: "80px", width: "auto" }} />
        </Link>
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
          Set new password
        </h1>
        <p
          style={{
            fontSize: "15px",
            color: "#6B7280",
            margin: "0 0 32px 0",
          }}
        >
          Enter your new password below
        </p>

        {/* Error banner */}
        {error && (
          <div
            style={{
              background: invalidToken ? "#FEF2F2" : "#FEF2F2",
              border: invalidToken ? "1px solid #FECACA" : "1px solid #FECACA",
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
            Password has been reset successfully! Redirecting to login...
          </div>
        )}

        {!success && !invalidToken ? (
          /* Form */
          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            {/* New Password */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label
                htmlFor="password"
                style={{
                  fontSize: "13px",
                  fontWeight: "500",
                  color: "#374151",
                }}
              >
                New Password
              </label>
              <input
                id="password"
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={loading}
                autoComplete="new-password"
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
              <p style={{ fontSize: "12px", color: "#9CA3AF", margin: 0 }}>
                Must be 8+ characters with uppercase, lowercase, and a number
              </p>
            </div>

            {/* Confirm Password */}
            <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
              <label
                htmlFor="confirmPassword"
                style={{
                  fontSize: "13px",
                  fontWeight: "500",
                  color: "#374151",
                }}
              >
                Confirm Password
              </label>
              <input
                id="confirmPassword"
                type="password"
                placeholder="••••••••"
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                required
                disabled={loading}
                autoComplete="new-password"
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
              {loading ? "Resetting..." : "Reset Password"}
            </button>
          </form>
        ) : invalidToken ? (
          /* Request new link button */
          <div style={{ textAlign: "center", marginTop: "8px" }}>
            <button
              onClick={() => router.push("/forgot-password")}
              style={{
                background: "linear-gradient(135deg, #007BFF, #7C3AED)",
                color: "white",
                border: "none",
                borderRadius: "10px",
                padding: "13px 24px",
                fontSize: "15px",
                fontWeight: "600",
                cursor: "pointer",
                transition: "opacity 150ms ease",
              }}
            >
              Request New Reset Link
            </button>
          </div>
        ) : null}
      </div>

      {/* Below card */}
      {!invalidToken && (
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
          </Link>
        </p>
      )}
    </div>
  );
}

export default function ResetPasswordPage() {
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
          <Link href="/" style={{ textDecoration: "none", lineHeight: 0 }}>
            <img src="/logo2.png" alt="EmoraTest" style={{ height: "64px", width: "auto" }} />
          </Link>
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
      <ResetPasswordForm />
    </Suspense>
  );
}
