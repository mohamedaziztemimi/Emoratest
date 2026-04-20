"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";

interface MerchantProfile {
  id: string;
  email: string;
  shop_domain: string;
  plan: string;
  is_active: boolean;
  created_at: string;
}

export default function SettingsPage() {
  // Profile state
  const [profile, setProfile] = useState<MerchantProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState<string | null>(null);

  // SDK Key state
  const [sdkKey, setSdkKey] = useState("");
  const [sdkKeyMasked, setSdkKeyMasked] = useState(true);
  const [copied, setCopied] = useState(false);
  const [revealing, setRevealing] = useState(false);

  // Modal state
  const [showRegenModal, setShowRegenModal] = useState(false);
  const [regenLoading, setRegenLoading] = useState(false);
  const [regenSuccess, setRegenSuccess] = useState(false);

  const [error, setError] = useState<string | null>(null);

  // Auto-hide timer for revealed key (30 seconds)
  const revealTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch profile on mount
  useEffect(() => {
    const fetchProfile = async () => {
      setProfileLoading(true);
      setProfileError(null);

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL;
        const res = await fetch(`${apiUrl}/api/v1/auth/me`, {
          credentials: "include",
        });

        if (res.status === 401) {
          setProfileError("Please log in to view your settings");
          return;
        }

        if (!res.ok) {
          throw new Error("Failed to fetch profile");
        }

        const data = await res.json();
        setProfile(data);
      } catch (err) {
        setProfileError(err instanceof Error ? err.message : "Failed to load profile");
      } finally {
        setProfileLoading(false);
      }
    };

    fetchProfile();
  }, []);

  // Clear timer on unmount
  useEffect(() => {
    return () => {
      if (revealTimerRef.current) {
        clearTimeout(revealTimerRef.current);
      }
    };
  }, []);

  // Reveal SDK key - calls onboarding-complete to get current key
  const revealSdkKey = useCallback(async () => {
    setRevealing(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const res = await fetch(`${apiUrl}/api/v1/auth/onboarding-complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error("Failed to retrieve SDK key");
      }

      const data = await res.json();
      if (data.sdk_key) {
        setSdkKey(data.sdk_key);
        setSdkKeyMasked(false);

        // Auto-hide after 30 seconds
        if (revealTimerRef.current) {
          clearTimeout(revealTimerRef.current);
        }
        revealTimerRef.current = setTimeout(() => {
          setSdkKeyMasked(true);
          setSdkKey("");
        }, 30000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to reveal SDK key");
    } finally {
      setRevealing(false);
    }
  }, []);

  // Copy SDK key to clipboard
  const copyToClipboard = useCallback(() => {
    if (sdkKey) {
      navigator.clipboard.writeText(sdkKey);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  }, [sdkKey]);

  // Open regenerate modal
  const openRegenModal = useCallback(() => {
    setShowRegenModal(true);
    setError(null);
  }, []);

  // Close regenerate modal
  const closeRegenModal = useCallback(() => {
    setShowRegenModal(false);
  }, []);

  // Confirm regenerate SDK key
  const confirmRegenerate = useCallback(async () => {
    setRegenLoading(true);
    setError(null);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL;
      const res = await fetch(`${apiUrl}/api/v1/auth/onboarding-complete`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error("Failed to regenerate SDK key");
      }

      const data = await res.json();
      if (data.sdk_key) {
        setSdkKey(data.sdk_key);
        setSdkKeyMasked(false); // show it immediately after regeneration
        setShowRegenModal(false);
        setRegenSuccess(true);

        // Hide success toast after 3 seconds
        setTimeout(() => setRegenSuccess(false), 3000);

        // Auto-hide after 30 seconds
        if (revealTimerRef.current) {
          clearTimeout(revealTimerRef.current);
        }
        revealTimerRef.current = setTimeout(() => {
          setSdkKeyMasked(true);
          setSdkKey("");
        }, 30000);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to regenerate SDK key");
      setShowRegenModal(false);
    } finally {
      setRegenLoading(false);
    }
  }, []);

  // Format date as "Month Year" (e.g., "April 2026")
  const formatMonthYear = (iso: string) => {
    return new Date(iso).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
    });
  };

  // Capitalize first letter of plan
  const capitalizePlan = (plan: string) => {
    return plan.charAt(0).toUpperCase() + plan.slice(1);
  };

  // Masked key display
  const maskedKey = "et_" + "•".repeat(30);

  return (
    <>
      <div className="space-y-8">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Settings</h1>
          <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">
            Manage your account and integration settings
          </p>
        </div>

        {/* SDK & Integration Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[hsl(var(--accent))]">
                <svg className="h-4 w-4 text-[hsl(var(--accent-foreground))]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
                </svg>
              </div>
              <div>
                <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">SDK & Integration</h2>
                <p className="text-[11px] text-[hsl(var(--muted-foreground))]">
                  Your SDK key for installing EmoraTest on your website
                </p>
              </div>
            </div>
          </CardHeader>
          <CardBody className="space-y-6">
            {/* Error display */}
            {error && (
              <div className="rounded-lg border border-red-200 bg-red-50 p-3 text-[12px] text-red-700">
                {error}
              </div>
            )}

            {/* SDK Key Card */}
            <div
              style={{
                background: "white",
                border: "1px solid #E5E7EB",
                borderRadius: "12px",
                padding: "24px",
              }}
            >
              {/* Label */}
              <label
                style={{
                  fontSize: "13px",
                  fontWeight: "500",
                  color: "#374151",
                  display: "block",
                  marginBottom: "4px",
                }}
              >
                SDK Key
              </label>
              <p
                style={{
                  fontSize: "12px",
                  color: "#9CA3AF",
                  margin: "0 0 12px 0",
                }}
              >
                Use this key to authenticate the EmoraTest SDK on your website. Keep it secret.
              </p>

              {/* Key Display */}
              <div
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "12px",
                }}
              >
                <code
                  style={{
                    flex: 1,
                    fontFamily: "monospace",
                    fontSize: "14px",
                    background: "#F3F4F6",
                    border: "1px solid #E5E7EB",
                    borderRadius: "8px",
                    padding: "12px 16px",
                    color: "#374151",
                  }}
                >
                  {sdkKeyMasked ? maskedKey : sdkKey}
                </code>

                {/* Reveal/Hide button */}
                <button
                  onClick={sdkKeyMasked ? revealSdkKey : () => setSdkKeyMasked(true)}
                  disabled={revealing}
                  style={{
                    background: "white",
                    border: "1px solid #E5E7EB",
                    borderRadius: "8px",
                    padding: "10px 16px",
                    fontSize: "13px",
                    fontWeight: "500",
                    color: "#374151",
                    cursor: revealing ? "not-allowed" : "pointer",
                    opacity: revealing ? 0.6 : 1,
                  }}
                >
                  {revealing ? "Loading..." : sdkKeyMasked ? "Reveal" : "Hide"}
                </button>

                {/* Copy button - only shown when revealed */}
                {!sdkKeyMasked && (
                  <button
                    onClick={copyToClipboard}
                    style={{
                      background: "#007BFF",
                      border: "none",
                      borderRadius: "8px",
                      padding: "10px 16px",
                      fontSize: "13px",
                      fontWeight: "500",
                      color: "white",
                      cursor: "pointer",
                    }}
                  >
                    {copied ? "✓ Copied!" : "Copy"}
                  </button>
                )}
              </div>

              {/* Regenerate button */}
              <div style={{ marginTop: "16px" }}>
                <button
                  onClick={openRegenModal}
                  style={{
                    background: "white",
                    border: "1px solid #EF4444",
                    borderRadius: "8px",
                    padding: "10px 16px",
                    fontSize: "13px",
                    fontWeight: "500",
                    color: "#EF4444",
                    cursor: "pointer",
                  }}
                >
                  Regenerate SDK Key
                </button>
              </div>
            </div>

            {/* Workspace Info Card */}
            <div
              style={{
                background: "white",
                border: "1px solid #E5E7EB",
                borderRadius: "12px",
                padding: "24px",
              }}
            >
              <h3
                style={{
                  fontSize: "14px",
                  fontWeight: "600",
                  color: "#111318",
                  marginBottom: "16px",
                }}
              >
                Workspace Information
              </h3>

              {profileLoading ? (
                <Spinner />
              ) : profileError ? (
                <ErrorBox message={profileError} onRetry={() => window.location.reload()} />
              ) : profile ? (
                <div
                  style={{
                    display: "grid",
                    gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
                    gap: "16px",
                  }}
                >
                  {/* Workspace name */}
                  <div>
                    <label
                      style={{
                        fontSize: "11px",
                        fontWeight: "500",
                        color: "#9CA3AF",
                        textTransform: "uppercase",
                        letterSpacing: "0.5px",
                        display: "block",
                        marginBottom: "4px",
                      }}
                    >
                      Workspace
                    </label>
                    <p
                      style={{
                        fontSize: "14px",
                        color: "#111318",
                        margin: 0,
                      }}
                    >
                      {profile.shop_domain}
                    </p>
                  </div>

                  {/* Email */}
                  <div>
                    <label
                      style={{
                        fontSize: "11px",
                        fontWeight: "500",
                        color: "#9CA3AF",
                        textTransform: "uppercase",
                        letterSpacing: "0.5px",
                        display: "block",
                        marginBottom: "4px",
                      }}
                    >
                      Email
                    </label>
                    <p
                      style={{
                        fontSize: "14px",
                        color: "#111318",
                        margin: 0,
                      }}
                    >
                      {profile.email}
                    </p>
                  </div>

                  {/* Plan */}
                  <div>
                    <label
                      style={{
                        fontSize: "11px",
                        fontWeight: "500",
                        color: "#9CA3AF",
                        textTransform: "uppercase",
                        letterSpacing: "0.5px",
                        display: "block",
                        marginBottom: "4px",
                      }}
                    >
                      Plan
                    </label>
                    <Badge variant="success">{capitalizePlan(profile.plan)}</Badge>
                  </div>

                  {/* Member since */}
                  <div>
                    <label
                      style={{
                        fontSize: "11px",
                        fontWeight: "500",
                        color: "#9CA3AF",
                        textTransform: "uppercase",
                        letterSpacing: "0.5px",
                        display: "block",
                        marginBottom: "4px",
                      }}
                    >
                      Member Since
                    </label>
                    <p
                      style={{
                        fontSize: "14px",
                        color: "#111318",
                        margin: 0,
                      }}
                    >
                      {formatMonthYear(profile.created_at)}
                    </p>
                  </div>
                </div>
              ) : null}
            </div>
          </CardBody>
        </Card>

        {/* Account Details Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[hsl(var(--accent))]">
                <svg className="h-4 w-4 text-[hsl(var(--accent-foreground))]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
                </svg>
              </div>
              <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Account Details</h2>
            </div>
          </CardHeader>
          <CardBody>
            {profileLoading ? <Spinner /> : profileError ? (
              <ErrorBox message={profileError} onRetry={() => window.location.reload()} />
            ) : profile ? (
              <dl className="grid grid-cols-1 gap-5 text-[13px] sm:grid-cols-2 lg:grid-cols-3">
                <ProfileField label="Email" value={profile.email} />
                <ProfileField label="Shop Domain" value={profile.shop_domain} />
                <ProfileField label="Plan">
                  <Badge variant="success">{capitalizePlan(profile.plan)}</Badge>
                </ProfileField>
                <ProfileField label="Status">
                  <Badge variant={profile.is_active ? "success" : "destructive"}>
                    {profile.is_active ? "Active" : "Inactive"}
                  </Badge>
                </ProfileField>
                <ProfileField label="Joined" value={formatMonthYear(profile.created_at)} />
                <ProfileField label="Merchant ID">
                  <code className="rounded-lg bg-[hsl(var(--secondary))] px-2 py-1 font-mono text-[11px] text-[hsl(var(--muted-foreground))]">
                    {profile.id}
                  </code>
                </ProfileField>
              </dl>
            ) : null}
          </CardBody>
        </Card>        {/* Privacy Notice Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div
                className="flex h-9 w-9 items-center justify-center rounded-xl"
                style={{ background: "#FEF3C7" }}
              >
                <svg
                  className="h-4 w-4"
                  style={{ color: "#D97706" }}
                  fill="none"
                  viewBox="0 0 24 24"
                  strokeWidth={1.5}
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"
                  />
                </svg>
              </div>
              <div>
                <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Privacy Disclosure</h2>
                <p className="text-[11px] text-[hsl(var(--muted-foreground))]">Important legal requirement</p>
              </div>
            </div>
          </CardHeader>
          <CardBody>
            <div
              style={{
                background: "#FFFBEB",
                border: "1px solid #FCD34D",
                borderRadius: "12px",
                padding: "20px",
              }}
            >
              <h3
                style={{
                  fontSize: "14px",
                  fontWeight: "600",
                  color: "#92400E",
                  margin: "0 0 12px 0",
                }}
              >
                Update Your Privacy Policy
              </h3>
              <p
                style={{
                  fontSize: "13px",
                  color: "#78350F",
                  margin: "0 0 12px 0",
                  lineHeight: "1.6",
                }}
              >
                You are collecting behavioral data from your website visitors. Under GDPR, CCPA, and other
                privacy laws, you must disclose this tracking in your own privacy policy.
              </p>
              <div
                style={{
                  background: "white",
                  border: "1px solid #FDE68A",
                  borderRadius: "8px",
                  padding: "12px",
                }}
              >
                <p
                  style={{
                    fontSize: "12px",
                    color: "#92400E",
                    margin: 0,
                    fontStyle: "italic",
                  }}
                >
                  &ldquo;We use EmoraTest to analyze user behavior and emotions on our website. This includes
                  tracking clicks, scrolls, and mouse movements to improve your experience.&rdquo;
                </p>
              </div>
            </div>
          </CardBody>
        </Card>


      </div>

      {/* Regenerate SDK Key Modal */}
      {showRegenModal && (
        <>
          {/* Backdrop */}
          <div
            onClick={closeRegenModal}
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
              padding: "32px",
              width: "440px",
              maxWidth: "calc(100vw - 48px)",
              zIndex: 51,
              boxShadow: "0 20px 60px rgba(0, 0, 0, 0.15)",
            }}
          >
            {/* Warning icon */}
            <div
              style={{
                width: "48px",
                height: "48px",
                borderRadius: "50%",
                background: "#FEF2F2",
                color: "#EF4444",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                margin: "0 auto 16px auto",
                fontSize: "24px",
                fontWeight: "700",
              }}
            >
              !
            </div>

            {/* Title */}
            <h3
              style={{
                fontSize: "20px",
                fontWeight: "700",
                color: "#111318",
                textAlign: "center",
                margin: "0 0 8px 0",
              }}
            >
              Regenerate SDK Key?
            </h3>

            {/* Description */}
            <p
              style={{
                fontSize: "14px",
                color: "#6B7280",
                textAlign: "center",
                lineHeight: "1.6",
                margin: "0 0 24px 0",
              }}
            >
              Your current SDK key will stop working immediately. Any website using this key will lose tracking until you update the snippet with the new key.
            </p>

            {/* Buttons */}
            <div style={{ display: "flex", gap: "12px" }}>
              {/* Cancel button */}
              <button
                onClick={closeRegenModal}
                disabled={regenLoading}
                style={{
                  flex: 1,
                  background: "white",
                  border: "1.5px solid #E5E7EB",
                  color: "#374151",
                  borderRadius: "10px",
                  padding: "12px",
                  fontSize: "14px",
                  fontWeight: "500",
                  cursor: regenLoading ? "not-allowed" : "pointer",
                  opacity: regenLoading ? 0.6 : 1,
                }}
              >
                Cancel
              </button>

              {/* Confirm button */}
              <button
                onClick={confirmRegenerate}
                disabled={regenLoading}
                style={{
                  flex: 1,
                  background: "#EF4444",
                  color: "white",
                  border: "none",
                  borderRadius: "10px",
                  padding: "12px",
                  fontSize: "14px",
                  fontWeight: "600",
                  cursor: regenLoading ? "not-allowed" : "pointer",
                  opacity: regenLoading ? 0.7 : 1,
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: "8px",
                }}
              >
                {regenLoading ? (
                  <>
                    <svg
                      style={{ animation: "spin 1s linear infinite", width: "16px", height: "16px" }}
                      fill="none"
                      viewBox="0 0 24 24"
                    >
                      <circle
                        cx="12"
                        cy="12"
                        r="10"
                        stroke="currentColor"
                        strokeWidth="4"
                        strokeOpacity="0.25"
                      />
                      <path
                        fill="currentColor"
                        d="M4 12a8 8 0 018-8v8H4z"
                      />
                    </svg>
                    Regenerating...
                  </>
                ) : (
                  "Yes, Regenerate"
                )}
              </button>
            </div>
          </div>
        </>
      )}

      {/* Success Toast */}
      {regenSuccess && (
        <div
          style={{
            position: "fixed",
            bottom: "24px",
            right: "24px",
            background: "#10B981",
            color: "white",
            borderRadius: "10px",
            padding: "14px 20px",
            fontSize: "14px",
            fontWeight: "500",
            boxShadow: "0 4px 12px rgba(0, 0, 0, 0.15)",
            zIndex: 100,
            animation: "slideIn 0.3s ease-out",
          }}
        >
          SDK key regenerated successfully
        </div>
      )}

      {/* Add animations */}
      <style jsx>{`
        @keyframes spin {
          from { transform: rotate(0deg); }
          to { transform: rotate(360deg); }
        }
        @keyframes slideIn {
          from {
            transform: translateY(100%);
            opacity: 0;
          }
          to {
            transform: translateY(0);
            opacity: 1;
          }
        }
      `}</style>
    </>
  );
}

function ProfileField({ label, value, children }: { label: string; value?: string; children?: React.ReactNode }) {
  return (
    <div>
      <dt className="text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">{label}</dt>
      <dd className="mt-1.5 font-medium text-[hsl(var(--foreground))]">{children || value}</dd>
    </div>
  );
}
