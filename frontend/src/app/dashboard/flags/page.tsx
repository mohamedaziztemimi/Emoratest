"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@/lib/hooks";
import {
  fetchFlags, createFlag, updateFlag, toggleKillSwitch, updateRollout, deleteFlag, fetchFlagResults,
  type FeatureFlag,
  type FlagResultsResponse,
  type VariantResult,
} from "@/lib/api";
import { formatDate } from "@/lib/format";
import { Card, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import { DeleteModal } from "@/components/ui/DeleteModal";

const STATUS_TABS = [
  { value: "", label: "All" },
  { value: "active", label: "Active" },
  { value: "inactive", label: "Inactive" },
  { value: "archived", label: "Archived" },
];

export default function FeatureFlagsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [archiveModal, setArchiveModal] = useState<{ key: string; name: string } | null>(null);
  const [archiveLoading, setArchiveLoading] = useState(false);
  const fetcher = useCallback(() => fetchFlags(1, statusFilter || undefined), [statusFilter]);
  const { data, error, loading, refetch } = useQuery(fetcher, [statusFilter]);

  async function handleCreate(form: { key: string; name: string; description?: string }) {
    await createFlag(form);
    setShowCreate(false);
    refetch();
  }

  async function handleToggleStatus(flag: FeatureFlag) {
    const newStatus = flag.status === "active" ? "inactive" : "active";
    await updateFlag(flag.key, { status: newStatus });
    refetch();
  }

  async function handleKillSwitch(flag: FeatureFlag) {
    await toggleKillSwitch(flag.key, !flag.kill_switch);
    refetch();
  }

  async function handleRolloutChange(flag: FeatureFlag, percentage: number) {
    await updateRollout(flag.key, percentage);
    refetch();
  }

  async function handleArchiveConfirm() {
    if (!archiveModal) return;
    setArchiveLoading(true);
    try {
      await deleteFlag(archiveModal.key);
      setArchiveModal(null);
      refetch();
    } catch (err) {
      console.error(err);
    } finally {
      setArchiveLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Beta Banner */}
      <div className="rounded-xl border border-amber-200 bg-amber-50 px-4 py-3 text-[13px] text-amber-800">
        <strong>Early Beta:</strong> You can create experiment definitions, but SDK-side variant assignment is coming soon. Currently, experiments track emotion differences between page variants you set up manually.
      </div>

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">A/B Tests</h1>
          <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">Test different versions and see which converts better</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl hover:-translate-y-0.5"
        >
          {showCreate ? "Cancel" : "New Test"}
        </button>
      </div>

      {/* Status filter tabs */}
      <div className="flex gap-1 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-1 w-fit">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setStatusFilter(tab.value)}
            className={`rounded-lg px-4 py-1.5 text-[12px] font-medium transition-all ${
              statusFilter === tab.value
                ? "bg-[hsl(var(--primary))] text-white shadow-sm"
                : "text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Create form */}
      {showCreate && <CreateFlagForm onSubmit={handleCreate} />}

      {/* Archive modal */}
      {archiveModal && (
        <DeleteModal
          isOpen={!!archiveModal}
          title="Archive Test?"
          description="This will archive the A/B test. Archived tests are read-only and no longer evaluated."
          itemName={archiveModal.name}
          isLoading={archiveLoading}
          onCancel={() => setArchiveModal(null)}
          onConfirm={handleArchiveConfirm}
          confirmLabel="Archive"
        />
      )}

      {/* Flag list */}
      {loading ? (
        <Spinner />
      ) : error ? (
        <ErrorBox message={error} onRetry={refetch} />
      ) : !data || data.flags.length === 0 ? (
        <EmptyState title="No A/B tests" description="Create your first A/B test to start optimizing conversions." />
      ) : (
        <div className="grid gap-4">
          {data.flags.map((flag) => (
            <FlagCard
              key={flag.id}
              flag={flag}
              onToggleStatus={() => handleToggleStatus(flag)}
              onKillSwitch={() => handleKillSwitch(flag)}
              onRolloutChange={(pct) => handleRolloutChange(flag, pct)}
              onArchive={() => setArchiveModal({ key: flag.key, name: flag.name })}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function FlagCard({
  flag,
  onToggleStatus,
  onKillSwitch,
  onRolloutChange,
  onArchive,
}: {
  flag: FeatureFlag;
  onToggleStatus: () => void;
  onKillSwitch: () => void;
  onRolloutChange: (pct: number) => void;
  onArchive: () => void;
}) {
  const [expandedResults, setExpandedResults] = useState<string | null>(null);
  const hasVariants = flag.variants && flag.variants.length > 0;
  const isExpanded = expandedResults === flag.key;

  const statusColor =
    flag.kill_switch
      ? "bg-red-100 text-red-700"
      : flag.status === "active"
        ? "bg-green-100 text-green-700"
        : flag.status === "archived"
          ? "bg-gray-100 text-gray-500"
          : "bg-yellow-100 text-yellow-700";

  const statusLabel = flag.kill_switch ? "Killed" : flag.status;

  return (
    <Card className="transition-all hover:shadow-md">
      <CardBody>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">{flag.name}</h3>
              <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium capitalize ${statusColor}`}>
                {statusLabel}
              </span>
            </div>
            <p className="mt-0.5 text-[12px] font-mono text-[hsl(var(--muted-foreground))]">{flag.key}</p>
            {flag.description && (
              <p className="mt-1 text-[13px] text-[hsl(var(--muted-foreground))]">{flag.description}</p>
            )}

            {/* Rollout bar */}
            <div className="mt-3 flex items-center gap-3">
              <span className="text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Rollout</span>
              <div className="h-2 flex-1 max-w-[200px] overflow-hidden rounded-full bg-[hsl(var(--secondary))]">
                <div
                  className="h-full rounded-full bg-[hsl(var(--primary))] transition-all duration-300"
                  style={{ width: `${flag.rollout_percentage}%` }}
                />
              </div>
              <span className="text-[12px] font-semibold text-[hsl(var(--foreground))]">{flag.rollout_percentage}%</span>
            </div>

            {/* Meta info */}
            <div className="mt-2 flex flex-wrap items-center gap-3 text-[12px] text-[hsl(var(--muted-foreground))]">
              {flag.variants && flag.variants.length > 0 && (
                <span>{flag.variants.length} variant{flag.variants.length !== 1 ? "s" : ""}</span>
              )}
              {flag.targeting_rules && flag.targeting_rules.length > 0 && (
                <Badge variant="outline">{flag.targeting_rules.length} rule{flag.targeting_rules.length !== 1 ? "s" : ""}</Badge>
              )}
              <span>{formatDate(flag.created_at)}</span>
            </div>

            {/* A/B Test Results Section */}
            {hasVariants && (
              <div className="mt-4">
                <FlagResultsPanel flagKey={flag.key} />
              </div>
            )}
          </div>

          {/* Actions */}
          {flag.status !== "archived" && (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={onToggleStatus}
                className={`rounded-xl border px-4 py-2 text-[12px] font-medium transition-all ${
                  flag.status === "active"
                    ? "border-yellow-300 text-yellow-700 hover:bg-yellow-50"
                    : "border-green-300 text-green-700 hover:bg-green-50"
                }`}
              >
                {flag.status === "active" ? "Pause" : "Activate"}
              </button>
              <button
                onClick={onKillSwitch}
                className={`rounded-xl border px-4 py-2 text-[12px] font-medium transition-all ${
                  flag.kill_switch
                    ? "border-green-300 text-green-700 hover:bg-green-50"
                    : "border-red-300 text-red-700 hover:bg-red-50"
                }`}
              >
                {flag.kill_switch ? "Revive" : "Kill"}
              </button>
              <button
                onClick={onArchive}
                className="rounded-xl border border-[hsl(var(--border))] px-4 py-2 text-[12px] font-medium text-[hsl(var(--muted-foreground))] transition-all hover:bg-[hsl(var(--accent))]"
              >
                Archive
              </button>
            </div>
          )}
        </div>
      </CardBody>
    </Card>
  );
}

