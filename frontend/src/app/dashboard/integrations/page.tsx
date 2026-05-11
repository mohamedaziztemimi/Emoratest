"use client";

import { useState, useCallback } from "react";
import { useQuery } from "@/lib/hooks";
import { fetchIntegrations, createIntegration, deleteIntegration, type Integration } from "@/lib/api";
import { formatDate } from "@/lib/format";
import { Card, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import { DeleteModal } from "@/components/ui/DeleteModal";

// Integrations that are fully working
const AVAILABLE_INTEGRATIONS = [
  { value: "slack", label: "Slack", icon: "💬", desc: "Get emotion alerts in Slack channels" },
  { value: "webhook", label: "Webhook", icon: "🔗", desc: "Send events to any URL endpoint" },
  { value: "zapier", label: "Zapier", icon: "⚡", desc: "Connect to 5000+ apps via Zapier" },
  { value: "jira", label: "Jira", icon: "📋", desc: "Create tickets from frustration alerts" },
];

// Integrations coming soon
const COMING_SOON_INTEGRATIONS = [
  { value: "amplitude", label: "Amplitude", icon: "📊", desc: "Sync emotion data to Amplitude" },
  { value: "posthog", label: "PostHog", icon: "🦔", desc: "Send emotion events to PostHog" },
  { value: "snowflake", label: "Snowflake", icon: "❄️", desc: "Export data to Snowflake warehouse" },
  { value: "bigquery", label: "BigQuery", icon: "🔍", desc: "Stream events to Google BigQuery" },
];

const ALL_TYPE_OPTIONS = [...AVAILABLE_INTEGRATIONS, ...COMING_SOON_INTEGRATIONS];

const TYPE_COLORS: Record<string, string> = {
  slack: "bg-purple-100 text-purple-700",
  webhook: "bg-blue-100 text-blue-700",
  zapier: "bg-orange-100 text-orange-700",
  jira: "bg-indigo-100 text-indigo-700",
  amplitude: "bg-cyan-100 text-cyan-700",
  posthog: "bg-yellow-100 text-yellow-700",
  snowflake: "bg-sky-100 text-sky-700",
  bigquery: "bg-green-100 text-green-700",
};

const COMING_SOON_TYPES = new Set(COMING_SOON_INTEGRATIONS.map((t) => t.value));

const EVENT_OPTIONS = [
  { value: "session.end", label: "Session End" },
  { value: "emotion.frustrated", label: "Frustrated Detected" },
  { value: "emotion.confused", label: "Confused Detected" },
  { value: "emotion.engaged", label: "Engaged Detected" },
  { value: "experiment.completed", label: "Experiment Completed" },
  { value: "flag.evaluated", label: "Flag Evaluated" },
];

export default function IntegrationsPage() {
  const [showCreate, setShowCreate] = useState(false);
  const [deleteModal, setDeleteModal] = useState<{ id: string; name: string } | null>(null);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [notifyEmail, setNotifyEmail] = useState("");
  const [notifySuccess, setNotifySuccess] = useState(false);
  const fetcher = useCallback(() => fetchIntegrations(), []);
  const { data, error, loading, refetch } = useQuery(fetcher, []);

  async function handleCreate(form: { name: string; integration_type: string; config: Record<string, any>; events: string[] }) {
    await createIntegration(form);
    setShowCreate(false);
    refetch();
  }

  async function handleDeleteConfirm() {
    if (!deleteModal) return;
    setDeleteLoading(true);
    try {
      await deleteIntegration(deleteModal.id);
      setDeleteModal(null);
      refetch();
    } catch (err) {
      console.error(err);
    } finally {
      setDeleteLoading(false);
    }
  }

  async function handleNotifyMe(email: string) {
    // In a real implementation, this would call an API to save the email
    // For now, just show success message
    setNotifyEmail(email);
    setNotifySuccess(true);
    setTimeout(() => setNotifySuccess(false), 3000);
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Integrations</h1>
          <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">Connect EmoraTest to your favorite tools and data pipelines</p>
        </div>
        <button
          onClick={() => setShowCreate(!showCreate)}
          className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl hover:-translate-y-0.5"
        >
          {showCreate ? "Cancel" : "Add Integration"}
        </button>
      </div>

      {deleteModal && (
        <DeleteModal
          isOpen={!!deleteModal}
          title="Remove Integration?"
          description="This will disconnect the integration and stop sending events. This action cannot be undone."
          itemName={deleteModal.name}
          isLoading={deleteLoading}
          onCancel={() => setDeleteModal(null)}
          onConfirm={handleDeleteConfirm}
        />
      )}

      {showCreate && <CreateIntegrationForm onSubmit={handleCreate} />}

      {loading ? (
        <Spinner />
      ) : error ? (
        <ErrorBox message={error} onRetry={refetch} />
      ) : !data || data.integrations.length === 0 ? (
        <div className="space-y-6">
          <EmptyState title="No integrations" description="Connect your first tool to start syncing emotion data." />

          {/* Available Now */}
          <div>
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))] mb-2">Available Now</h2>
            <p className="text-[13px] text-[hsl(var(--muted-foreground))] mb-4">Fully functional integrations ready to connect</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {AVAILABLE_INTEGRATIONS.map((t) => (
                <button
                  key={t.value}
                  onClick={() => setShowCreate(true)}
                  className="flex flex-col items-start gap-2 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-4 text-left transition-all hover:shadow-md hover:-translate-y-0.5"
                >
                  <span className="text-2xl">{t.icon}</span>
                  <span className="text-[13px] font-semibold text-[hsl(var(--foreground))]">{t.label}</span>
                  <span className="text-[11px] text-[hsl(var(--muted-foreground))]">{t.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Coming Soon */}
          <div>
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))] mb-2">Coming Soon</h2>
            <p className="text-[13px] text-[hsl(var(--muted-foreground))] mb-4">We're working on these integrations. Get notified when they're ready.</p>
            <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
              {COMING_SOON_INTEGRATIONS.map((t) => (
                <div
                  key={t.value}
                  className="flex flex-col items-start gap-2 rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--muted))]/30 p-4 text-left opacity-75"
                >
                  <div className="flex items-center justify-between w-full">
                    <span className="text-2xl">{t.icon}</span>
                    <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-gray-200 text-gray-600">Coming Soon</span>
                  </div>
                  <span className="text-[13px] font-semibold text-[hsl(var(--foreground))]">{t.label}</span>
                  <span className="text-[11px] text-[hsl(var(--muted-foreground))]">{t.desc}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="grid gap-4">
          {data.integrations.map((intg) => (
            <IntegrationCard
              key={intg.id}
              integration={intg}
              onDelete={() => setDeleteModal({ id: intg.id, name: intg.name })}
            />
          ))}
        </div>
      )}
    </div>
  );
}

function IntegrationCard({
  integration: intg,
  onDelete,
}: {
  integration: Integration;
  onDelete: () => void;
}) {
  const typeInfo = ALL_TYPE_OPTIONS.find((t) => t.value === intg.integration_type);
  const typeColor = TYPE_COLORS[intg.integration_type] || "bg-gray-100 text-gray-700";
  const isComingSoon = COMING_SOON_TYPES.has(intg.integration_type);

  return (
    <Card className="transition-all hover:shadow-md">
      <CardBody>
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div className="flex items-start gap-3 flex-1">
            <span className="text-2xl mt-0.5">{typeInfo?.icon || "🔌"}</span>
            <div>
              <div className="flex items-center gap-2 flex-wrap">
                <h3 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">{intg.name}</h3>
                <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium capitalize ${typeColor}`}>
                  {intg.integration_type}
                </span>
                {isComingSoon && (
                  <span className="rounded-md px-2 py-0.5 text-[11px] font-medium bg-amber-100 text-amber-700">
                    Coming Soon
                  </span>
                )}
                <span className={`rounded-md px-2 py-0.5 text-[11px] font-medium ${
                  intg.is_active ? "bg-green-100 text-green-700" : "bg-gray-100 text-gray-500"
                }`}>
                  {intg.is_active ? "Connected" : "Paused"}
                </span>
              </div>
              {isComingSoon && (
                <p className="mt-2 text-[12px] text-amber-600 bg-amber-50 px-3 py-1.5 rounded-lg">
                  ⚠️ This integration is not yet available. We're working on it and will notify you when it's ready.
                </p>
              )}
              <div className="mt-2 flex flex-wrap items-center gap-2">
                {intg.events && intg.events.length > 0 && intg.events.map((ev) => (
                  <Badge key={ev} variant="outline">{ev}</Badge>
                ))}
              </div>
              {intg.created_at && (
                <span className="mt-2 block text-[12px] text-[hsl(var(--muted-foreground))]">Added {formatDate(intg.created_at)}</span>
              )}
            </div>
          </div>
          <button
            onClick={onDelete}
            className="rounded-xl border border-[hsl(var(--destructive)/0.3)] px-4 py-2 text-[12px] font-medium text-[hsl(var(--destructive))] transition-all hover:bg-[hsl(var(--destructive)/0.06)]"
          >
            Remove
          </button>
        </div>
      </CardBody>
    </Card>
  );
}

function CreateIntegrationForm({ onSubmit }: { onSubmit: (f: { name: string; integration_type: string; config: Record<string, any>; events: string[] }) => Promise<void> }) {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [selectedType, setSelectedType] = useState("slack"); // Default to working integration
  const [selectedEvents, setSelectedEvents] = useState<string[]>([]);

  function toggleEvent(ev: string) {
    setSelectedEvents((prev) => prev.includes(ev) ? prev.filter((e) => e !== ev) : [...prev, ev]);
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setSubmitting(true);
    setError("");
    const fd = new FormData(e.currentTarget);
    try {
      await onSubmit({
        name: fd.get("name") as string,
        integration_type: selectedType,
        config: selectedType === "webhook"
          ? { webhook_url: fd.get("webhook_url") as string }
          : selectedType === "slack"
            ? { webhook_url: fd.get("slack_webhook") as string, channel: fd.get("slack_channel") as string }
            : selectedType === "jira"
              ? {
                  base_url: fd.get("jira_base_url") as string,
                  email: fd.get("jira_email") as string,
                  api_token: fd.get("jira_api_token") as string,
                  project_key: fd.get("jira_project_key") as string,
                }
              : { api_key: fd.get("api_key") as string },
        events: selectedEvents,
      });
    } catch (err) {
      if (err && typeof err === "object" && "detail" in err) {
        setError((err as any).detail);
      } else {
        setError(err instanceof Error ? err.message : "Failed to create integration");
      }
    } finally {
      setSubmitting(false);
    }
  }

  const inputCls = "rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-4 py-2.5 text-[13px] text-[hsl(var(--foreground))] outline-none transition-colors focus:border-[hsl(var(--ring))] focus:ring-2 focus:ring-[hsl(var(--ring)/0.2)]";

  // Filter out coming soon integrations from type selector
  const availableTypes = ALL_TYPE_OPTIONS.filter((t) => !COMING_SOON_TYPES.has(t.value));

  return (
    <Card className="animate-scale-in">
      <CardBody>
        <form onSubmit={handleSubmit} className="space-y-4">
          {error && (
            <div className="rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-[13px] text-red-600">
              {error}
            </div>
          )}

          {/* Type selector - only show available integrations */}
          <div>
            <span className="text-[12px] font-semibold text-[hsl(var(--muted-foreground))]">Integration Type</span>
            <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
              {availableTypes.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setSelectedType(t.value)}
                  className={`flex items-center gap-2 rounded-xl border p-3 text-[12px] font-medium transition-all ${
                    selectedType === t.value
                      ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary)/0.06)] text-[hsl(var(--primary))]"
                      : "border-[hsl(var(--border))] text-[hsl(var(--foreground))] hover:bg-[hsl(var(--accent))]"
                  }`}
                >
                  <span>{t.icon}</span>
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          <label className="flex flex-col gap-1.5 text-[12px]">
            <span className="font-semibold text-[hsl(var(--muted-foreground))]">Name *</span>
            <input name="name" required maxLength={255} className={inputCls} placeholder={`e.g. ${selectedType === "slack" ? "Alerts Channel" : selectedType === "jira" ? "Jira Issues" : "My " + selectedType + " integration"}`} />
          </label>

          {/* Type-specific config */}
          {selectedType === "webhook" && (
            <label className="flex flex-col gap-1.5 text-[12px]">
              <span className="font-semibold text-[hsl(var(--muted-foreground))]">Webhook URL *</span>
              <input name="webhook_url" required type="url" className={inputCls} placeholder="https://your-app.com/webhook" />
            </label>
          )}
          {selectedType === "slack" && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <label className="flex flex-col gap-1.5 text-[12px]">
                <span className="font-semibold text-[hsl(var(--muted-foreground))]">Slack Webhook URL *</span>
                <input name="slack_webhook" required type="url" className={inputCls} placeholder="https://hooks.slack.com/..." />
              </label>
              <label className="flex flex-col gap-1.5 text-[12px]">
                <span className="font-semibold text-[hsl(var(--muted-foreground))]">Channel</span>
                <input name="slack_channel" className={inputCls} placeholder="#alerts" />
              </label>
            </div>
          )}
          {selectedType === "jira" && (
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <label className="flex flex-col gap-1.5 text-[12px]">
                <span className="font-semibold text-[hsl(var(--muted-foreground))]">Jira Base URL *</span>
                <input name="jira_base_url" required type="url" className={inputCls} placeholder="https://your-domain.atlassian.net" />
              </label>
              <label className="flex flex-col gap-1.5 text-[12px]">
                <span className="font-semibold text-[hsl(var(--muted-foreground))]">Email *</span>
                <input name="jira_email" required type="email" className={inputCls} placeholder="you@company.com" />
              </label>
              <label className="flex flex-col gap-1.5 text-[12px]">
                <span className="font-semibold text-[hsl(var(--muted-foreground))]">API Token *</span>
                <input name="jira_api_token" required className={inputCls} placeholder="Your Jira API token" />
              </label>
              <label className="flex flex-col gap-1.5 text-[12px]">
                <span className="font-semibold text-[hsl(var(--muted-foreground))]">Project Key *</span>
                <input name="jira_project_key" required className={inputCls} placeholder="PROJ" />
              </label>
            </div>
          )}

          {/* Event subscriptions */}
          <div>
            <span className="text-[12px] font-semibold text-[hsl(var(--muted-foreground))]">Subscribe to Events</span>
            <div className="mt-2 flex flex-wrap gap-2">
              {EVENT_OPTIONS.map((ev) => (
                <button
                  key={ev.value}
                  type="button"
                  onClick={() => toggleEvent(ev.value)}
                  className={`rounded-lg border px-3 py-1.5 text-[12px] font-medium transition-all ${
                    selectedEvents.includes(ev.value)
                      ? "border-[hsl(var(--primary))] bg-[hsl(var(--primary)/0.06)] text-[hsl(var(--primary))]"
                      : "border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))]"
                  }`}
                >
                  {ev.label}
                </button>
              ))}
            </div>
          </div>

          <button
            type="submit"
            disabled={submitting}
            className="rounded-xl bg-[hsl(var(--primary))] px-5 py-2.5 text-[13px] font-semibold text-white shadow-lg shadow-[hsl(var(--primary)/0.25)] transition-all hover:shadow-xl disabled:opacity-50"
          >
            {submitting ? "Connecting..." : "Connect Integration"}
          </button>
        </form>
      </CardBody>
    </Card>
  );
}
