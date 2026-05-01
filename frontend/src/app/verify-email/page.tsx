/* ────────────────────────────────────────────────
   Email Verification Page - Verify email address
   ──────────────────────────────────────────────── */

"use client";

import { useEffect, useState, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";

function VerifyEmailForm() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const token = searchParams.get("token");

  const [status, setStatus] = useState<"loading" | "success" | "error" | "expired">("loading");
  const [email, setEmail] = useState("");

  useEffect(() => {
    if (!token) {
      setStatus("error");
      return;
    }

    const verifyEmail = async () => {
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        if (!apiUrl) throw new Error("API URL not configured");

        const res = await fetch(`${apiUrl}/api/v1/auth/verify-email?token=${token}`, {
          method: "GET",
          credentials: "include",
        });

        if (res.redirected || res.status === 302) {
          // The backend redirects to login with query params
          const location = res.headers.get("Location") || "";
          if (location.includes("verified=true")) {
            setStatus("success");
          } else if (location.includes("verified=expired")) {
            setStatus("expired");
          } else {
            setStatus("error");
          }
          // Redirect to login after 3 seconds
          setTimeout(() => {
            router.push("/login?verified=" + (location.includes("verified=true") ? "true" : location.includes("verified=expired") ? "expired" : "false"));
          }, 3000);
          return;
        }

        setStatus("success");
        setTimeout(() => {
          router.push("/login?verified=true");
        }, 3000);
      } catch (err) {
        setStatus("error");
      }
    };

    verifyEmail();
  }, [token, router]);

  const getContent = () => {
    switch (status) {
      case "loading":
        return (
          <>
            <div
              style={{
                width: "48px",
                height: "48px",
                border: "4px solid #E5E7EB",
                borderTopColor: "#007BFF",
                borderRadius: "50%",
                animation: "spin 1s linear infinite",
                margin: "0 auto 24px",
              }}
            />
            <h2
              style={{
                fontSize: "20px",
                fontWeight: "600",
                color: "#111318",
                margin: "0 0 8px 0",
              }}
            >
              Verifying your email...
            </h2>
            <p
              style={{
                fontSize: "15px",
                color: "#6B7280",
                margin: 0,
              }}
            >
              Please wait while we confirm your email address.
            </p>
          </>
        );

      case "success":
        return (
          <>
            <div
              style={{
                width: "64px",
                height: "64px",
                borderRadius: "50%",
                background: "#D1FAE5",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 24px",
              }}
            >
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" fill="#10B981" />
                <path
                  d="M8 12L11 15L16 9"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                />
              </svg>
            </div>
            <h2
              style={{
                fontSize: "24px",
                fontWeight: "700",
                color: "#111318",
                margin: "0 0 12px 0",
              }}
            >
              Email Verified!
            </h2>
            <p
              style={{
                fontSize: "15px",
                color: "#6B7280",
                margin: "0 0 24px 0",
                lineHeight: "1.6",
              }}
            >
              Your email has been successfully verified. You can now sign in to your account.
            </p>
            <p
              style={{
                fontSize: "14px",
                color: "#9CA3AF",
                margin: 0,
              }}
            >
              Redirecting to login...
            </p>
          </>
        );

      case "expired":
        return (
          <>
            <div
              style={{
                width: "64px",
                height: "64px",
                borderRadius: "50%",
                background: "#FEF3C7",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 24px",
              }}
            >
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" fill="#F59E0B" />
                <path
                  d="M12 8V12M12 16H12.01"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <h2
              style={{
                fontSize: "24px",
                fontWeight: "700",
                color: "#111318",
                margin: "0 0 12px 0",
              }}
            >
              Verification Link Expired
            </h2>
            <p
              style={{
                fontSize: "15px",
                color: "#6B7280",
                margin: "0 0 24px 0",
                lineHeight: "1.6",
              }}
            >
              The verification link has expired. Please request a new one.
            </p>
            <a
              href="/login"
              style={{
                display: "inline-block",
                background: "linear-gradient(135deg, #007BFF, #7C3AED)",
                color: "white",
                textDecoration: "none",
                padding: "13px 24px",
                borderRadius: "10px",
                fontSize: "15px",
                fontWeight: "600",
              }}
            >
              Go to Login
            </a>
          </>
        );

      case "error":
        return (
          <>
            <div
              style={{
                width: "64px",
                height: "64px",
                borderRadius: "50%",
                background: "#FEE2E2",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 24px",
              }}
            >
              <svg width="32" height="32" viewBox="0 0 24 24" fill="none">
                <circle cx="12" cy="12" r="10" fill="#EF4444" />
                <path
                  d="M15 9L9 15M9 9L15 15"
                  stroke="white"
                  strokeWidth="2"
                  strokeLinecap="round"
                />
              </svg>
            </div>
            <h2
              style={{
                fontSize: "24px",
                fontWeight: "700",
                color: "#111318",
                margin: "0 0 12px 0",
              }}
            >
              Invalid Verification Link
            </h2>
            <p
              style={{
                fontSize: "15px",
                color: "#6B7280",
                margin: "0 0 24px 0",
                lineHeight: "1.6",
              }}
            >
              This verification link is invalid or has already been used.
            </p>
            <a
              href="/login"
              style={{
                display: "inline-block",
                background: "linear-gradient(135deg, #007BFF, #7C3AED)",
                color: "white",
                textDecoration: "none",
                padding: "13px 24px",
                borderRadius: "10px",
                fontSize: "15px",
                fontWeight: "600",
              }}
            >
              Go to Login
            </a>
          </>
        );

      default:
        return null;
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

      {/* Card */}
      <div
        style={{
          background: "white",
          border: "1px solid #E5E7EB",
          borderRadius: "24px",
          padding: "48px",
          width: "100%",
          boxShadow: "0 4px 24px rgba(0,0,0,0.06)",
          textAlign: "center",
        }}
      >
        {getContent()}
      </div>

      {/* CSS for spinner animation */}
      <style jsx>{`
        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }
      `}</style>
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <Suspense
      fallback={
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
      }
    >
      <VerifyEmailForm />
    </Suspense>
  );
}
