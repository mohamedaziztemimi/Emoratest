"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import { WaitlistModal } from "@/components/WaitlistModal";
import { API_BASE } from "@/lib/api";

interface MerchantProfile {
  id: string;
  email: string;
  shop_domain: string;
  plan: string;
  is_active: boolean;
  created_at: string;
}

interface UsageData {
  plan: string;
  sessions_used: number;
  sessions_limit: number;
  reset_date: string;
}

export default function SettingsPage() {
  // Profile state
  const [profile, setProfile] = useState<MerchantProfile | null>(null);
  const [profileLoading, setProfileLoading] = useState(true);
  const [profileError, setProfileError] = useState<string | null>(null);

  // Usage state
  const [usage, setUsage] = useState<UsageData | null>(null);
  const [usageLoading, setUsageLoading] = useState(true);
  const [usageError, setUsageError] = useState<string | null>(null);

  // SDK Key state
  const [sdkKey, setSdkKey] = useState("");
  const [sdkKeyMasked, setSdkKeyMasked] = useState(true);
  const [copied, setCopied] = useState(false);
  const [regenerating, setRegenerating] = useState(false);

  // Modal state
  const [showRegenModal, setShowRegenModal] = useState(false);
  const [regenLoading, setRegenLoading] = useState(false);
  const [regenSuccess, setRegenSuccess] = useState(false);
  const [showWaitlist, setShowWaitlist] = useState(false);

  // ML Model health state
  const [mlHealth, setMlHealth] = useState<{ model_loaded: boolean; using_fallback: boolean } | null>(null);

  const [error, setError] = useState<string | null>(null);

  // Auto-hide timer for revealed key (30 seconds)
  const revealTimerRef = useRef<NodeJS.Timeout | null>(null);

  // Fetch profile on mount
  useEffect(() => {
    const fetchProfile = async () => {
      setProfileLoading(true);
      setProfileError(null);

      try {
        const apiUrl = API_BASE;
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

  // Fetch usage on mount
  useEffect(() => {
    const fetchUsage = async () => {
      setUsageLoading(true);
      setUsageError(null);

      try {
        const apiUrl = API_BASE;
        const res = await fetch(`${apiUrl}/api/v1/auth/usage`, {
          credentials: "include",
        });

        if (!res.ok) {
          throw new Error("Failed to fetch usage");
        }

        const data = await res.json();
        setUsage(data);
      } catch (err) {
        setUsageError(err instanceof Error ? err.message : "Failed to load usage");
      } finally {
        setUsageLoading(false);
      }
    };

    fetchUsage();
  }, []);

  // Fetch ML model health on mount
  useEffect(() => {
    const fetchMlHealth = async () => {
      try {
        const apiUrl = API_BASE;
        const res = await fetch(`${apiUrl}/api/v1/health/ml`, {
          credentials: "include",
        });
        if (res.ok) {
          const data = await res.json();
          setMlHealth(data);
        }
      } catch (err) {
        // Silently fail - this is optional monitoring
        console.error("Failed to fetch ML health:", err);
      }
    };
    fetchMlHealth();
  }, []);

  // Clear timer on unmount
  useEffect(() => {
    return () => {
      if (revealTimerRef.current) {
        clearTimeout(revealTimerRef.current);
      }
    };
  }, []);

  // Reveal SDK key - NOTE: SDK keys are stored as hashes only, so we cannot retrieve the original key.
  // This function is now removed because calling onboarding-complete would generate a NEW key each time.
  // Users should use "Regenerate" to get a new key instead.

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

  // Confirm regenerate SDK key - uses the correct rotate-key endpoint
  const confirmRegenerate = useCallback(async () => {
    setRegenLoading(true);
    setError(null);

    try {
      const apiUrl = API_BASE;
      const res = await fetch(`${apiUrl}/api/v1/merchants/rotate-key`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
      });

      if (!res.ok) {
        throw new Error("Failed to regenerate SDK key");
      }

      const data = await res.json();
      if (data.new_sdk_key) {
        setSdkKey(data.new_sdk_key);
        // Store to localStorage for docs page access
        localStorage.setItem("emoratest_sdk_key", data.new_sdk_key);
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
          localStorage.removeItem("emoratest_sdk_key");
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

        {/* ML Model Health Warning */}
        {mlHealth?.using_fallback === true && (
          <div
            style={{
              background: "#FEF3C7",
              border: "1px solid #F59E0B",
              borderRadius: "12px",
              padding: "16px",
              display: "flex",
              gap: "12px",
              alignItems: "flex-start",
            }}
          >
            <svg
              style={{ width: "20px", height: "20px", color: "#D97706", flexShrink: 0, marginTop: "2px" }}
              fill="none"
              viewBox="0 0 24 24"
              strokeWidth={2}
              stroke="currentColor"
            >
              <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z" />
            </svg>
            <div>
              <p style={{ fontSize: "14px", fontWeight: "600", color: "#92400E", margin: "0 0 4px 0" }}>
                ML Model Not Loaded
              </p>
              <p style={{ fontSize: "13px", color: "#B45309", margin: 0 }}>
                Predictions are using simplified heuristics instead of the trained XGBoost model. This may reduce accuracy. Contact support if this issue persists.
              </p>
            </div>
          </div>
        )}

        {/* Usage Section */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3">
              <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[hsl(var(--accent))]">
                <svg className="h-4 w-4 text-[hsl(var(--accent-foreground))]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 3v11.25A2.25 2.25 0 006 16.5h2.25M3.75 3h-1.5m1.5 0h16.5m0 0h1.5m-1.5 0v11.25A2.25 2.25 0 0118 16.5h-2.25m-7.5 0h7.5m-7.5 0l-1 3m8.5-3l1 3m0 0l.5 1.5m-.5-1.5h-9.5m0 0l-.5 1.5m.75-9l3-3 2.148 2.148A12.061 12.061 0 0116.5 7.605c0 2.526-1.11 4.898-3 6.5" />
                </svg>
              </div>
              <div>
                <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Usage</h2>
                <p className="text-[11px] text-[hsl(var(--muted-foreground))]">
                  Your monthly session usage and limits
                </p>
              </div>
            </div>
          </CardHeader>
          <CardBody>
            {usageLoading ? (
              <Spinner />
            ) : usageError ? (
              <ErrorBox message={usageError} onRetry={() => window.location.reload()} />
            ) : usage ? (
              <div
                style={{
                  background: "white",
                  border: "1px solid #E5E7EB",
                  borderRadius: "12px",
                  padding: "24px",
                }}
              >
                {/* Plan Badge */}
                <div style={{ marginBottom: "20px" }}>
                  <Badge variant="success">
                    {usage.plan === "free" ? "Free Beta" : capitalizePlan(usage.plan)}
                  </Badge>
                </div>

                {/* Session Usage Bar */}
                <div style={{ marginBottom: "16px" }}>
                  <div
                    style={{
                      display: "flex",
                      justifyContent: "space-between",
                      alignItems: "center",
                      marginBottom: "8px",
                    }}
                  >
                    <span
                      style={{
                        fontSize: "14px",
                        fontWeight: "500",
                        color: "#111318",
                      }}
                    >
                      {usage.sessions_used} / {usage.sessions_limit} sessions this month
                    </span>
                    <span
                      style={{
                        fontSize: "12px",
                        color: "#6B7280",
                      }}
                    >
                      {Math.round((usage.sessions_used / usage.sessions_limit) * 100)}%
                    </span>
                  </div>

                  {/* Progress Bar */}
                  <div
                    style={{
                      width: "100%",
                      height: "8px",
                      background: "#E5E7EB",
                      borderRadius: "4px",
                      overflow: "hidden",
                    }}
                  >
                    <div
                      style={{
                        height: "100%",
                        width: `${Math.min((usage.sessions_used / usage.sessions_limit) * 100, 100)}%`,
                        background:
                          usage.sessions_used >= usage.sessions_limit
                            ? "#EF4444"
                            : usage.sessions_used >= usage.sessions_limit * 0.8
                            ? "#F59E0B"
                            : "#007BFF",
                        borderRadius: "4px",
                        transition: "width 0.3s ease",
                      }}
                    />
                  </div>

                  {/* Limit Reached Message */}
                  {usage.sessions_used >= usage.sessions_limit && (
                    <p
                      style={{
                        fontSize: "12px",
                        color: "#EF4444",
                        marginTop: "8px",
                        fontWeight: "500",
                      }}
                    >
                      Limit reached. New sessions are not being tracked.
                    </p>
                  )}
                </div>

                {/* Reset Date */}
                <p
                  style={{
                    fontSize: "12px",
                    color: "#6B7280",
                    marginBottom: "16px",
                  }}
                >
                  Resets on {new Date(usage.reset_date).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
                </p>

                {/* Need More Sessions Link */}
                <button
                  onClick={() => setShowWaitlist(true)}
                  style={{
                    fontSize: "13px",
                    color: "#007BFF",
                    textDecoration: "none",
                    fontWeight: "500",
                    background: "none",
                    border: "none",
                    padding: 0,
                    cursor: "pointer",
                  }}
                >
                  Need more sessions? →
                </button>
              </div>
            ) : null}
          </CardBody>
        </Card>

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

                {/* Hide button - only shown when revealed */}
                {!sdkKeyMasked && (
                  <button
                    onClick={() => {
                      setSdkKeyMasked(true);
                      setSdkKey("");
                      localStorage.removeItem("emoratest_sdk_key");
                    }}
                    style={{
                      background: "white",
                      border: "1px solid #E5E7EB",
                      borderRadius: "8px",
                      padding: "10px 16px",
                      fontSize: "13px",
                      fontWeight: "500",
                      color: "#374151",
                      cursor: "pointer",
                    }}
                  >
                    Hide
                  </button>
                )}
              </div>

              {/* Regenerate button */}
              <div style={{ marginTop: "16px" }}>
                <button
                  onClick={openRegenModal}
                  disabled={regenerating}
                  style={{
                    background: "white",
                    border: "1px solid #EF4444",
                    borderRadius: "8px",
                    padding: "10px 16px",
                    fontSize: "13px",
                    fontWeight: "500",
                    color: "#EF4444",
                    cursor: regenerating ? "not-allowed" : "pointer",
                    opacity: regenerating ? 0.6 : 1,
                  }}
                >
                  {regenerating ? "Generating..." : "Regenerate SDK Key"}
                </button>
                <p
                  style={{
                    fontSize: "11px",
                    color: "#9CA3AF",
                    margin: "8px 0 0 0",
                  }}
                >
                  Generates a new SDK key and invalidates the old one. Your existing integration will stop working until updated.
                </p>
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

      {/* Waitlist Modal */}
      <WaitlistModal
        isOpen={showWaitlist}
        onClose={() => setShowWaitlist(false)}
        prefillEmail={profile?.email}
      />

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
