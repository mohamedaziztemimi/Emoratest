import clsx from "clsx";

type Variant = "default" | "success" | "warning" | "destructive" | "outline";

interface BadgeProps {
  children: React.ReactNode;
  variant?: Variant;
  className?: string;
}

const VARIANT_CLASSES: Record<Variant, string> = {
  default: "bg-[hsl(var(--secondary))] text-[hsl(var(--secondary-foreground))]",
  success: "bg-[hsl(var(--success)/0.12)] text-[hsl(var(--success))]",
  warning: "bg-[hsl(var(--warning)/0.12)] text-[hsl(var(--warning))]",
  destructive: "bg-[hsl(var(--destructive)/0.12)] text-[hsl(var(--destructive))]",
  outline: "border border-[hsl(var(--border))] text-[hsl(var(--muted-foreground))]",
};

export default function Badge({ children, variant = "default", className }: BadgeProps) {
  return (
    <span
      className={clsx(
        "inline-flex items-center rounded-lg px-2.5 py-1 text-[11px] font-semibold tracking-wide",
        VARIANT_CLASSES[variant],
        className
      )}
    >
      {children}
    </span>
  );
}
