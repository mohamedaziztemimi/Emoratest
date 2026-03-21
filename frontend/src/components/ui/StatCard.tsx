import clsx from "clsx";

interface StatCardProps {
  label: string;
  value: string;
  sub?: string;
  trend?: "up" | "down" | "neutral";
  icon?: React.ReactNode;
  className?: string;
}

export default function StatCard({ label, value, sub, trend, icon, className }: StatCardProps) {
  return (
    <div
      className={clsx(
        "group relative overflow-hidden rounded-2xl border border-[hsl(var(--border))] bg-[hsl(var(--card))] p-5 shadow-sm transition-all duration-200 hover:shadow-md hover:-translate-y-0.5",
        className
      )}
    >
      {/* Decorative gradient blob */}
      <div className="absolute -right-4 -top-4 h-16 w-16 rounded-full bg-[hsl(var(--primary)/0.06)] transition-transform duration-300 group-hover:scale-125" />

      <div className="relative flex items-start justify-between">
        <div>
          <p className="text-[13px] font-medium text-[hsl(var(--muted-foreground))]">{label}</p>
          <p className="mt-1.5 text-[22px] font-bold tracking-tight text-[hsl(var(--foreground))]">
            {value}
          </p>
          {sub && (
            <div className="mt-1.5 flex items-center gap-1.5">
              {trend === "up" && (
                <svg className="h-3.5 w-3.5 text-[hsl(var(--success))]" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 19.5l15-15m0 0H8.25m11.25 0v11.25" />
                </svg>
              )}
              {trend === "down" && (
                <svg className="h-3.5 w-3.5 text-[hsl(var(--destructive))]" fill="none" viewBox="0 0 24 24" strokeWidth={2.5} stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" d="M4.5 4.5l15 15m0 0V8.25m0 11.25H8.25" />
                </svg>
              )}
              <p
                className={clsx(
                  "text-[12px] font-medium",
                  trend === "up" && "text-[hsl(var(--success))]",
                  trend === "down" && "text-[hsl(var(--destructive))]",
                  (!trend || trend === "neutral") && "text-[hsl(var(--muted-foreground))]"
                )}
              >
                {sub}
              </p>
            </div>
          )}
        </div>
        {icon && (
          <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-[hsl(var(--accent))] text-[hsl(var(--accent-foreground))]">
            {icon}
          </div>
        )}
      </div>
    </div>
  );
}
