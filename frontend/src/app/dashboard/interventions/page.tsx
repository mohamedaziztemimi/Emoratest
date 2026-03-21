"use client";

import { useMemo } from "react";
import { useQuery } from "@/lib/hooks";
import { fetchInterventionStats } from "@/lib/api";
import { formatPercent, formatNumber } from "@/lib/format";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import Badge from "@/components/ui/Badge";
import Spinner from "@/components/ui/Spinner";
import ErrorBox from "@/components/ui/ErrorBox";
import EmptyState from "@/components/ui/EmptyState";
import {
  LazyBarChart, LazyResponsiveContainer,
  Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  chartTooltipStyle, tickStyle,
} from "@/components/charts/LazyRecharts";

const statsFetcher = () => fetchInterventionStats();

export default function InterventionsPage() {
  const { data, error, loading, refetch } = useQuery(statsFetcher, [], "intervention-stats");

  const tooltipFormatter = useMemo(
    () => (v: unknown, name?: string | number) =>
      name === "conversion_rate" ? formatPercent(v as number) : formatNumber(v as number),
    []
  );

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-[26px] font-bold tracking-tight text-[hsl(var(--foreground))]">Interventions</h1>
        <p className="mt-1 text-[14px] text-[hsl(var(--muted-foreground))]">
          Psychology-based intervention performance metrics
        </p>
      </div>

      {loading ? <Spinner /> : error ? (
        <ErrorBox message={error} onRetry={refetch} />
      ) : !data || data.length === 0 ? (
        <EmptyState title="No intervention data yet" description="Stats appear here once sessions trigger interventions." />
      ) : (
        <>
          {/* Stacked chart */}
          <Card>
            <CardHeader>
              <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Performance Overview</h2>
            </CardHeader>
            <CardBody>
              <LazyResponsiveContainer width="100%" height={320}>
                <LazyBarChart data={data} barSize={28}>
                  <CartesianGrid strokeDasharray="3 3" stroke="hsl(var(--border))" />
                  <XAxis dataKey="intervention_id" tick={tickStyle} />
                  <YAxis tick={tickStyle} />
                  <Tooltip contentStyle={chartTooltipStyle} formatter={tooltipFormatter} />
                  <Legend iconType="circle" iconSize={8} wrapperStyle={{ fontSize: "11px" }} />
                  <Bar dataKey="converted" fill="hsl(var(--success))" stackId="a" radius={[0, 0, 0, 0]} />
                  <Bar dataKey="dismissed" fill="hsl(var(--warning))" stackId="a" />
                  <Bar dataKey="ignored" fill="hsl(var(--muted-foreground)/0.3)" stackId="a" />
                  <Bar dataKey="bounced" fill="hsl(var(--destructive))" stackId="a" radius={[6, 6, 0, 0]} />
                </LazyBarChart>
              </LazyResponsiveContainer>
            </CardBody>
          </Card>

          {/* Stats table */}
          <Card className="overflow-hidden">
            <CardHeader>
              <h2 className="text-[15px] font-semibold text-[hsl(var(--foreground))]">Detailed Statistics</h2>
            </CardHeader>
            <div className="overflow-x-auto">
              <table className="w-full text-left text-[13px]">
                <thead className="border-b border-[hsl(var(--border))] bg-[hsl(var(--secondary)/0.5)]">
                  <tr>
                    {["Intervention", "Triggers", "Converted", "Dismissed", "Ignored", "Bounced", "Conv Rate", "Avg Delta"].map((h) => (
                      <th key={h} className="px-5 py-3.5 text-[11px] font-semibold uppercase tracking-wider text-[hsl(var(--muted-foreground))]">{h}</th>
                    ))}
                  </tr>
                </thead>
                <tbody className="divide-y divide-[hsl(var(--border)/0.5)]">
                  {data.map((s) => (
                    <tr key={s.intervention_id} className="transition-colors hover:bg-[hsl(var(--accent)/0.5)]">
                      <td className="px-5 py-3.5 font-medium text-[hsl(var(--foreground))]">{s.intervention_id}</td>
                      <td className="px-5 py-3.5 text-[hsl(var(--muted-foreground))]">{formatNumber(s.total_triggers)}</td>
                      <td className="px-5 py-3.5"><Badge variant="success">{formatNumber(s.converted)}</Badge></td>
                      <td className="px-5 py-3.5"><Badge variant="warning">{formatNumber(s.dismissed)}</Badge></td>
                      <td className="px-5 py-3.5 text-[hsl(var(--muted-foreground))]">{formatNumber(s.ignored)}</td>
                      <td className="px-5 py-3.5"><Badge variant="destructive">{formatNumber(s.bounced)}</Badge></td>
                      <td className="px-5 py-3.5 font-semibold text-[hsl(var(--primary))]">{formatPercent(s.conversion_rate)}</td>
                      <td className="px-5 py-3.5 text-[hsl(var(--muted-foreground))]">{formatPercent(s.avg_conversion_delta)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </Card>
        </>
      )}
    </div>
  );
}
