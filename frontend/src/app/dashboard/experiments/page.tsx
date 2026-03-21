"use client";

import { useState } from "react";
import { useQuery } from "@/lib/hooks";
import {
  fetchExperiments, createExperiment, deleteExperiment, fetchExperimentStats,
  type Experiment, type ExperimentStats,
} from "@/lib/api";
import { formatPercent, formatDate, formatNumber } from "@/lib/format";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";

export default function ExperimentsPage() {
  const [page, setPage] = useState(1);
  const { data, error, loading, refetch } = useQuery(() => fetchExperiments(page), [page]);
  const [showCreate, setShowCreate] = useState(false);
  const [selectedStats, setSelectedStats] = useState<ExperimentStats | null>(null);
  const [statsLoading, setStatsLoading] = useState(false);

  async function handleCreate(form: {
    title: string; hypothesis?: string; friction_type?: string; variant_a?: string; variant_b?: string;
  }) {
    await createExperiment(form);
    setShowCreate(false);
    refetch();
  }

  async function handleDelete(id: string) {
    if (!confirm("Delete this experiment?")) return;
    await deleteExperiment(id);
    refetch();
  }

  async function handleViewStats(id: string) {
    setStatsLoading(true);
    try {
      setSelectedStats(await fetchExperimentStats(id));
    } catch {
      setSelectedStats(null);
    } finally {
      setStatsLoading(false);
    }
  }

  const totalPages = data ? Math.ceil(data.total / 20) : 0;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Experiments</h1>
          <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">Manage A/B experiments and view results</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl hover:-translate-y-0.5"
        >
          {showCreate ? "Cancel" : "New Experiment"}
        </button>
      </div>

      {showCreate && <CreateForm onSubmit={handleCreate} />}
      {selectedStats && <StatsPanel stats={selectedStats} onClose={() => setSelectedStats(null)} />}
      {statsLoading && <Spinner />}

      {loading ? <Spinner /> : error ? (
        <ErrorBox message={error} onRetry={refetch} />
      ) : !data || data.experiments.length === 0 ? (
        <EmptyState title="No experiments yet" description="Create your first A/B experiment to get started." />
      ) : (
        <>
          <div className="grid gap-4">
            {data.experiments.map((exp) => (
              <ExperimentCard key={exp.id} experiment={exp} onDelete={() => handleDelete(exp.id)} onViewStats={() => handleViewStats(exp.id)} />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="flex justify-center gap-2">
              <PgBtn disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>Previous</PgBtn>
              <span className="flex items-center px-3 text-[12px] text-[hsl(var(--muted-foreground))]">Page {page} of {totalPages}</span>
              <PgBtn disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>Next</PgBtn>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function ExperimentCard({ experiment: exp, onDelete, onViewStats }: { experiment: Experiment; onDelete: () => void; onViewStats: () => void }) {
  const resultVariant = exp.result === "winner_b" ? "success" : exp.result === "winner_a" ? "success" : exp.result === "no_significant_difference" ? "warning" : "default";

  return (
    <Card className="animate-slide-in">
      <CardBody>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex-1">
            <h3 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">{exp.title}</h3>
            {exp.hypothesis && <p className="mt-1 text-[13px] text-[hsl(var(--muted-foreground))]">{exp.hypothesis}</p>}
            <div className="mt-3 flex flex-wrap items-center gap-2">
              {exp.friction_type && <Badge variant="outline">{exp.friction_type}</Badge>}
              {exp.result && <Badge variant={resultVariant}>{exp.result}</Badge>}
              {exp.conversion_delta != null && (
                <span className="text-[12px] text-[hsl(var(--muted-foreground))]">Delta: {formatPercent(exp.conversion_delta)}</span>
              )}
              {exp.sample_size != null && (
                <span className="text-[12px] text-[hsl(var(--muted-foreground))]">n={formatNumber(exp.sample_size)}</span>
              )}
              <span className="text-[12px] text-[hsl(var(--muted-foreground))]">{formatDate(exp.created_at)}</span>
            </div>
            {exp.variant_a && (
              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="rounded-xl bg-[hsl(var(--primary)/0.06)] p-3 text-[12px]">
                  <span className="font-semibold text-[hsl(var(--primary))]">A:</span>{" "}
                  <span className="text-[hsl(var(--foreground))]">{exp.variant_a}</span>
                </div>
                {exp.variant_b && (
                  <div className="rounded-xl bg-[hsl(var(--success)/0.06)] p-3 text-[12px]">
                    <span className="font-semibold text-[hsl(var(--success))]">B:</span>{" "}
                    <span className="text-[hsl(var(--foreground))]">{exp.variant_b}</span>
                  </div>
                )}
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <button onClick={onViewStats} className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] px-4 py-2 text-[12px] font-medium text-[hsl(var(--foreground))] transition-all hover:bg-[hsl(var(--accent))]">
              Stats
            </button>
            <button onClick={onDelete} className="rounded-xl border border-[hsl(var(--destructive)/0.3)] px-4 py-2 text-[12px] font-medium text-[hsl(var(--destructive))] transition-all hover:bg-[hsl(var(--destructive)/0.06)]">
              Delete
            </button>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function StatsPanel({ stats, onClose }: { stats: ExperimentStats; onClose: () => void }) {
  return (
    <Card className="animate-scale-in border-[hsl(var(--primary)/0.3)] bg-gradient-to-br from-[hsl(var(--primary)/0.04)] to-[hsl(var(--primary)/0.08)]">
      <CardBody>
        <div className="flex items-start justify-between">
          <h3 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">{stats.title} - Statistics</h3>
          <button onClick={onClose} className="text-[12px] font-medium text-[hsl(var(--primary))] hover:underline">Close</button>
        </div>
        <dl className="mt-4 grid grid-cols-2 gap-4 text-[13px] sm:grid-cols-4">
          <StatItem label="Conv. Delta" value={formatPercent(stats.conversion_delta)} />
          <StatItem label="p-value" value={stats.p_value?.toFixed(4) ?? "--"} />
          <StatItem label="Significant?" value={stats.is_significant ? "Yes" : "No"} />
          <StatItem label="Power" value={stats.power?.toFixed(2) ?? "--"} />
        </dl>
        <p className="mt-4 rounded-xl bg-[hsl(var(--card))] p-4 text-[13px] text-[hsl(var(--muted-foreground))]">{stats.recommendation}</p>
      </CardBody>
    </Card>
  );
}

function StatItem({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <dt className="text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">{label}</dt>
      <dd className="mt-1 text-[18px] font-bold text-[hsl(var(--foreground))]">{value}</dd>
    </div>
  );
}

function CreateForm({ onSubmit }: { onSubmit: (f: { title: string; hypothesis?: string; friction_type?: string; variant_a?: string; variant_b?: string }) => Promise<void> }) {
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    const fd = new FormData(e.currentTarget);
    try {
      await onSubmit({
        title: fd.get("title") as string,
        hypothesis: (fd.get("hypothesis") as string) || undefined,
        friction_type: (fd.get("friction_type") as string) || undefined,
        variant_a: (fd.get("variant_a") as string) || undefined,
        variant_b: (fd.get("variant_b") as string) || undefined,
      });
    } finally {
      setSubmitting(false);
    }
  }

  const inputCls = "rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-4 py-2.5 text-[13px] text-[hsl(var(--foreground))] outline-none transition-colors focus:border-[hsl(var(--ring))] focus:ring-2 focus:ring-[hsl(var(--ring)/0.2)]";

  return (
    <Card className="animate-scale-in">
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Title *</span>
              <input name="title" required maxLength={200} className={inputCls} placeholder="e.g. Exit intent popup test" />
            </label>
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Friction Type</span>
              <input name="friction_type" maxLength={100} className={inputCls} placeholder="e.g. checkout_hesitation" />
            </label>
          </div>
          <label className="flex flex-col gap-1.5 text-[12px]">
            <span className="font-semibold text-[hsl(var(--muted-foreground))]">Hypothesis</span>
            <textarea name="hypothesis" rows={2} maxLength={1000} className={inputCls} placeholder="Describe your hypothesis..." />
          </label>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Variant A</span>
              <input name="variant_a" maxLength={200} className={inputCls} placeholder="Control" />
            </label>
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Variant B</span>
              <input name="variant_b" maxLength={200} className={inputCls} placeholder="Treatment" />
            </label>
          </div>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl disabled:opacity-50"
          >
            {submitting ? "Creating..." : "Create Experiment"}
          </button>
        </form>
      </CardBody>
    </Card>
  );
}

function PgBtn({ children, disabled, onClick }: { children: React.ReactNode; disabled: boolean; onClick: () => void }) {
  return (
    <button disabled={disabled} onClick={onClick} className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] px-4 py-1.5 text-[12px] font-medium text-[hsl(var(--foreground))] transition-all hover:bg-[hsl(var(--accent))] disabled:opacity-40 disabled:cursor-not-allowed">
      {children}
    </button>
  );
}
