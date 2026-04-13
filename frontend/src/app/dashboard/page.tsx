"use client";

import { useMemo } from "react";
import { useQuery } from "@/lib/hooks";
import { fetchUsage, fetchFunnel, fetchRiskDistribution } from "@/lib/api";
import type { RiskDistributionResponse } from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/format";
import { StatCard } from "@/components/ui/StatCard";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import {
  LazyBarChart, LazyPieChart, LazyResponsiveContainer,
  Bar, XAxis, YAxis, CartesianGrid, Tooltip, Pie, Cell, Legend,
  chartTooltipStyle, tickStyle,
} from "@/components/charts/LazyRecharts";

const RISK_LABELS = ["Likely to Buy", "Leaning Positive", "On the Fence", "Leaning Away", "Likely to Leave"];
const RISK_COLORS = ["#4CAF50", "#88D4AB", "#FFD700", "#F97316", "#E53935"];

function humanizeRiskBuckets(data: RiskDistributionResponse) {
  return data.buckets.map((b, i) => ({
    ...b,
    name: RISK_LABELS[i] || b.range_label,
  }));
}

function getRiskSummary(data: RiskDistributionResponse): string {
  const total = data.total_sessions;
  if (!total) return "";
  const atRisk = data.buckets
    .filter(b => b.range_min >= 0.6)
    .reduce((sum, b) => sum + b.session_count, 0);
  const safe = data.buckets
    .filter(b => b.range_max <= 0.4)
    .reduce((sum, b) => sum + b.session_count, 0);
  const atRiskPct = Math.round((atRisk / total) * 100);
  const safePct = Math.round((safe / total) * 100);
  return `${safePct}% of visitors show buying signals. ${atRiskPct}% are at risk of leaving \u2014 these are your biggest opportunity for recovery.`;
}

function getConversionContext(rate: number, sessions: number): string {
  const lost = Math.round(sessions * (1 - rate));
  const potential = Math.round(lost * 0.15);
  if (rate < 0.03) return `${lost.toLocaleString()} visitors left without buying. Targeted interventions could recover ~${potential} sales.`;
  if (rate < 0.05) return `Below the 5% industry average. Each 1% improvement = ~${Math.round(sessions * 0.01)} more sales.`;
  return `Above the 5% industry average. Keep optimizing high-friction touchpoints.`;
}

const funnelFetcher = () => fetchFunnel();
const usageFetcher = () => fetchUsage();
const riskFetcher = () => fetchRiskDistribution(5);

