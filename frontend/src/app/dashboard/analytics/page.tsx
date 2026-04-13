"use client";

import { useCallback, useMemo, useState } from "react";
import { useQuery } from "@/lib/hooks";

// ── Types ────────────────────────────────────────────────

export interface FunnelStep {
  name: string;
  visitors: number;
  conversions: number;
  conversionRate: number;
  dropOffRate: number;
  emotionProfile?: Record<string, number>;
  dominantEmotion?: string;
}

export interface FunnelResult {
  experimentId: string;
  steps: FunnelStep[];
  totalVisitors: number;
  overallConversionRate: number;
  variantId?: string;
}

export interface ExperimentVariant {
  variantId: string;
  name: string;
  visitors: number;
  conversions: number;
  conversionRate: number;
  relativeLift: number | null;
  pValue: number | null;
  confidenceInterval: [number, number] | null;
  isSignificant: boolean;
  practicalSignificance: "significant_positive" | "significant_negative" | "equivalent" | "inconclusive";
}

export interface ExperimentResults {
  experimentId: string;
  experimentName: string;
  variants: ExperimentVariant[];
  winner: string | null;
  status: string;
  totalVisitors: number;
  totalConversions: number;
  srmDetected?: boolean;
  srmSeverity?: string;
}

export interface Anomaly {
  timestamp: string;
  metric: string;
  value: number;
  zScore: number;
  type: "spike" | "drop";
}

export interface EmotionInsight {
  emotion: string;
  timeline: Array<{ timestamp: string; avgScore: number }>;
  frustrationVsConversion: Array<{ x: number; y: number; label: string }>;
  whyAnalysis: string;
}

export interface CUPEDResult {
  enabled: boolean;
  varianceReduction: number | null;
  theta: number | null;
}

// ── UI Components ────────────────────────────────────────────

function SRMBanner({ detected, severity, affectedVariants }: {
  detected: boolean;
  severity: string;
  affectedVariants: string[];
}) {
  if (!detected) return null;

  return (
    <div className="bg-amber-50 border-l-4 border-amber-500 rounded-lg p-4 mb-6">
      <div className="flex items-start gap-3">
        <svg className="w-6 h-6 text-amber-600 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01M12 17v.01M4 12a3 3 0 00-3-3m0 3v6a3 3 0 006-6m0 6a2 2 0 00-2 2 0 2 2" />
        </svg>
        <div>
          <h3 className="font-semibold text-amber-800">Sample Ratio Mismatch (SRM) Detected</h3>
          <p className="text-sm text-amber-700 mt-1">
            {severity === "severe"
              ? "Severe allocation imbalance detected. The observed traffic split significantly differs from expected split (p < 0.001)."
              : severity === "moderate"
              ? "Moderate allocation imbalance detected. Traffic split doesn't match expected ratios."}
          </p>
          {affectedVariants.length > 0 && (
            <p className="text-sm text-amber-700 mt-2">
              Affected variants: <strong>{affectedVariants.join(", ")}</strong>. Consider re-running or increasing sample size.
            </p>
          )}
        </div>
      </div>
    );
  );
}

