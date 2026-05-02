"use client";

import { useState } from "react";
import { useQuery } from "@/lib/hooks";
import { fetchFeedbackSummary, FeedbackSummaryResponse } from "@/lib/api";
import Card from "@/components/ui/Card";

// ── Components ─────────────────────────────────────────────────

function PageHeader({
  onDaysChange,
  days,
}: {
  onDaysChange: (v: number | null) => void;
  days: number | null;
}) {
  return (
    <div className="flex flex-col sm:flex-row sm:items-end sm:justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-bold text-gray-900 tracking-tight">User Feedback</h1>
        <p className="text-sm text-gray-500 mt-1">
          Direct emotion feedback from your visitors via micro-survey
        </p>
      </div>
      <div className="flex gap-1 bg-gray-100 rounded-lg p-1">
        {[
          { key: 7, label: "7 days" },
          { key: 30, label: "30 days" },
          { key: 90, label: "90 days" },
        ].map(({ key, label }) => (
          <button
            key={key}
            onClick={() => onDaysChange(key)}
            className={`px-3 py-1.5 text-sm font-medium rounded-md transition-all ${
              days === key
                ? "bg-white text-gray-900 shadow-sm"
                : "text-gray-600 hover:text-gray-900"
            }`}
          >
            {label}
          </button>
        ))}
      </div>
    </div>
  );
}

function SummaryCards({
  total,
  positive,
  neutral,
  negative,
  positive_pct,
  neutral_pct,
  negative_pct,
}: FeedbackSummaryResponse) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {/* Total Responses */}
      <Card className="p-6">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
          Total Responses
        </p>
        <p className="text-3xl font-bold text-gray-900 mt-2">
          {total}
        </p>
      </Card>

      {/* Positive */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Positive
          </p>
          <span className="text-2xl">😊</span>
        </div>
        <p className="text-3xl font-bold text-emerald-600 mt-2">
          {positive_pct}%
        </p>
        <p className="text-xs text-gray-500">
          {positive} responses
        </p>
      </Card>

      {/* Neutral */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Neutral
          </p>
          <span className="text-2xl">😐</span>
        </div>
        <p className="text-3xl font-bold text-amber-600 mt-2">
          {neutral_pct}%
        </p>
        <p className="text-xs text-gray-500">
          {neutral} responses
        </p>
      </Card>

      {/* Negative */}
      <Card className="p-6">
        <div className="flex items-center justify-between">
          <p className="text-xs font-medium text-gray-500 uppercase tracking-wide">
            Negative
          </p>
          <span className="text-2xl">😟</span>
        </div>
        <p className="text-3xl font-bold text-red-600 mt-2">
          {negative_pct}%
        </p>
        <p className="text-xs text-gray-500">
          {negative} responses
        </p>
      </Card>
    </div>
  );
}

