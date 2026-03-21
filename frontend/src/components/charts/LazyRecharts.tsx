"use client";

import dynamic from "next/dynamic";

export const LazyBarChart = dynamic(
  () => import("recharts").then((m) => m.BarChart),
  { ssr: false }
);
export const LazyPieChart = dynamic(
  () => import("recharts").then((m) => m.PieChart),
  { ssr: false }
);
export const LazyLineChart = dynamic(
  () => import("recharts").then((m) => m.LineChart),
  { ssr: false }
);
export const LazyResponsiveContainer = dynamic(
  () => import("recharts").then((m) => m.ResponsiveContainer),
  { ssr: false }
);

export {
  Bar, XAxis, YAxis, CartesianGrid, Tooltip, Pie, Cell, Legend, Line,
} from "recharts";

export const chartTooltipStyle = {
  backgroundColor: "hsl(var(--card))",
  border: "1px solid hsl(var(--border))",
  borderRadius: "12px",
  fontSize: "12px",
} as const;

export const tickStyle = { fontSize: 11, fill: "hsl(var(--muted-foreground))" } as const;
