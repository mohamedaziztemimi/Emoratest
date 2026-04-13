"use client";

import { useCallback, useState } from "react";
import { useQuery } from "@/lib/hooks";
import { fetchMerchantProfile, rotateKey } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";

const profileFetcher = () => fetchMerchantProfile();

export default function SettingsPage() {
  const profile = useQuery(profileFetcher, [], "merchant-profile");
  const [sdkKey, setSdkKey] = useState(() =>
    typeof window !== "undefined" ? localStorage.getItem("emoratest_sdk_key") || "" : ""
  );
  const [saved, setSaved] = useState(false);
  const [rotating, setRotating] = useState(false);
  const [rotateResult, setRotateResult] = useState<string | null>(null);

  const handleSaveKey = useCallback(() => {
    localStorage.setItem("emoratest_sdk_key", sdkKey);
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  }, [sdkKey]);

  async function handleRotateKey() {
    if (!confirm("Rotate your SDK key? The old key will stop working immediately.")) return;
    setRotating(true);
    try {
      const res = await rotateKey();
      setSdkKey(res.new_sdk_key);
      localStorage.setItem("emoratest_sdk_key", res.new_sdk_key);
      setRotateResult(`Key rotated at ${res.rotated_at}. New key saved.`);
    } catch (err) {
      setRotateResult(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    } finally {
      setRotating(false);
    }
  }

  const inputCls = "rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-4 py-2.5 text-[13px] text-[hsl(var(--foreground))] outline-none transition-colors focus:border-[hsl(var(--ring))] focus:ring-2 focus:ring-[hsl(var(--ring)/0.2)]";

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Settings</h1>
        <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">
          Manage your SDK key and account details
        </p>
      </div>

      {/* SDK Key */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[hsl(var(--accent))]">
              <svg className="h-4 w-4 text-[hsl(var(--accent-foreground))]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-1 .43-1.563A6 6 0 1121.75 8.25z" />
              </svg>
            </div>
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">SDK Key</h2>
          </div>
        </CardHeader>
        <CardBody className="space-y-5">
          <div>
            <label className="block text-[12px] font-semibold text-[hsl(var(--muted-foreground))]">Current SDK Key</label>
            <div className="mt-2 flex gap-2">
              <input
                type="text"
                value={sdkKey}
                onChange={(e) => setSdkKey(e.target.value)}
                placeholder="Paste your SDK key here"
                className={`flex-1 font-mono ${inputCls}`}
              />
              <button
                onClick={handleSaveKey}
                className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl"
              >
                {saved ? "Saved!" : "Save"}
              </button>
            </div>
            <p className="mt-2 text-[11px] text-[hsl(var(--muted-foreground))]">
              Stored in browser localStorage. Sent as X-SDK-Key header with every API request.
            </p>
          </div>

          <div className="flex items-center gap-3 border-t border-[hsl(var(--border))] pt-5">
            <button
              onClick={handleRotateKey}
              disabled={rotating}
              className="rounded-xl border border-[hsl(var(--destructive)/0.3)] px-5 py-2.5 text-[13px] font-semibold text-[hsl(var(--destructive))] transition-all hover:bg-[hsl(var(--destructive)/0.06)] disabled:opacity-50"
            >
              {rotating ? "Rotating..." : "Rotate SDK Key"}
            </button>
            {rotateResult && (
              <p className="text-[12px] text-[hsl(var(--muted-foreground))]">{rotateResult}</p>
            )}
          </div>
        </CardBody>
      </Card>

      {/* Merchant Profile */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-[hsl(var(--accent))]">
              <svg className="h-4 w-4 text-[hsl(var(--accent-foreground))]" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z" />
              </svg>
            </div>
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Merchant Profile</h2>
          </div>
        </CardHeader>
        <CardBody>
          {profile.loading ? <Spinner /> : profile.error ? (
            <ErrorBox message={profile.error} onRetry={profile.refetch} />
          ) : profile.data ? (
            <dl className="grid grid-cols-1 gap-5 text-[13px] sm:grid-cols-2 lg:grid-cols-3">
              <ProfileField label="Email" value={profile.data.email} />
              <ProfileField label="Shop Domain" value={profile.data.shop_domain} />
              <ProfileField label="Plan">
                <Badge variant="success">{profile.data.plan}</Badge>
              </ProfileField>
              <ProfileField label="Status">
                <Badge variant={profile.data.is_active ? "success" : "destructive"}>
                  {profile.data.is_active ? "Active" : "Inactive"}
                </Badge>
              </ProfileField>
              <ProfileField label="Joined" value={formatDate(profile.data.created_at)} />
              <ProfileField label="Merchant ID">
                <code className="rounded-lg bg-[hsl(var(--secondary))] px-2 py-1 font-mono text-[11px] text-[hsl(var(--muted-foreground))]">
                  {profile.data.id}
                </code>
              </ProfileField>
            </dl>
          ) : null}
        </CardBody>
      </Card>
    </div>
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