function PageBreakdownTable({ pages }: { pages: FeedbackSummaryResponse["by_page"] }) {
  if (pages.length === 0) {
    return (
      <Card className="p-8 text-center">
        <span className="text-4xl mb-3 block">📊</span>
        <h2 className="text-lg font-semibold text-gray-900 mb-2">
          No feedback data yet
        </h2>
        <p className="text-gray-600 max-w-md mx-auto">
          Feedback responses will appear here once users interact with the micro-survey widget on your site.
        </p>
      </Card>
    );
  }

  return (
    <Card className="overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">Feedback by Page</h2>
        <p className="text-sm text-gray-500 mt-1">
          Per-page breakdown of user sentiment
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left py-3 px-4 font-medium text-gray-600">Page URL</th>
              <th className="text-center py-3 px-4 font-medium text-gray-600">Total</th>
              <th className="text-center py-3 px-4 font-medium text-emerald-600">😊 Positive</th>
              <th className="text-center py-3 px-4 font-medium text-amber-600">😐 Neutral</th>
              <th className="text-center py-3 px-4 font-medium text-red-600">😟 Negative</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {pages.map((page, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="py-3 px-4">
                  <div className="max-w-xs truncate font-medium text-gray-900" title={page.page_url}>
                    {page.page_url}
                  </div>
                </td>
                <td className="text-center py-3 px-4 font-semibold text-gray-900">{page.total}</td>
                <td className="text-center py-3 px-4">
                  <span className="inline-flex items-center gap-1 text-emerald-600">
                    😊 {page.positive_pct}%
                    <span className="text-gray-400">({page.positive})</span>
                  </span>
                </td>
                <td className="text-center py-3 px-4">
                  <span className="inline-flex items-center gap-1 text-amber-600">
                    😐 {page.neutral_pct}%
                    <span className="text-gray-400">({page.neutral})</span>
                  </span>
                </td>
                <td className="text-center py-3 px-4">
                  <span className="inline-flex items-center gap-1 text-red-600">
                    😟 {page.negative_pct}%
                    <span className="text-gray-400">({page.negative})</span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}

function MLComparisonTable({ comparison }: { comparison: FeedbackSummaryResponse["ml_comparison"] }) {
  if (comparison.length === 0) {
    return null;
  }

  // Format emotion names for display
  const formatEmotion = (emotion: string) => {
    return emotion.split("_").map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(" ");
  };

  // Calculate totals for percentage
  const totalSessions = comparison.reduce((sum, item) => sum + item.total, 0);

  return (
    <Card className="overflow-hidden">
      <div className="px-6 py-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900">ML Model vs User Feedback</h2>
        <p className="text-sm text-gray-500 mt-1">
          When our model predicts an emotion, how do users actually feel?
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead className="bg-gray-50">
            <tr>
              <th className="text-left py-3 px-4 font-medium text-gray-600">ML Predicted</th>
              <th className="text-center py-3 px-4 font-medium text-emerald-600">😊 User Said Positive</th>
              <th className="text-center py-3 px-4 font-medium text-amber-600">😐 User Said Neutral</th>
              <th className="text-center py-3 px-4 font-medium text-red-600">😟 User Said Negative</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-200">
            {comparison.map((item, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="py-3 px-4">
                  <div className="font-semibold text-gray-900">
                    {formatEmotion(item.predicted_emotion)}
                  </div>
                  <div className="text-xs text-gray-500">
                    {item.total} sessions
                  </div>
                </td>
                <td className="text-center py-3 px-4">
                  <span className="inline-flex items-center gap-1 text-emerald-600">
                    😊 {item.positive_count}
                    <span className="text-gray-400">
                      ({item.total > 0 ? Math.round(item.positive_count / item.total * 100) : 0}%)
                    </span>
                  </span>
                </td>
                <td className="text-center py-3 px-4">
                  <span className="inline-flex items-center gap-1 text-amber-600">
                    😐 {item.neutral_count}
                    <span className="text-gray-400">
                      ({item.total > 0 ? Math.round(item.neutral_count / item.total * 100) : 0}%)
                    </span>
                  </span>
                </td>
                <td className="text-center py-3 px-4">
                  <span className="inline-flex items-center gap-1 text-red-600">
                    😟 {item.negative_count}
                    <span className="text-gray-400">
                      ({item.total > 0 ? Math.round(item.negative_count / item.total * 100) : 0}%)
                    </span>
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <p className="text-xs text-gray-500">
          💡 <strong>Tip:</strong> If "Frustrated" predictions show many 😊 responses, the model may need recalibration.
        </p>
      </div>
    </Card>
  );
}

function LoadingState() {
  return (
    <div className="space-y-6">
      <div className="grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map((i) => (
          <div key={i} className="bg-gray-100 rounded-xl h-28 animate-pulse" />
        ))}
      </div>
      <div className="bg-gray-100 rounded-xl h-64 animate-pulse" />
      <div className="bg-gray-100 rounded-xl h-64 animate-pulse" />
    </div>
  );
}

function EmptyState() {
  return (
    <Card className="p-12 text-center">
      <span className="text-5xl mb-4 block">💬</span>
      <h2 className="text-xl font-semibold text-gray-900 mb-2">
        No feedback yet
      </h2>
      <p className="text-gray-600 max-w-md mx-auto mb-6">
        Enable the micro-survey widget in your EmoraTest SDK to start collecting direct user feedback.
      </p>
      <a
        href="/dashboard/settings"
        className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
      >
        Go to Settings
      </a>
    </Card>
  );
}

// ── MAIN PAGE ─────────────────────────────────────────────────

export default function FeedbackPage() {
  const [days, setDays] = useState<number | null>(null); // null = use API default (30 days)

  const { data: feedback, loading, error } = useQuery(
    () => fetchFeedbackSummary(days ?? undefined),
    [days],
    `feedback-${days ?? "default"}`
  );

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto">
        <PageHeader onDaysChange={setDays} days={days} />
        <LoadingState />
      </div>
    );
  }

  if (error || !feedback) {
    return (
      <div className="max-w-6xl mx-auto">
        <PageHeader onDaysChange={setDays} days={days} />
        <EmptyState />
      </div>
    );
  }

  // Calculate percentages if not provided by API
  const total = feedback.total || 1;
  const positive_pct = feedback.positive_pct ?? Math.round((feedback.positive / total) * 100);
  const neutral_pct = feedback.neutral_pct ?? Math.round((feedback.neutral / total) * 100);
  const negative_pct = feedback.negative_pct ?? Math.round((feedback.negative / total) * 100);

  return (
    <div className="max-w-6xl mx-auto pb-24">
      <PageHeader onDaysChange={setDays} days={days} />

      {feedback.total === 0 ? (
        <EmptyState />
      ) : (
        <div className="space-y-6">
          <SummaryCards
            total={feedback.total}
            positive={feedback.positive}
            neutral={feedback.neutral}
            negative={feedback.negative}
            positive_pct={positive_pct}
            neutral_pct={neutral_pct}
            negative_pct={negative_pct}
          />

          <PageBreakdownTable pages={feedback.by_page} />

          <MLComparisonTable comparison={feedback.ml_comparison} />
        </div>
      )}
    </div>
  );
}