export default function OverviewPage() {
  const usage = useQuery(usageFetcher, [], "usage");
  const funnel = useQuery(funnelFetcher, [], "funnel");
  const risk = useQuery(riskFetcher, [], "risk-5");

  const funnelFormatter = useMemo(() => (v: unknown) => formatNumber(v as number), []);
  const riskBuckets = useMemo(() => risk.data ? humanizeRiskBuckets(risk.data) : [], [risk.data]);

  if (usage.loading && funnel.loading && risk.loading) return <Spinner />;

  return (
    <div className="space-y-8">
      {/* Page header */}
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">
          Store Overview
        </h1>
        <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">
          How your visitors are behaving right now and where you&apos;re losing sales
        </p>
      </div>

      {usage.error && <ErrorBox message={usage.error} onRetry={usage.refetch} />}

      {/* KPI row */}
      {usage.data && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 xl:grid-cols-4">
          <StatCard
            label="Visitors Tracked"
            value={formatNumber(usage.data.total_sessions)}
            sub="Total shopping sessions"
            icon={
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
              </svg>
            }
          />
          <StatCard
            label="Behaviors Captured"
            value={formatNumber(usage.data.total_events)}
            sub="Clicks, scrolls, hesitations"
            icon={
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
              </svg>
            }
          />
          <StatCard
            label="Shopping Now"
            value={formatNumber(usage.data.active_sessions_today)}
            sub="Active visitors today"
            trend="up"
            icon={
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            }
          />
          <StatCard
            label="A/B Tests Run"
            value={formatNumber(usage.data.total_experiments)}
            sub="Psychology-based experiments"
            icon={
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" strokeWidth={1.5} stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714a2.25 2.25 0 00.659 1.591L19 14.5M14.25 3.104c.251.023.501.05.75.082M5 14.5l-1.456 7.28a.75.75 0 00.736.893h15.44a.75.75 0 00.736-.893L19 14.5M5 14.5h14" />
              </svg>
            }
          />
        </div>
      )}

      {/* Quick insight banner */}
      {funnel.data && (
        <div className="rounded-xl border border-[hsl(var(--border))] bg-[hsl(var(--accent)/0.3)] p-5">
          <p className="text-[13px] font-semibold text-[hsl(var(--foreground))]">
            Your conversion rate is {formatPercent(funnel.data.conversion_rate)}
          </p>
          <p className="mt-1 text-[13px] text-[hsl(var(--muted-foreground))]">
            {getConversionContext(funnel.data.conversion_rate, funnel.data.total_sessions)}
          </p>
        </div>
      )}

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Funnel chart */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">
                  Where Customers Drop Off
                </h2>
                {funnel.data && (
                  <p className="mt-0.5 text-[12px] text-[hsl(var(--muted-foreground))]">
                    {formatNumber(funnel.data.total_sessions)} visitors \u2192{" "}
                    {formatPercent(funnel.data.conversion_rate)} bought
                  </p>
                )}
              </div>
            </div>
          </CardHeader>
          <CardBody>
            {funnel.loading ? (
              <Spinner />
            ) : funnel.error ? (
              <ErrorBox message={funnel.error} onRetry={funnel.refetch} />
            ) : funnel.data ? (
              <LazyResponsiveContainer width="100%" height={280}>
                <LazyBarChart data={funnel.data.steps} layout="vertical" barSize={20}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis type="number" tick={tickStyle} />
                  <YAxis type="category" dataKey="step" width={100} tick={tickStyle} />
                  <Tooltip
                    contentStyle={chartTooltipStyle}
                    formatter={funnelFormatter}
                  />
                  <Bar dataKey="sessions" fill="hsl(var(--primary))" radius={[0, 6, 6, 0]} name="Visitors" />
                </LazyBarChart>
              </LazyResponsiveContainer>
            ) : null}
          </CardBody>
        </Card>

        {/* Risk distribution */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">
                  Visitor Purchase Intent
                </h2>
                <p className="mt-0.5 text-[12px] text-[hsl(var(--muted-foreground))]">
                  How likely your visitors are to buy, based on their behavior
                </p>
              </div>
            </div>
          </CardHeader>
          <CardBody>
            {risk.loading ? (
              <Spinner />
            ) : risk.error ? (
              <ErrorBox message={risk.error} onRetry={risk.refetch} />
            ) : risk.data ? (
              <>
                <LazyResponsiveContainer width="100%" height={240}>
                  <LazyPieChart>
                    <Pie
                      data={riskBuckets}
                      dataKey="session_count"
                      nameKey="name"
                      cx="50%"
                      cy="50%"
                      innerRadius={55}
                      outerRadius={95}
                      paddingAngle={3}
                      strokeWidth={0}
                    >
                      {riskBuckets.map((_, i) => (
                        <Cell key={i} fill={RISK_COLORS[i % RISK_COLORS.length]} />
                      ))}
                    </Pie>
                    <Legend
                      iconType="circle"
                      iconSize={8}
                      wrapperStyle={{ fontSize: "11px" }}
                    />
                    <Tooltip contentStyle={chartTooltipStyle} />
                  </LazyPieChart>
                </LazyResponsiveContainer>
                <p className="mt-2 text-center text-[12px] text-[hsl(var(--muted-foreground))]">
                  {getRiskSummary(risk.data)}
                </p>
              </>
            ) : null}
          </CardBody>
        </Card>
      </div>
    </div>
  );
}
