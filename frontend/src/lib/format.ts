/**
 * Formatting utilities for the dashboard (CONV-51).
 */

export function formatPercent(value: number | null | undefined): string {
  if (value == null) return "--";
  return `${(value * 100).toFixed(1)}%`;
}

export function formatRisk(value: number | null | undefined): string {
  if (value == null) return "--";
  const pct = value * 100;
  if (pct >= 70) return `${pct.toFixed(0)}% High`;
  if (pct >= 40) return `${pct.toFixed(0)}% Med`;
  return `${pct.toFixed(0)}% Low`;
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "--";
  return new Date(iso).toLocaleDateString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function formatDuration(seconds: number | null | undefined): string {
  if (seconds == null) return "--";
  if (seconds < 60) return `${seconds.toFixed(0)}s`;
  const mins = Math.floor(seconds / 60);
  const secs = Math.round(seconds % 60);
  return `${mins}m ${secs}s`;
}

export function formatNumber(value: number | null | undefined): string {
  if (value == null) return "--";
  return value.toLocaleString("en-US");
}

export type RiskVariant = "success" | "warning" | "destructive" | "default";

export function riskVariant(value: number | null | undefined): RiskVariant {
  if (value == null) return "default";
  if (value >= 0.7) return "destructive";
  if (value >= 0.4) return "warning";
  return "success";
}

export type OutcomeVariant = "success" | "destructive" | "default";

export function outcomeVariant(outcome: string): OutcomeVariant {
  switch (outcome) {
    case "purchase": return "success";
    case "abandon": return "destructive";
    default: return "default";
  }
}