function FlagResultsPanel({ flagKey }: { flagKey: string }) {
  const [expandedResults, setExpandedResults] = useState<string | null>(null);
  const isExpanded = expandedResults === flagKey;
  const { data, loading } = useQuery<FlagResultsResponse>(
    () => fetchFlagResults(flagKey),
    [flagKey],
    `flag-results-${flagKey}`
  );

  const VARIANT_COLORS = ["#007BFF", "#7C3AED", "#10B981", "#F59E0B"];

  return (
    <>
      <button
        onClick={() => setExpandedResults(isExpanded ? null : flagKey)}
        className="text-[12px] font-semibold text-[hsl(var(--primary))] hover:underline"
      >
        {isExpanded ? "Hide" : "View"} Results
      </button>
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-100">
          {loading ? (
            <div className="py-3 text-sm text-gray-400">Loading results...</div>
          ) : data ? (
            <>
              <div className="flex items-center justify-between mb-3">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">A/B Test Results</p>
                <span className="text-xs text-gray-400">{data.total_exposures} visitors</span>
              </div>
              {data.total_exposures === 0 ? (
                <p className="text-sm text-gray-400 py-2">No visitors assigned yet. Waiting for SDK traffic.</p>
              ) : (
                <div className="space-y-3">
                  {data.variants.map((v, i) => {
                    const color = VARIANT_COLORS[i % VARIANT_COLORS.length];
                    const isWinner = data.winning_variant === v.variant;
                    const maxExposures = Math.max(...data.variants.map((x) => x.exposures), 1);
                    const barWidth = Math.max((v.exposures / maxExposures) * 100, 5);
                    return (
                      <div key={v.variant}>
                        <div className="flex items-center justify-between mb-1">
                          <div className="flex items-center gap-2">
                            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }} />
                            <span className="text-sm font-medium text-gray-700 capitalize">{v.variant.replace(/_/g, " ")}</span>
                            {isWinner && (
                              <span className="text-[10px] font-medium text-green-600 bg-green-50 px-1.5 py-0.5 rounded">Winner</span>
                            )}
                          </div>
                          <div className="flex items-center gap-3 text-xs">
                            <span className="text-gray-400">{v.exposures} visitors</span>
                            <span className="font-semibold text-gray-800">{v.conversion_rate.toFixed(1)}%</span>
                          </div>
                        </div>
                        <div className="w-full bg-gray-100 rounded-full h-2 overflow-hidden">
                          <div
                            className="h-full rounded-full transition-all duration-500"
                            style={{ width: `${barWidth}%`, backgroundColor: color }}
                          />
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
              {data.total_conversions === 0 && data.total_exposures > 0 && (
                <p className="text-xs text-gray-400 mt-3 pt-2 border-t border-gray-50">
                  No conversions tracked yet. Make sure your site calls EmoraTest.track(&quot;purchase&quot;) on conversion.
                </p>
              )}
            </>
          ) : null}
        </div>
      )}
    </>
  );
}

function CreateFlagForm({ onSubmit }: { onSubmit: (f: { key: string; name: string; description?: string }) => Promise<void> }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    const fd = new FormData(e.currentTarget);
    try {
      await onSubmit({
        key: fd.get("key") as string,
        name: fd.get("name") as string,
        description: (fd.get("description") as string) || undefined,
      });
    } catch (err) {
      if (err && typeof err === "object" && "detail" in err) {
        setError((err as any).detail);
      } else {
        setError(err instanceof Error ? err.message : "Failed to create flag");
      }
    } finally {
      setSubmitting(false);
    }
  }

  const inputCls = "rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-4 py-2.5 text-[13px] text-[hsl(var(--foreground))] outline-none transition-colors focus:border-[hsl(var(--ring))] focus:ring-2 focus:ring-[hsl(var(--ring)/0.2)]";

  return (
    <Card className="animate-scale-in">
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-600">
              {error}
            </div>
          )}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Test Key *</span>
              <input name="key" required maxLength={100} className={inputCls} placeholder="e.g. hero-headline-test" />
              <span className="text-[11px] text-[hsl(var(--muted-foreground))]">Only letters, numbers, hyphens, underscores</span>
            </label>
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Test Name *</span>
              <input name="name" required maxLength={255} className={inputCls} placeholder="e.g. Hero Headline Test" />
            </label>
          </div>
          <label className="flex flex-col gap-1.5 text-[12px]">
            <span className="font-semibold text-[hsl(var(--muted-foreground))]">Description</span>
            <textarea name="description" rows={2} maxLength={1000} className={inputCls} placeholder="What are you testing?" />
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl disabled:opacity-50"
          >
            {submitting ? "Creating..." : "Create Test"}
          </button>
        </form>
      </CardBody>
    </Card>
  );
}
