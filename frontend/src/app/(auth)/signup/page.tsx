/* ────────────────────────────────────────────────
   Signup Page - Create a new EmoraTest account
   ──────────────────────────────────────────────── */

"use client";

import { useState } from "react";
import { API_BASE } from "@/lib/api";

interface FieldError {
  name?: string;
  email?: string;
  password?: string;
  workspaceName?: string;
}

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldError>({});
  const [passwordStrength, setPasswordStrength] = useState(0);
  const [signupSuccess, setSignupSuccess] = useState(false);
  const [signupEmail, setSignupEmail] = useState("");
  const [resendLoading, setResendLoading] = useState(false);
  const [resendSuccess, setResendSuccess] = useState(false);

  // Password strength rules
  const getPasswordStrength = (pwd: string) => {
    let strength = 0;
    if (pwd.length >= 8) strength++;
    if (/[0-9]/.test(pwd)) strength++;
    if (/[A-Z]/.test(pwd)) strength++;
    if (/[!@#$%^&*]/.test(pwd)) strength++;
    return strength;
  };

  const getStrengthLabel = (strength: number) => {
    switch (strength) {
      case 0: return "";
      case 1: return "Weak";
      case 2: return "Fair";
      case 3: return "Good";
      case 4: return "Strong";
      default: return "";
    }
  };

  const getStrengthColor = (strength: number) => {
    switch (strength) {
      case 1: return "#EF4444"; // red
      case 2: return "#F97316"; // orange
      case 3: return "#F59E0B"; // yellow
      case 4: return "#10B981"; // green
      default: return "#E5E7EB";
    }
  };

  const validateForm = (): boolean => {
    const errors: FieldError = {};

    if (!name.trim()) {
      errors.name = "Name is required";
    }

    if (!email.trim()) {
      errors.email = "Email is required";
    } else if (!email.includes("@")) {
      errors.email = "Please enter a valid email";
    }

    if (!password) {
      errors.password = "Password is required";
    } else if (password.length < 8) {
      errors.password = "Password must be at least 8 characters";
    } else if (!/(?=.*[0-9])(?=.*[A-Z])/.test(password)) {
      errors.password = "Password must contain a number and uppercase letter";
    } else if (passwordStrength < 2) {
      errors.password = "Please choose a stronger password";
    }

    if (!workspaceName.trim()) {
      errors.workspaceName = "Workspace name is required";
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handlePasswordChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const pwd = e.target.value;
    setPassword(pwd);
    setPasswordStrength(getPasswordStrength(pwd));
    // Clear password error when user types
    setFieldErrors((prev) => ({ ...prev, password: undefined }));
  };

  const handleResendVerification = async () => {
    if (!signupEmail) return;

    setResendLoading(true);
    setResendSuccess(false);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      if (!apiUrl) throw new Error("API URL not configured");

      const res = await fetch(`${apiUrl}/api/v1/auth/resend-verification`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ email: signupEmail }),
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

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${API_BASE}/api/v1/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name,
          email,
          password,
          workspace_name: workspaceName,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Signup failed");
      }

      const data = await res.json();

      // Show success message instead of redirecting
      setSignupSuccess(true);
      setSignupEmail(data.email || email);
    } catch (err) {
      if (err && typeof err === "object" && "detail" in err) {
        setError((err as any).detail);
      } else {
        setError(err instanceof Error ? err.message : "Signup failed");
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
        {signupSuccess ? (
          /* Success State */
          <div style={{ textAlign: "center" }}>
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
            <h1
              style={{
                fontSize: "24px",
                fontWeight: "700",
                color: "#111318",
                margin: "0 0 12px 0",
              }}
            >
              Check your email!
            </h1>
            <p
              style={{
                fontSize: "15px",
                color: "#6B7280",
                margin: "0 0 8px 0",
                lineHeight: "1.6",
              }}
            >
              We've sent a verification link to:
            </p>
            <p
              style={{
                fontSize: "15px",
                fontWeight: "600",
                color: "#111318",
                margin: "0 0 24px 0",
              }}
            >
              {signupEmail}
            </p>
            <p
              style={{
                fontSize: "14px",
                color: "#6B7280",
                margin: "0 0 24px 0",
                lineHeight: "1.5",
              }}
            >
              Click the link in the email to verify your account and start using EmoraTest.
            </p>

            {/* Resend success message */}
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
                Verification email sent! Check your inbox.
              </div>
            )}

            <button
              onClick={handleResendVerification}
              disabled={resendLoading}
              style={{
                background: "white",
                border: "1.5px solid #E5E7EB",
                color: "#374151",
                borderRadius: "10px",
                padding: "11px 16px",
                fontSize: "14px",
                fontWeight: "500",
                cursor: resendLoading ? "not-allowed" : "pointer",
                opacity: resendLoading ? 0.6 : 1,
                transition: "opacity 150ms ease",
                marginBottom: "16px",
              }}
            >
              {resendLoading ? "Sending..." : "Resend verification email"}
            </button>

            <div style={{ fontSize: "13px", color: "#6B7280" }}>
              Didn't receive the email? Check your spam folder.
            </div>
          </div>
        ) : (
          /* Signup Form */
          <>
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
              Create your account
            </h1>
            <p
              style={{
                fontSize: "15px",
                color: "#10B981",
                margin: "0 0 32px 0",
                fontWeight: "500",
              }}
            >
              Free forever. No credit card required.
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

        {/* Form */}
        <form onSubmit={handleSignup} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          {/* Full Name */}
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label
              htmlFor="name"
              style={{
                fontSize: "13px",
                fontWeight: "500",
                color: "#374151",
              }}
            >
              Full Name
            </label>
            <input
              id="name"
              type="text"
              placeholder="Your name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setFieldErrors((prev) => ({ ...prev, name: undefined }));
              }}
              disabled={loading}
              autoComplete="name"
              style={{
                background: "#F9FAFB",
                border: fieldErrors.name ? "1.5px solid #FECACA" : "1.5px solid #E5E7EB",
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
                if (!fieldErrors.name) {
                  e.currentTarget.style.borderColor = "#7C3AED";
                  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.08)";
                }
              }}
              onBlur={(e) => {
                if (!fieldErrors.name) {
                  e.currentTarget.style.borderColor = "#E5E7EB";
                  e.currentTarget.style.boxShadow = "none";
                }
              }}
            />
            {fieldErrors.name && (
              <p
                style={{
                  fontSize: "12px",
                  color: "#DC2626",
                  margin: "4px 0 0 0",
                }}
              >
                {fieldErrors.name}
              </p>
            )}
          </div>

          {/* Work Email */}
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label
              htmlFor="email"
              style={{
                fontSize: "13px",
                fontWeight: "500",
                color: "#374151",
              }}
            >
              Work Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setFieldErrors((prev) => ({ ...prev, email: undefined }));
              }}
              disabled={loading}
              autoComplete="email"
              style={{
                background: "#F9FAFB",
                border: fieldErrors.email ? "1.5px solid #FECACA" : "1.5px solid #E5E7EB",
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
                if (!fieldErrors.email) {
                  e.currentTarget.style.borderColor = "#7C3AED";
                  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.08)";
                }
              }}
              onBlur={(e) => {
                if (!fieldErrors.email) {
                  e.currentTarget.style.borderColor = "#E5E7EB";
                  e.currentTarget.style.boxShadow = "none";
                }
              }}
            />
            {fieldErrors.email && (
              <p
                style={{
                  fontSize: "12px",
                  color: "#DC2626",
                  margin: "4px 0 0 0",
                }}
              >
                {fieldErrors.email}
              </p>
            )}
          </div>

          {/* Password */}
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
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
            <input
              id="password"
              type="password"
              placeholder="Min. 8 characters"
              value={password}
              onChange={handlePasswordChange}
              disabled={loading}
              autoComplete="new-password"
              style={{
                background: "#F9FAFB",
                border: fieldErrors.password ? "1.5px solid #FECACA" : "1.5px solid #E5E7EB",
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
                if (!fieldErrors.password) {
                  e.currentTarget.style.borderColor = "#7C3AED";
                  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.08)";
                }
              }}
              onBlur={(e) => {
                if (!fieldErrors.password) {
                  e.currentTarget.style.borderColor = "#E5E7EB";
                  e.currentTarget.style.boxShadow = "none";
                }
              }}
            />
            {/* Password Strength Indicator */}
            {password && (
              <div style={{ marginTop: "8px" }}>
                <div
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "8px",
                  }}
                >
                  <div
                    style={{
                      flex: 1,
                      height: "4px",
                      background: "#E5E7EB",
                      borderRadius: "2px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        width: passwordStrength > 0 ? `${passwordStrength * 25}%` : "0%",
                        height: "100%",
                        background: getStrengthColor(passwordStrength),
                        transition: "all 200ms ease",
                      }}
                    />
                  </div>
                  <span
                    style={{
                      fontSize: "11px",
                      fontWeight: "500",
                      color: getStrengthColor(passwordStrength),
                      minWidth: "35px",
                    }}
                  >
                    {getStrengthLabel(passwordStrength)}
                  </span>
                </div>
              </div>
            )}
            {fieldErrors.password && (
              <p
                style={{
                  fontSize: "12px",
                  color: "#DC2626",
                  margin: "4px 0 0 0",
                }}
              >
                {fieldErrors.password}
              </p>
            )}
          </div>

          {/* Workspace Name */}
          <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
            <label
              htmlFor="workspace"
              style={{
                fontSize: "13px",
                fontWeight: "500",
                color: "#374151",
              }}
            >
              Workspace Name
            </label>
            <input
              id="workspace"
              type="text"
              placeholder="Your company name"
              value={workspaceName}
              onChange={(e) => {
                setWorkspaceName(e.target.value);
                setFieldErrors((prev) => ({ ...prev, workspaceName: undefined }));
              }}
              disabled={loading}
              autoComplete="organization"
              style={{
                background: "#F9FAFB",
                border: fieldErrors.workspaceName ? "1.5px solid #FECACA" : "1.5px solid #E5E7EB",
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
                if (!fieldErrors.workspaceName) {
                  e.currentTarget.style.borderColor = "#7C3AED";
                  e.currentTarget.style.boxShadow = "0 0 0 3px rgba(124,58,237,0.08)";
                }
              }}
              onBlur={(e) => {
                if (!fieldErrors.workspaceName) {
                  e.currentTarget.style.borderColor = "#E5E7EB";
                  e.currentTarget.style.boxShadow = "none";
                }
              }}
            />
            {fieldErrors.workspaceName && (
              <p
                style={{
                  fontSize: "12px",
                  color: "#DC2626",
                  margin: "4px 0 0 0",
                }}
              >
                {fieldErrors.workspaceName}
              </p>
            )}
          </div>

          {/* GDPR Consent Checkbox */}
          <div style={{ display: "flex", gap: "10px", alignItems: "flex-start" }}>
            <input
              id="consent"
              type="checkbox"
              required
              style={{
                marginTop: "3px",
                width: "16px",
                height: "16px",
                accentColor: "#007BFF",
                cursor: "pointer",
              }}
            />
            <label
              htmlFor="consent"
              style={{
                fontSize: "13px",
                color: "#374151",
                lineHeight: "1.5",
                cursor: "pointer",
              }}
            >
              I agree to the{" "}
              <a
                href="/privacy"
                style={{ color: "#007BFF", textDecoration: "none" }}
                target="_blank"
                rel="noopener noreferrer"
              >
                Privacy Policy
              </a>
              {" and "}
              <a
                href="/terms"
                style={{ color: "#007BFF", textDecoration: "none" }}
                target="_blank"
                rel="noopener noreferrer"
              >
                Terms of Service
              </a>
            </label>
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
            {loading ? "Creating account..." : "Create Free Account"}
          </button>
        </form>
          </>
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
        Already have an account?{" "}
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
