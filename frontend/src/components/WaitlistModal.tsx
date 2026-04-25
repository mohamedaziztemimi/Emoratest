"use client";

import { useState, useRef } from "react";

interface WaitlistModalProps {
  isOpen: boolean;
  onClose: () => void;
  prefillEmail?: string;
}

export function WaitlistModal({ isOpen, onClose, prefillEmail }: WaitlistModalProps) {
  const [email, setEmail] = useState(prefillEmail || "");
  const [companyName, setCompanyName] = useState("");
  const [planInterest, setPlanInterest] = useState("growth");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const res = await fetch(`${apiUrl}/api/v1/waitlist`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          email,
          company_name: companyName || undefined,
          plan_interest: planInterest,
          message: message || undefined,
        }),
      });

      if (!res.ok) {
        throw new Error("Failed to join waitlist");
      }

      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
      }, 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to join waitlist");
    } finally {
      setLoading(false);
    }
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        onClick={onClose}
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0, 0, 0, 0.4)",
          backdropFilter: "blur(4px)",
          zIndex: 50,
        }}
      />

      {/* Modal */}
      <div
        style={{
          position: "fixed",
          top: "50%",
          left: "50%",
          transform: "translate(-50%, -50%)",
          background: "white",
          borderRadius: "20px",
          padding: success ? "40px" : "32px",
          width: success ? "400px" : "480px",
          maxWidth: "calc(100vw - 48px)",
          zIndex: 51,
          boxShadow: "0 20px 60px rgba(0, 0, 0, 0.15)",
        }}
      >
        {success ? (
          <>
            {/* Success checkmark */}
            <div
              style={{
                width: "64px",
                height: "64px",
                borderRadius: "50%",
                background: "#10B981",
                color: "white",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 20px auto",
                fontSize: "32px",
              }}
            >
              ✓
            </div>
            <h3
              style={{
                fontSize: "22px",
                fontWeight: "700",
                color: "#111318",
                textAlign: "center",
                margin: "0 0 12px 0",
              }}
            >
              You're on the list!
            </h3>
            <p
              style={{
                fontSize: "15px",
                color: "#6B7280",
                textAlign: "center",
                margin: 0,
              }}
            >
              We'll be in touch when paid plans are ready.
            </p>
          </>
        ) : (
          <>
            {/* Header */}
            <h3
              style={{
                fontSize: "22px",
                fontWeight: "700",
                color: "#111318",
                margin: "0 0 8px 0",
              }}
            >
              Join the waiting list
            </h3>
            <p
              style={{
                fontSize: "14px",
                color: "#6B7280",
                margin: "0 0 24px 0",
                lineHeight: "1.5",
              }}
            >
              We're in beta and opening paid plans soon. Leave your details and we'll
              reach out when ready.
            </p>

            {/* Form */}
            <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              {/* Email */}
              <div>
                <label
                  style={{
                    fontSize: "13px",
                    fontWeight: "500",
                    color: "#374151",
                    display: "block",
                    marginBottom: "6px",
                  }}
                >
                  Email <span style={{ color: "#EF4444" }}>*</span>
                </label>
                <input
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: "1px solid #D1D5DB",
                    borderRadius: "8px",
                    fontSize: "14px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              {/* Company Name */}
              <div>
                <label
                  style={{
                    fontSize: "13px",
                    fontWeight: "500",
                    color: "#374151",
                    display: "block",
                    marginBottom: "6px",
                  }}
                >
                  Company name <span style={{ color: "#9CA3AF", fontSize: "11px" }}>(optional)</span>
                </label>
                <input
                  type="text"
                  value={companyName}
                  onChange={(e) => setCompanyName(e.target.value)}
                  placeholder="Your company"
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: "1px solid #D1D5DB",
                    borderRadius: "8px",
                    fontSize: "14px",
                    boxSizing: "border-box",
                  }}
                />
              </div>

              {/* Plan Interest */}
              <div>
                <label
                  style={{
                    fontSize: "13px",
                    fontWeight: "500",
                    color: "#374151",
                    display: "block",
                    marginBottom: "6px",
                  }}
                >
                  Plan interested in
                </label>
                <select
                  value={planInterest}
                  onChange={(e) => setPlanInterest(e.target.value)}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: "1px solid #D1D5DB",
                    borderRadius: "8px",
                    fontSize: "14px",
                    boxSizing: "border-box",
                    background: "white",
                  }}
                >
                  <option value="growth">Growth - $29/month</option>
                  <option value="scale">Scale - $79/month</option>
                </select>
              </div>

              {/* Message */}
              <div>
                <label
                  style={{
                    fontSize: "13px",
                    fontWeight: "500",
                    color: "#374151",
                    display: "block",
                    marginBottom: "6px",
                  }}
                >
                  Message <span style={{ color: "#9CA3AF", fontSize: "11px" }}>(optional)</span>
                </label>
                <textarea
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  placeholder="Tell us about your needs"
                  rows={3}
                  style={{
                    width: "100%",
                    padding: "10px 12px",
                    border: "1px solid #D1D5DB",
                    borderRadius: "8px",
                    fontSize: "14px",
                    boxSizing: "border-box",
                    resize: "vertical",
                  }}
                />
              </div>

              {/* Error */}
              {error && (
                <div
                  style={{
                    fontSize: "13px",
                    color: "#EF4444",
                    background: "#FEF2F2",
                    padding: "10px",
                    borderRadius: "8px",
                  }}
                >
                  {error}
                </div>
              )}

              {/* Buttons */}
              <div style={{ display: "flex", gap: "12px", marginTop: "8px" }}>
                <button
                  type="button"
                  onClick={onClose}
                  disabled={loading}
                  style={{
                    flex: 1,
                    background: "white",
                    border: "1.5px solid #E5E7EB",
                    color: "#374151",
                    borderRadius: "10px",
                    padding: "12px",
                    fontSize: "14px",
                    fontWeight: "500",
                    cursor: loading ? "not-allowed" : "pointer",
                    opacity: loading ? 0.6 : 1,
                  }}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={loading}
                  style={{
                    flex: 1,
                    background: "#007BFF",
                    color: "white",
                    border: "none",
                    borderRadius: "10px",
                    padding: "12px",
                    fontSize: "14px",
                    fontWeight: "600",
                    cursor: loading ? "not-allowed" : "pointer",
                    opacity: loading ? 0.7 : 1,
                  }}
                >
                  {loading ? "Joining..." : "Join waitlist"}
                </button>
              </div>
            </form>
          </>
        )}
      </div>
    </>
  );
}
