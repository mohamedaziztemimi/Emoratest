"use client";

import { useCallback, useState } from "react";
import { useQuery } from "@/lib/hooks";
import {
  fetchFunnel, fetchFrictionMap, fetchCohorts, fetchRiskDistribution,
} from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/format";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import StatCard from "@/components/ui/StatCard";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import Badge from "@/components/ui/Badge";
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
  LineChart, Line,
} from "recharts";

const COHORT_DIMENSIONS = ["device_type", "country_code", "outcome", "intent_label"] as const;

const chartTooltipStyle = {
  backgroundColor: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "12px",
  fontSize: "12px",
};
const tickStyle = { fontSize: 11, fill: "hsl(var(--muted-foreground))" };

export default function AnalyticsPage() {
  const [cohortDim, setCohortDim] = useState<string>("device_type");

  const funnel = useQuery(() => fetchFunnel());
  const friction = useQuery(() => fetchFrictionMap(30));
  const cohorts = useQuery(
    useCallback(() => fetchCohorts(cohortDim), [cohortDim]),
    [cohortDim]
  );
  const risk = useQuery(() => fetchRiskDistribution(10));

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Analytics</h1>
        <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">
          Deep dive into conversion funnels, friction points, and cohort behavior
        </p>
      </div>

      {/* KPIs */}
      {funnel.data && (
        <div className="grid grid-cols-1 gap-5 sm:grid-cols-3">
          <StatCard label="Total Sessions" value={formatNumber(funnel.data.total_sessions)} />
          <StatCard
            label="Conversion Rate"
            value={formatPercent(funnel.data.conversion_rate)}
            trend={funnel.data.conversion_rate > 0.05 ? "up" : "neutral"}
            sub={funnel.data.conversion_rate > 0.05 ? "Above target" : "Below 5% target"}
          />
          <StatCard label="Avg Risk" value={formatPercent(risk.data?.avg_risk ?? null)} />
        </div>
      )}

      {/* Funnel */}
      <Card>
        <CardHeader>
          <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Conversion Funnel</h2>
        </CardHeader>
        <CardBody>
          {funnel.loading ? <Spinner /> : funnel.error ? (
            <ErrorBox message={funnel.error} onRetry={funnel.refetch} />
          ) : funnel.data && funnel.data.steps.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={funnel.data.steps} barSize={28}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="step" tick={tickStyle} />
                <YAxis tick={tickStyle} />
                <Tooltip contentStyle={chartTooltipStyle} formatter={(v) => formatNumber(v as number)} />
                <Bar dataKey="sessions" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} />
                <Bar dataKey="drop_off" fill="hsl(var(--destructive)/0.6)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No funnel data" />}
        </CardBody>
      </Card>

      <div className="grid grid-cols-1 gap-6 xl:grid-cols-2">
        {/* Friction map */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-2">
              <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Friction Hotspots</h2>
              {friction.data && <Badge variant="outline">{friction.data.total_elements} elements</Badge>}
            </div>
          </CardHeader>
          <CardBody className="p-0">
            {friction.loading ? <Spinner /> : friction.error ? (
              <div className="p-5"><ErrorBox message={friction.error} onRetry={friction.refetch} /></div>
            ) : friction.data && friction.data.elements.length > 0 ? (
              <div className="max-h-[420px] overflow-y-auto">
                <table className="w-full text-left text-[13px]">
                  <thead className="sticky top-0 z-10 border-b border-[hsl(var(--border))] bg-[hsl(var(--card))]">
                    <tr>
                      {["Element", "Events", "Rage Clicks", "Rate", "Hesitation"].map((h) => (
                        <th key={h} className="px-5 py-3 text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-[hsl(var(--border)/0.5)]">
                    {friction.data.elements.map((el) => (
                      <tr key={el.element_id} className="transition-colors hover:bg-[hsl(var(--accent)/0.5)]">
                        <td className="px-5 py-3 font-medium text-[hsl(var(--foreground))]">{el.element_id}</td>
                        <td className="px-5 py-3 text-[hsl(var(--muted-foreground))]">{el.event_count}</td>
                        <td className="px-5 py-3">
                          <Badge variant={el.rage_click_count > 0 ? "destructive" : "default"}>
                            {el.rage_click_count}
                          </Badge>
                        </td>
                        <td className="px-5 py-3 text-[hsl(var(--muted-foreground))]">{formatPercent(el.rage_click_rate)}</td>
                        <td className="px-5 py-3 text-[hsl(var(--muted-foreground))]">{el.avg_hesitation.toFixed(1)}s</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : <div className="p-5"><EmptyState title="No friction data" /></div>}
          </CardBody>
        </Card>

        {/* Risk distribution */}
        <Card>
          <CardHeader>
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Risk Distribution</h2>
          </CardHeader>
          <CardBody>
            {risk.loading ? <Spinner /> : risk.error ? (
              <ErrorBox message={risk.error} onRetry={risk.refetch} />
            ) : risk.data && risk.data.buckets.length > 0 ? (
              <ResponsiveContainer width="100%" height={280}>
                <BarChart data={risk.data.buckets} barSize={24}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="range_label" tick={{ ...tickStyle, fontSize: 10 }} />
                  <YAxis tick={tickStyle} />
                  <Tooltip contentStyle={chartTooltipStyle} />
                  <Bar dataKey="session_count" fill="hsl(var(--primary))" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : <EmptyState title="No risk data" />}
          </CardBody>
        </Card>
      </div>

      {/* Cohort analysis */}
      <Card>
        <CardHeader>
          <div className="flex flex-wrap items-center justify-between gap-4">
            <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Cohort Analysis</h2>
            <select
              value={cohortDim}
              onChange={(e) => setCohortDim(e.target.value)}
              className="rounded-xl border border-[hsl(var(--input))] bg-[hsl(var(--card))] px-3 py-2 text-[13px] text-[hsl(var(--foreground))] outline-none transition-colors focus:border-[hsl(var(--ring))] focus:ring-2 focus:ring-[hsl(var(--ring)/0.2)]"
            >
              {COHORT_DIMENSIONS.map((d) => (
                <option key={d} value={d}>{d.replace("_", " ")}</option>
              ))}
            </select>
          </div>
        </CardHeader>
        <CardBody>
          {cohorts.loading ? <Spinner /> : cohorts.error ? (
            <ErrorBox message={cohorts.error} onRetry={cohorts.refetch} />
          ) : cohorts.data && cohorts.data.buckets.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={cohorts.data.buckets}>
                <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                <XAxis dataKey="label" tick={tickStyle} />
                <YAxis yAxisId="left" tick={tickStyle} />
                <YAxis yAxisId="right" orientation="right" tick={tickStyle} />
                <Tooltip
                  contentStyle={chartTooltipStyle}
                  formatter={(v, name) =>
                    name === "conversion_rate" ? formatPercent(v as number) : formatNumber(v as number)
                  }
                />
                <Bar yAxisId="left" dataKey="session_count" fill="hsl(var(--primary)/0.15)" />
                <Line yAxisId="right" type="monotone" dataKey="conversion_rate" stroke="hsl(var(--primary))" strokeWidth={2.5} dot={{ r: 4, fill: "hsl(var(--primary))" }} />
              </LineChart>
            </ResponsiveContainer>
          ) : <EmptyState title="No cohort data" />}
        </CardBody>
      </Card>
    </div>
  );
}
