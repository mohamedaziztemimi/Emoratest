"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@/lib/hooks";
import {
  fetchBandits,
  createBandit,
  updateBandit,
  deleteBandit,
  type Bandit,
  type CreateBanditPayload,
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
  { value: "paused", label: "Paused" },
  { value: "completed", label: "Completed" },
];

const VARIANT_COLORS = ["#007BFF", "#7C3AED", "#10B981", "#F59E0B"];

export default function BanditsPage() {
  const [statusFilter, setStatusFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [deleteModal, setDeleteModal] = useState<{ id: string; name: string } | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const fetcher = useCallback(() => fetchBandits(1, statusFilter || undefined), [statusFilter]);
  const { data, error, loading, refetch } = useQuery(fetcher, [statusFilter]);

  async function handleCreate(payload: CreateBanditPayload) {
    await createBandit(payload);
    setShowCreate(false);
    refetch();
  }

  async function handleToggleStatus(bandit: Bandit) {
    const newStatus = bandit.status === "active" ? "paused" : "active";
    await updateBandit(bandit.id, { status: newStatus });
    refetch();
  }

  async function handleDeleteConfirm() {
    if (!deleteModal) return;
    setDeleteLoading(true);
    try {
      await deleteBandit(deleteModal.id);
      setDeleteModal(null);
      refetch();
    } catch (err) {
      console.error(err);
    } finally {
      setDeleteLoading(false);
    }
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Multi-Armed Bandits</h1>
          <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">Automatically optimize variant allocation using Thompson Sampling</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl hover:-translate-y-0.5"
        >
          {showCreate ? "Cancel" : "Create Bandit"}
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
      {showCreate && <CreateBanditForm onSubmit={handleCreate} />}

      {/* Delete modal */}
      {deleteModal && (
        <DeleteModal
          isOpen={!!deleteModal}
          title="Delete Bandit?"
          description="This will permanently delete this bandit experiment. All arm statistics and convergence data will be lost."
          itemName={deleteModal.name}
          isLoading={deleteLoading}
          onCancel={() => setDeleteModal(null)}
          onConfirm={handleDeleteConfirm}
        />
      )}

      {/* Bandit list */}
      {loading ? (
        <Spinner />
      ) : error ? (
        <ErrorBox message={error} onRetry={refetch} />
      ) : !data || data.bandits.length === 0 ? (
        <EmptyState
          title="No bandits yet"
          description="Create a bandit experiment to start automatically optimizing your variants."
        />
      ) : (
        <div className="grid gap-4">
          {data.bandits.map((bandit) => (
            <BanditCard
              key={bandit.id}
              bandit={bandit}
              onToggleStatus={() => handleToggleStatus(bandit)}
              onDelete={() => setDeleteModal({ id: bandit.id, name: bandit.name })}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function BanditCard({
  bandit,
  onToggleStatus,
  onDelete,
}: {
  bandit: Bandit;
  onToggleStatus: () => void;
  onDelete: () => void;
}) {
  const statusColor =
    bandit.status === "active"
      ? "bg-green-100 text-green-700"
      : bandit.status === "paused"
        ? "bg-gray-100 text-gray-600"
        : "bg-blue-100 text-blue-700";

  return (
    <Card className="transition-all hover:shadow-sm">
      <CardBody>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2">
              <h3 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">{bandit.name}</h3>
              <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium capitalize ${statusColor}`}>
                {bandit.status}
              </span>
              {bandit.converged && (
                <span className="rounded-md px-2 py-0.5 text-[11px] font-medium bg-purple-100 text-purple-700">
                  Winner: {bandit.winner_variant_id}
                </span>
              )}
            </div>
            {bandit.description && (
              <p className="mt-1 text-[13px] text-[hsl(var(--muted-foreground))]">{bandit.description}</p>
            )}

            {/* Variants with conversion bars */}
            <div className="mt-4 space-y-2">
              {bandit.variants.map((variant, idx) => (
                <div key={variant.variant_id} className="flex items-center gap-3">
                  <span className="text-[12px] font-medium text-[hsl(var(--foreground))] w-24 truncate" title={variant.name}>
                    {variant.name}
                  </span>
                  <div className="h-2 flex-1 max-w-[200px] overflow-hidden rounded-full bg-[hsl(var(--secondary))]">
                    <div
                      className="h-full rounded-full transition-all duration-300"
                      style={{
                        width: `${variant.conversion_rate * 100}%`,
                        backgroundColor: VARIANT_COLORS[idx % VARIANT_COLORS.length],
                      }}
                    />
                  </div>
                  <span className="text-[11px] text-[hsl(var(--muted-foreground))] w-16 text-right">
                    {(variant.conversion_rate * 100).toFixed(1)}%
                  </span>
                  <span className="text-[11px] text-[hsl(var(--muted-foreground))] w-16 text-right">
                    {variant.trials} trials
                  </span>
                </div>
              ))}
            </div>

            {/* Meta info */}
            <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-[hsl(var(--muted-foreground))]">
              <span className="capitalize">{bandit.algorithm.replace("_", " ")}</span>
              <span>•</span>
              <span>{bandit.variants.length} variant{bandit.variants.length !== 1 ? "s" : ""}</span>
              <span>•</span>
              <span>{bandit.total_trials} total trials</span>
              <span>•</span>
              <span>{formatDate(bandit.created_at)}</span>
            </div>
          </div>

          {/* Actions */}
          <div className="flex flex-wrap gap-2">
            <button
              onClick={onToggleStatus}
              className={`rounded-xl border px-4 py-2 text-[12px] font-medium transition-all ${
                bandit.status === "active"
                  ? "border-yellow-300 text-yellow-700 hover:bg-yellow-50"
                  : "border-green-300 text-green-700 hover:bg-green-50"
              }`}
            >
              {bandit.status === "active" ? "Pause" : "Resume"}
            </button>
            <button
              onClick={onDelete}
              className="rounded-xl border border-[hsl(var(--border))] px-4 py-2 text-[12px] font-medium text-[hsl(var(--muted-foreground))] transition-all hover:bg-red-50 hover:text-red-600 hover:border-red-200"
            >
              Delete
            </button>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function CreateBanditForm({ onSubmit }: { onSubmit: (payload: CreateBanditPayload) => Promise<void> }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [variants, setVariants] = useState([
    { name: "Control", variant_id: "control" },
    { name: "Variant B", variant_id: "variant_b" },
  ]);

  function addVariant() {
    if (variants.length >= 4) return;
    setVariants([
      ...variants,
      { name: `Variant ${variants.length + 1}`, variant_id: `variant_${variants.length + 1}` },
    ]);
  }

  function removeVariant(index: number) {
    if (variants.length <= 2) return;
    setVariants(variants.filter((_, i) => i !== index));
  }

  function updateVariant(index: number, field: "name" | "variant_id", value: string) {
    const newVariants = [...variants];
    newVariants[index][field] = value;
    setVariants(newVariants);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    const fd = new FormData(e.currentTarget);
    try {
      await onSubmit({
        name: fd.get("name") as string,
        description: (fd.get("description") as string) || undefined,
        algorithm: (fd.get("algorithm") as CreateBanditPayload["algorithm"]) || "thompson_sampling",
        epsilon: parseFloat((fd.get("epsilon") as string) || "0.1"),
        exploration_factor: parseFloat((fd.get("exploration_factor") as string) || "2.0"),
        min_samples_per_arm: parseInt((fd.get("min_samples_per_arm") as string) || "100"),
        variants: variants.map((v) => ({
          name: v.name,
          variant_id: v.variant_id,
        })),
      });
    } catch (err) {
      if (err && typeof err === "object" && "detail" in err) {
        setError((err as any).detail);
      } else {
        setError(err instanceof Error ? err.message : "Failed to create bandit");
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

          {/* Name */}
          <label className="flex flex-col gap-1.5 text-[12px]">
            <span className="font-semibold text-[hsl(var(--muted-foreground))]">Bandit Name *</span>
            <input name="name" required maxLength={255} className={inputCls} placeholder="e.g. Button Color Test" />
          </label>

          {/* Description */}
          <label className="flex flex-col gap-1.5 text-[12px]">
            <span className="font-semibold text-[hsl(var(--muted-foreground))]">Description</span>
            <textarea name="description" rows={2} maxLength={2000} className={inputCls} placeholder="What are you testing?" />
          </label>

          {/* Algorithm */}
          <label className="flex flex-col gap-1.5 text-[12px]">
            <span className="font-semibold text-[hsl(var(--muted-foreground))]">Algorithm</span>
            <select name="algorithm" className={inputCls}>
              <option value="thompson_sampling">Thompson Sampling (recommended)</option>
              <option value="ucb1">UCB1</option>
              <option value="epsilon_greedy">ε-Greedy</option>
            </select>
          </label>

          {/* Variants */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <span className="text-[12px] font-semibold text-[hsl(var(--muted-foreground))]">Variants *</span>
              {variants.length < 4 && (
                <button
                  type="button"
                  onClick={addVariant}
                  className="text-[11px] font-medium text-[hsl(var(--primary))] hover:underline"
                >
                  + Add Variant
                </button>
              )}
            </div>
            <div className="space-y-2">
              {variants.map((variant, idx) => (
                <div key={idx} className="flex gap-2 items-center">
                  <input
                    required
                    value={variant.name}
                    onChange={(e) => updateVariant(idx, "name", e.target.value)}
                    className={`${inputCls} flex-1`}
                    placeholder="Variant name"
                  />
                  <input
                    required
                    value={variant.variant_id}
                    onChange={(e) => updateVariant(idx, "variant_id", e.target.value)}
                    className={`${inputCls} flex-1 font-mono text-[11px]`}
                    placeholder="variant_id"
                  />
                  {variants.length > 2 && (
                    <button
                      type="button"
                      onClick={() => removeVariant(idx)}
                      className="text-red-500 hover:text-red-700 px-2"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Advanced settings */}
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Epsilon (ε-greedy)</span>
              <input
                name="epsilon"
                type="number"
                min="0"
                max="1"
                step="0.01"
                defaultValue="0.1"
                className={inputCls}
              />
            </label>
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Exploration Factor (UCB1)</span>
              <input
                name="exploration_factor"
                type="number"
                min="0"
                step="0.1"
                defaultValue="2.0"
                className={inputCls}
              />
            </label>
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Min Samples per Arm</span>
              <input
                name="min_samples_per_arm"
                type="number"
                min="0"
                defaultValue="100"
                className={inputCls}
              />
            </label>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl disabled:opacity-50"
          >
            {submitting ? "Creating..." : "Create Bandit"}
          </button>
        </form>
      </CardBody>
    </Card>
  );
}
