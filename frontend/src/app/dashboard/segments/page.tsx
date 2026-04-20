"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@/lib/hooks";
import { fetchSegments, createSegment, updateSegment, deleteSegment, type Segment } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { Card, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import { DeleteModal } from "@/components/ui/DeleteModal";

const TYPE_TABS = [
  { value: "", label: "All" },
  { value: "static", label: "Static" },
  { value: "dynamic", label: "Dynamic" },
  { value: "emotional", label: "Emotional" },
];

const TYPE_COLORS: Record<string, string> = {
  static: "bg-blue-100 text-blue-700",
  dynamic: "bg-purple-100 text-purple-700",
  emotional: "bg-pink-100 text-pink-700",
};

export default function SegmentsPage() {
  const [typeFilter, setTypeFilter] = useState("");
  const [showCreate, setShowCreate] = useState(false);
  const [deleteModal, setDeleteModal] = useState<{ id: string; name: string } | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const fetcher = useCallback(() => fetchSegments(1, typeFilter || undefined), [typeFilter]);
  const { data, error, loading, refetch } = useQuery(fetcher, [typeFilter]);

  async function handleCreate(form: { name: string; description?: string; segment_type?: string }) {
    await createSegment(form);
    setShowCreate(false);
    refetch();
  }

  async function handleToggleActive(seg: Segment) {
    await updateSegment(seg.id, { is_active: !seg.is_active });
    refetch();
  }

  async function handleDeleteConfirm() {
    if (!deleteModal) return;
    setDeleteLoading(true);
    try {
      await deleteSegment(deleteModal.id);
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
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Segments</h1>
          <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">Group users by behavior, emotions, and attributes for targeted experiments</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl hover:-translate-y-0.5"
        >
          {showCreate ? "Cancel" : "New Segment"}
        </button>
      </div>

      <div className="flex gap-1 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-1 w-fit">
        {TYPE_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => setTypeFilter(tab.value)}
            className={`rounded-lg px-4 py-1.5 text-[12px] font-medium transition-all ${
              typeFilter === tab.value
                ? "bg-[hsl(var(--primary))] text-white shadow-sm"
                : "text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {showCreate && <CreateSegmentForm onSubmit={handleCreate} />}

      {deleteModal && (
        <DeleteModal
          isOpen={!!deleteModal}
          title="Delete Segment?"
          description="This will permanently delete this segment. This action cannot be undone."
          itemName={deleteModal.name}
          isLoading={deleteLoading}
          onCancel={() => setDeleteModal(null)}
          onConfirm={handleDeleteConfirm}
        />
      )}

      {loading ? (
        <Spinner />
      ) : error ? (
        <ErrorBox message={error} onRetry={refetch} />
      ) : !data || data.segments.length === 0 ? (
        <EmptyState title="No segments" description="Create your first segment to group users by behavior and emotions." />
      ) : (
        <div className="grid gap-4">
          {data.segments.map((seg) => (
            <SegmentCard
              key={seg.id}
              segment={seg}
              onToggleActive={() => handleToggleActive(seg)}
              onDelete={() => setDeleteModal({ id: seg.id, name: seg.name })}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function SegmentCard({
  segment: seg,
  onToggleActive,
  onDelete,
}: {
  segment: Segment;
  onToggleActive: () => void;
  onDelete: () => void;
}) {
  const typeColor = TYPE_COLORS[seg.segment_type] || "bg-gray-100 text-gray-700";
  const conditionCount = seg.conditions?.conditions?.length || 0;

  return (
    <Card className="transition-all hover:shadow-md">
      <CardBody>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <h3 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">{seg.name}</h3>
              <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium capitalize ${typeColor}`}>
                {seg.segment_type}
              </span>
              <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${
                seg.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
              }`}>
                {seg.is_active ? "Active" : "Inactive"}
              </span>
            </div>
            {seg.description && (
              <p className="mt-1 text-[13px] text-[hsl(var(--muted-foreground))]">{seg.description}</p>
            )}
            <div className="mt-2 flex flex-wrap items-center gap-3 text-[12px] text-[hsl(var(--muted-foreground))]">
              {conditionCount > 0 && (
                <Badge variant="outline">{conditionCount} condition{conditionCount !== 1 ? "s" : ""}</Badge>
              )}
              {seg.estimated_size != null && (
                <span>{seg.estimated_size.toLocaleString()} users</span>
              )}
              {seg.created_at && <span>{formatDate(seg.created_at)}</span>}
            </div>
          </div>
          <div className="flex gap-2">
            <button
              onClick={onToggleActive}
              className={`rounded-xl border px-4 py-2 text-[12px] font-medium transition-all ${
                seg.is_active
                  ? "border-yellow-300 text-yellow-700 hover:bg-yellow-50"
                  : "border-green-300 text-green-700 hover:bg-green-50"
              }`}
            >
              {seg.is_active ? "Pause" : "Activate"}
            </button>
            <button
              onClick={onDelete}
              className="rounded-xl border border-[hsl(var(--destructive)/0.3)] px-4 py-2 text-[12px] font-medium text-[hsl(var(--destructive))] transition-all hover:bg-[hsl(var(--destructive)/0.06)]"
            >
              Delete
            </button>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

function CreateSegmentForm({ onSubmit }: { onSubmit: (f: { name: string; description?: string; segment_type?: string }) => Promise<void> }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    const fd = new FormData(e.currentTarget);
    try {
      await onSubmit({
        name: fd.get("name") as string,
        description: (fd.get("description") as string) || undefined,
        segment_type: (fd.get("segment_type") as string) || "static",
      });
    } catch (err) {
      if (err && typeof err === "object" && "detail" in err) {
        setError((err as any).detail);
      } else {
        setError(err instanceof Error ? err.message : "Failed to create segment");
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
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Segment Name *</span>
              <input name="name" required maxLength={255} className={inputCls} placeholder="e.g. Frustrated Mobile Users" />
            </label>
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Type</span>
              <select name="segment_type" className={inputCls}>
                <option value="static">Static</option>
                <option value="dynamic">Dynamic</option>
                <option value="emotional">Emotional</option>
              </select>
            </label>
          </div>
          <label className="flex flex-col gap-1.5 text-[12px]">
            <span className="font-semibold text-[hsl(var(--muted-foreground))]">Description</span>
            <textarea name="description" rows={2} maxLength={2000} className={inputCls} placeholder="Who does this segment target?" />
          </label>
          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl disabled:opacity-50"
          >
            {submitting ? "Creating..." : "Create Segment"}
          </button>
        </form>
      </CardBody>
    </Card>
  );
}
