import clsx from "clsx";

export default function Spinner({ className }: { className?: string }) {
  return (
    <div className={clsx("flex items-center justify-center py-16", className)}>
      <div className="relative h-10 w-10">
        <div className="absolute inset-0 rounded-full border-[3px] border-[hsl(var(--border))]" />
        <div className="absolute inset-0 animate-spin rounded-full border-[3px] border-transparent border-t-[hsl(var(--primary))]" />
      </div>
    </div>
  );
}