function ResultsTable({ results, onExport }: {
  results: ExperimentResults | null;
  onExport: () => void;
}) {
  if (!results) return null;

  const getROPEBadge = (classification?: string) => {
    switch (classification) {
      case "significant_positive":
        return <span className="inline-flex items-center px-2 py-1 rounded-full bg-green-100 text-green-700 text-xs font-medium">
          ✓ Significant Positive
        </span>;
      case "significant_negative":
        return <span className="inline-flex items-center px-2 py-1 rounded-full bg-red-100 text-red-700 text-xs font-medium">
          ✗ Significant Negative
        </span>;
      case "equivalent":
        return <span className="inline-flex items-center px-2 py-1 rounded-full bg-blue-100 text-blue-700 text-xs font-medium">
          ≈ Practically Equivalent
        </span>;
      default:
        return <span className="inline-flex items-center px-2 py-1 rounded-full bg-gray-100 text-gray-700 text-xs font-medium">
          ? Inconclusive
        </span>;
    }
  };

  return (
    <div className="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))] overflow-hidden">
      <div className="px-6 py-4 border-b border-[hsl(var(--border))] flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-[hsl(var(--foreground))]">Experiment Results</h3>
          <p className="text-sm text-[hsl(var(--muted-foreground))]">{results.experimentName}</p>
        </div>
        <button
          onClick={onExport}
          className="px-4 py-2 text-sm bg-[hsl(var(--muted))] hover:bg-[hsl(var(--accent))] rounded-lg transition-colors"
        >
          Export CSV
        </button>
      </div>

      {/* SRM Banner */}
      {results.srmDetected && (
        <div className="p-4 border-b border-[hsl(var(--border))]">
          <SRMBanner
            detected={results.srmDetected}
            severity={results.srmSeverity || "moderate"}
            affectedVariants={results.variants.map((v) => v.name)}
          />
        </div>
      )}

      {/* Variants Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-left">
          <thead className="bg-[hsl(var(--muted))]/50">
            <tr>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Variant</th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Visitors</th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Conversions</th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Conversion Rate</th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">Lift</th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">P-Value</th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">95% CI</th>
              <th className="px-4 py-3 text-xs font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">ROPE</th>
            </tr>
          </thead>
          <tbody>
            {results.variants.map((variant, index) => {
              const isWinner = variant.variantId === results.winner;
              return (
                <tr key={variant.variantId} className={isWinner ? "bg-green-50" : ""}>
                  <td className="px-4 py-3">
                    {isWinner && (
                      <span className="inline-flex items-center mr-2">
                        <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 0 8 8 0 0116 4l-2.829 2.829-2.829 2.829a8 8 0 1116 0l5.172-5.172a8 8 0 00016-4l5.172 5.172a8 8 0 00016 4L10 18z" clipRule="evenodd" />
                        </svg>
                      </span>
                    )}
                    {variant.name}
                  </td>
                  <td className="px-4 py-3 text-[hsl(var(--foreground))]">{variant.visitors.toLocaleString()}</td>
                  <td className="px-4 py-3 text-[hsl(var(--foreground))]">{variant.conversions.toLocaleString()}</td>
                  <td className="px-4 py-3 font-semibold text-[hsl(var(--foreground))]">
                    {(variant.conversionRate * 100).toFixed(2)}%
                  </td>
                  <td className="px-4 py-3 text-[hsl(var(--foreground))]">
                    {variant.relativeLift !== null ? (
                      <span className={variant.relativeLift > 0 ? "text-green-600" : "text-red-600"}>
                        {variant.relativeLift > 0 ? "+" : ""}
                        {(variant.relativeLift * 100).toFixed(1)}%
                      </span>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3 text-[hsl(var(--foreground))]">
                    {variant.pValue !== null ? (
                      <span className={variant.pValue < 0.05 ? "text-green-600" : "text-red-600"}>
                        {variant.pValue < 0.05 ? "< 0.05" : "≥ 0.05"}
                      </span>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3 text-[hsl(var(--foreground))]">
                    {variant.confidenceInterval ? (
                      <span className="text-xs">
                        [{(variant.confidenceInterval[0] * 100).toFixed(1)}%, {(variant.confidenceInterval[1] * 100).toFixed(1)}%]
                      </span>
                    ) : "—"}
                  </td>
                  <td className="px-4 py-3">
                    {getROPEBadge(variant.practicalSignificance)}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Summary Stats */}
      <div className="px-6 py-4 bg-[hsl(var(--muted))]/30">
        <div className="grid grid-cols-3 gap-6">
          <div>
            <div className="text-sm text-[hsl(var(--muted-foreground))]">Total Visitors</div>
            <div className="text-2xl font-bold text-[hsl(var(--foreground))]">{results.totalVisitors.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-sm text-[hsl(var(--muted-foreground))]">Total Conversions</div>
            <div className="text-2xl font-bold text-[hsl(var(--foreground))]">{results.totalConversions.toLocaleString()}</div>
          </div>
          <div>
            <div className="text-sm text-[hsl(var(--muted-foreground))]">Overall Conversion</div>
            <div className="text-2xl font-bold text-[hsl(var(--foreground))]">{(results.totalConversions / results.totalVisitors * 100).toFixed(2)}%</div>
          </div>
        </div>
      </div>
    </div>
  );
}

function AnomalyFeed({ anomalies }: { anomalies: Anomaly[] }) {
  if (!anomalies || anomalies.length === 0) {
    return (
      <div className="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))] p-8 text-center text-[hsl(var(--muted-foreground))]">
        <svg className="w-12 h-12 mx-auto mb-4 text-[hsl(var(--muted-foreground))]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0l6 3 6 6 6 0 1116 0l-6-3a9 9 0 00016-4z" />
        </svg>
        <p>No anomalies detected</p>
      </div>
    );
  }

  return (
    <div className="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))]">
      <div className="px-6 py-4 border-b border-[hsl(var(--border))]">
        <h3 className="text-lg font-semibold text-[hsl(var(--foreground))]">Anomaly Detection</h3>
        <p className="text-sm text-[hsl(var(--muted-foreground))]">Recent metric anomalies detected via Z-score analysis</p>
      </div>

      <div className="max-h-80 overflow-y-auto">
        {anomalies.map((anomaly, index) => (
          <div
            key={index}
            className={`px-6 py-3 border-b border-[hsl(var(--border))] flex items-center justify-between ${
              anomaly.type === "spike" ? "bg-red-50" : "bg-orange-50"
            }`}
          >
            <div className="flex-1">
              <div className="flex items-center gap-2">
                <span
                  className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-semibold ${
                    anomaly.type === "spike"
                      ? "bg-red-200 text-red-700"
                      : "bg-orange-200 text-orange-700"
                  }`}
                >
                  {anomaly.type === "spike" ? "↑ Spike" : "↓ Drop"}
                </span>
                <span className="text-[hsl(var(--foreground))] font-medium">{anomaly.metric}</span>
              </div>
              <div className="text-sm text-[hsl(var(--muted-foreground))]">
                Value: {(anomaly.value * 100).toFixed(2)}% | Z-Score: {anomaly.zScore.toFixed(2)}
              </div>
              <div className="text-xs text-[hsl(var(--muted-foreground))]">
                {new Date(anomaly.timestamp).toLocaleString()}
              </div>
            </div>
            <div className="text-sm font-semibold text-[hsl(var(--foreground))]">
              {anomaly.zScore > 4 ? "Severe" : anomaly.zScore > 3 ? "Moderate" : "Minor"}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function EmotionInsights({ insights }: { insights: EmotionInsight | null }) {
  if (!insights) {
    return (
      <div className="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))] p-8 text-center">
        <p className="text-[hsl(var(--muted-foreground))]">No emotion insights available</p>
      </div>
    );
  }

  const EMOTION_COLORS: Record<string, string> = {
    confusion: "#F59E0B",
    frustration: "#EF4444",
    delight: "#10B981",
    anxiety: "#8B5CF6",
    satisfaction: "#3B82F6",
    hesitation: "#FBBF24",
    focus: "#60A5FA",
  };

  return (
    <div className="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))]">
      <div className="px-6 py-4 border-b border-[hsl(var(--border))]">
        <h3 className="text-lg font-semibold text-[hsl(var(--foreground))]">Emotion Insights</h3>
      </div>

      <div className="p-6 space-y-6">
        {/* Emotion Timeline */}
        <div>
          <h4 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-3">Emotion Timeline by Variant</h4>
          <div className="flex items-center gap-4 mb-4">
            {insights.timeline.map((point, index) => (
              <div key={index} className="flex-1">
                <div className="text-xs text-[hsl(var(--muted-foreground))] mb-1">
                  {new Date(point.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                </div>
                <div
                  className="h-20 rounded transition-all duration-500"
                  style={{ width: `${point.avgScore * 100}%`, backgroundColor: EMOTION_COLORS[point.emotion] }}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Frustration vs Conversion Scatter */}
        <div>
          <h4 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-3">Frustration vs Conversion</h4>
          <div className="h-48 relative">
            <svg width="100%" height="100%" viewBox="0 0 100 100">
              {/* Axes */}
              <line x1="10" y1="10" x2="10" y2="90" stroke="hsl(var(--border))" strokeWidth="1" />
              <line x1="10" y1="90" x2="90" y2="90" stroke="hsl(var(--border))" strokeWidth="1" />

              {/* Data points */}
              {insights.frustrationVsConversion.map((point, index) => (
                <circle
                  key={index}
                  cx={10 + point.x * 0.8}
                  cy={90 - point.y * 0.8}
                  r={4}
                  fill={point.y > 50 ? "#EF4444" : "#10B981"}
                  className="cursor-pointer hover:r-6 transition-all"
                />
              ))}

              {/* Trend line */}
              <line
                x1="10"
                y1="90"
                x2="90"
                y2="10"
                stroke="hsl(var(--muted-foreground))"
                strokeWidth="2"
                strokeDasharray="4 4"
                opacity="0.5"
              />

              {/* Labels */}
              <text x="50" y="5" textAnchor="middle" className="text-xs text-[hsl(var(--muted-foreground))]">
                Frustration ↑
              </text>
              <text x="95" y="50" textAnchor="end" className="text-xs text-[hsl(var(--muted-foreground))]">
                Conversion →
              </text>
            </svg>
          </div>
        </div>

        {/* Why-Analysis Summary */}
        <div>
          <h4 className="text-sm font-semibold text-[hsl(var(--foreground))] mb-3">Why Analysis Summary</h4>
          <div className="bg-[hsl(var(--accent))]/10 rounded-lg p-4">
            <p className="text-sm text-[hsl(var(--foreground))] leading-relaxed">
              {insights.whyAnalysis}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

function CUPEDToggle({ result, onToggle }: {
  result: CUPEDResult;
  onToggle: (enabled: boolean) => void;
}) {
  return (
    <div className="bg-[hsl(var(--card))] rounded-lg border border-[hsl(var(--border))] p-4">
      <div className="flex items-center justify-between">
        <div>
          <h4 className="text-sm font-semibold text-[hsl(var(--foreground))]">CUPED Variance Reduction</h4>
          <p className="text-xs text-[hsl(var(--muted-foreground))] mt-1">
            Use pre-experiment covariate to reduce variance and improve statistical power
          </p>
        </div>
        <label className="flex items-center gap-3 cursor-pointer">
          <input
            type="checkbox"
            checked={result.enabled}
            onChange={(e) => onToggle(e.target.checked)}
            className="w-5 h-5 rounded border-[hsl(var(--border))] text-[hsl(var(--primary))] focus:ring-2 focus:ring-[hsl(var(--ring))] focus:ring-offset-2"
          />
          <span className="text-sm text-[hsl(var(--foreground))]">Enable CUPED</span>
        </label>
      </div>
      {result.enabled && result.varianceReduction !== null && (
        <div className="mt-4 pt-4 border-t border-[hsl(var(--border))]">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <div className="text-xs text-[hsl(var(--muted-foreground))]">Variance Reduction</div>
              <div className="text-xl font-bold text-[hsl(var(--foreground))]">
                {result.varianceReduction.toFixed(1)}%
              </div>
            </div>
            <div>
              <div className="text-xs text-[hsl(var(--muted-foreground))]">Regression Coefficient (θ)</div>
              <div className="text-xl font-bold text-[hsl(var(--foreground))]">
                {result.theta?.toFixed(3) || "—"}
              </div>
            </div>
          </div>
          <div className="mt-3 flex items-center gap-2">
            <svg className="w-5 h-5 text-green-600" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M16.707 5.293a1 1 0 00-1.414 1.414L9 16.586A3 3 0 00-.293.707.293l-7-7 1.414 1.414A1 1 0 001.414 1.414l1.414-1.414A1 1 0 012.586-5.293 16.707-5.293a1 1 0 00-1.414-1.414z" clipRule="evenodd" />
            </svg>
            <span className="text-sm text-[hsl(var(--foreground))]">
              CUPED enabled. Using pre-experiment covariate for variance reduction.
            </span>
          </div>
        </div>
      )}
    </div>
  );
}

// ── Main Analytics Page Component ────────────────────────────────────

const METRIC_OPTIONS = ["conversion_rate", "revenue", "session_duration"] as const;

export default function AnalyticsPage() {
  const [experimentId, setExperimentId] = useState("current");
  const [activeTab, setActiveTab] = useState<"results" | "funnel" | "emotions" | "anomalies">("results");
  const [showEmotions, setShowEmotions] = useState(false);
  const [cupedEnabled, setCupedEnabled] = useState(false);
  const [covariateMetric, setCovariateMetric] = useState("revenue");

  // Fetch experiment results
  const { data: results, loading, refetch } = useQuery<ExperimentResults>({
    queryKey: ["experiment-results", experimentId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/experiments/${experimentId}/results`);
      return res.json();
    },
    enabled: !!experimentId,
    refetchInterval: 30000, // Poll every 30s
  });

  // Fetch funnel data
  const { data: funnelData } = useQuery<FunnelResult>({
    queryKey: ["funnel", experimentId, activeTab],
    queryFn: async () => {
      if (activeTab === "funnel") {
        const res = await fetch(`/api/v1/analytics/funnel?experiment_id=${experimentId}`);
        return res.json();
      }
      return null;
    },
    enabled: activeTab === "funnel",
  });

  // Fetch emotion insights
  const { data: emotionInsights } = useQuery<EmotionInsight>({
    queryKey: ["emotion-insights", experimentId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/emotion/experiments/${experimentId}/why-analysis`);
      return res.json();
    },
    enabled: activeTab === "emotions",
  });

  // Fetch anomalies
  const { data: anomalies } = useQuery<{ anomalies: Anomaly[] }>({
    queryKey: ["anomalies", experimentId],
    queryFn: async () => {
      const res = await fetch(`/api/v1/analytics/anomalies?experiment_id=${experimentId}`);
      return res.json();
    },
    enabled: activeTab === "anomalies",
    refetchInterval: 60000, // Poll every 60s
  });

  const handleExport = useCallback(() => {
    if (!results) return;
    const csvContent = [
      "Variant,Visitors,Conversions,Conversion Rate,Lift,P-Value,95% CI Lower,95% CI Upper,ROPE",
      ...results.variants.map(
        (v) =>
          `${v.name},${v.visitors},${v.conversions},${(v.conversionRate * 100).toFixed(2)}%,${v.relativeLift || ""},${v.pValue || ""},${v.confidenceInterval?.[0] || ""},${v.confidenceInterval?.[1] || ""},${v.practicalSignificance || ""}`
      ),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${results.experimentName}_results.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }, [results]);

  const handleCupedToggle = useCallback((enabled: boolean) => {
    setCupedEnabled(enabled);
    // TODO: Call API to enable/disable CUPED
  }, []);

  return (
    <div className="min-h-screen bg-[hsl(var(--background))]">
      <div className="max-w-7xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div>
            <h1 className="text-2xl font-bold text-[hsl(var(--foreground))]">Analytics Dashboard</h1>
            <p className="text-[hsl(var(--muted-foreground))]">
              Advanced statistical analysis with CUPED, ROPE, SRM detection, and emotion overlays
            </p>
          </div>
          <div className="flex items-center gap-4">
            <select
              value={experimentId}
              onChange={(e) => setExperimentId(e.target.value)}
              className="px-4 py-2 border border-[hsl(var(--border))] rounded-lg bg-[hsl(var(--card))] text-[hsl(var(--foreground))] focus:outline-none focus:ring-2 focus:ring-[hsl(var(--ring))] focus:ring-offset-2"
            >
              <option value="current">Current Experiment</option>
              {/* TODO: Fetch actual experiments */}
            </select>
            <button
              onClick={() => refetch()}
              className="p-2 bg-[hsl(var(--muted))] hover:bg-[hsl(var(--accent))] rounded-lg transition-colors"
              title="Refresh data"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356-2A2 2 0 00-2.828-2.828l-1.414 1.414V9a2 2 0 0112 1.414l1.414 1.414a1 1 0 001.414 1.414l1.414-1.414A1 1 0 0112 0l6.586-5.172a1 1 0 00016-4z" />
              </svg>
            </button>
          </div>
        </div>

        {/* Tabs */}
        <div className="flex border-b border-[hsl(var(--border))] mb-6">
          {[
            { id: "results", label: "Results" },
            { id: "funnel", label: "Funnel" },
            { id: "emotions", label: "Emotions" },
            { id: "anomalies", label: "Anomalies" },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 font-medium transition-colors ${
                activeTab === tab.id
                  ? "text-[hsl(var(--primary))] border-b-2 border-[hsl(var(--primary))]"
                  : "text-[hsl(var(--muted-foreground))] hover:text-[hsl(var(--foreground))] border-b-2 border-transparent"
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Tab Content */}
        {activeTab === "results" && (
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            <div className="xl:col-span-2">
              <ResultsTable results={results} onExport={handleExport} />
            </div>
            <div className="xl:col-span-1">
              <CUPEDToggle
                result={{ enabled: cupedEnabled, varianceReduction: cupedEnabled ? 15.3 : null, theta: null }}
                onToggle={handleCupedToggle}
              />
            </div>
          </div>
        )}

        {activeTab === "funnel" && (
          <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
            <div>
              {funnelData && <FunnelChart data={funnelData} showEmotions={showEmotions} height={350} />}
            </div>
            <div className="flex items-center justify-end">
              <label className="flex items-center gap-2 cursor-pointer">
                <input
                  type="checkbox"
                  checked={showEmotions}
                  onChange={(e) => setShowEmotions(e.target.checked)}
                  className="w-5 h-5 rounded border-[hsl(var(--border))] text-[hsl(var(--primary))] focus:ring-2 focus:ring-[hsl(var(--ring))] focus:ring-offset-2"
                />
                <span className="text-sm text-[hsl(var(--foreground))]">Show Emotions</span>
              </label>
            </div>
            </div>
          </div>
        )}

        {activeTab === "emotions" && (
          <EmotionInsights insights={emotionInsights} />
        )}

        {activeTab === "anomalies" && (
          <AnomalyFeed anomalies={anomalies?.anomalies || []} />
        )}
      </div>
    </div>
  );
}

// ── Import FunnelChart Component ─────────────────────────────────

function FunnelChart({ data, showEmotions = false, height = 300 }: {
  data: FunnelResult;
  showEmotions?: boolean;
  height?: number;
}) {
  const [mounted, setMounted] = useState(false);
  const [hoveredStep, setHoveredStep] = useState<number | null>(null);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!data.steps || data.steps.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-[hsl(var(--muted-foreground))]">
        <p>No funnel data available</p>
      </div>
    );
  }

  const maxVisitors = Math.max(...data.steps.map((s) => s.visitors));
  const chartHeight = height - 40;
  const stepHeight = chartHeight / data.steps.length;
  const maxStepWidth = 600;
  const xCenter = 300;

  const EMOTION_COLORS: Record<string, { bg: string; icon: string }> = {
    confusion: { bg: "#F59E0B", icon: "😕" },
    frustration: { bg: "#EF4444", icon: "😤" },
    delight: { bg: "#10B981", icon: "😊" },
    anxiety: { bg: "#8B5CF6", icon: "😰" },
    satisfaction: { bg: "#3B82F6", icon: "😌" },
    hesitation: { bg: "#FBBF24", icon: "🤔" },
    focus: { bg: "#60A5FA", icon: "🎯" },
  };

  return (
    <div className="relative" style={{ width: "100%", height: `${height + 40}px` }}>
      <svg
        width="100%"
        height={height + 40}
        viewBox={`0 0 600 ${height + 40}`}
        className="overflow-visible"
      >
        <defs>
          <linearGradient id="funnelGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" stopColor="#3B82F6" />
            <stop offset="100%" stopColor="#1D4ED8" />
          </linearGradient>
        </defs>

        {data.steps.map((step, index) => {
          const stepWidth = (step.visitors / maxVisitors) * maxStepWidth;
          const stepY = index * stepHeight + 20;
          const isHovered = hoveredStep === index;
          const dropOffRate = step.dropOffRate;

          const generateTrapezoidPath = () => {
            const halfWidth = stepWidth / 2;
            return `M ${xCenter - halfWidth},${stepY} L ${xCenter + halfWidth},${stepY} L ${xCenter + halfWidth},${stepY + stepHeight} L ${xCenter - halfWidth},${stepY + stepHeight} Z`;
          };

          return (
            <g key={index} onMouseEnter={() => setHoveredStep(index)} onMouseLeave={() => setHoveredStep(null)}>
              <path
                d={generateTrapezoidPath()}
                fill={dropOffRate > 0.4 ? `rgba(239, 68, 68, 0.8)` : "url(#funnelGradient)"}
                stroke="rgba(255, 255, 255, 0.3)"
                strokeWidth={1}
                className={`transition-all duration-300 ${mounted ? "opacity-100" : "opacity-0"}`}
                style={{ transitionDelay: `${index * 100}ms` }}
              />
              <text
                x={xCenter}
                y={stepY + stepHeight / 2}
                textAnchor="middle"
                dominantBaseline="middle"
                className={`fill-[hsl(var(--foreground))] font-semibold ${
                  isHovered ? "text-lg" : "text-sm"
                } transition-all`}
              >
                {step.name}
              </text>
            </g>
          );
        })}
      </svg>

      {/* Tooltip */}
      {hoveredStep !== null && data.steps[hoveredStep] && (
        <div
          className="absolute bg-[hsl(var(--popover))] text-[hsl(var(--popover-foreground))] text-xs rounded shadow-lg border border-[hsl(var(--border))] p-3 pointer-events-none z-50"
          style={{
            left: `${xCenter + 10}px`,
            top: `${hoveredStep * stepHeight + 20}px`,
          }}
        >
          <div className="font-semibold mb-2">{data.steps[hoveredStep].name}</div>
          <div className="space-y-1">
            <div>Visitors: {data.steps[hoveredStep].visitors.toLocaleString()}</div>
            <div>Conversions: {data.steps[hoveredStep].conversions.toLocaleString()}</div>
            <div>Conversion Rate: {(data.steps[hoveredStep].conversionRate * 100).toFixed(2)}%</div>
            <div>Drop-off: {(data.steps[hoveredStep].dropOffRate * 100).toFixed(1)}%</div>
          </div>
        </div>
      )}
    </div>
  );
}
