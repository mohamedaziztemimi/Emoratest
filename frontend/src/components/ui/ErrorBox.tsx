interface ErrorBoxProps {
  message: string;
  onRetry?: () => void;
}

export default function ErrorBox({ message, onRetry }: ErrorBoxProps) {
  return (
    <div className="animate-scale-in rounded-2xl border border-[hsl(var(--destructive)/0.2)] bg-[hsl(var(--destructive)/0.06)] p-5">
      <div className="flex items-start gap-3">
        <div className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-[hsl(var(--destructive)/0.12)]">
          <svg className="h-4 w-4 text-[hsl(var(--destructive))]" fill="none" viewBox="0 0 24 24" strokeWidth={2} stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
          </svg>
        </div>
        <div>
          <p className="text-[13px] font-medium text-[hsl(var(--destructive))]">Something went wrong</p>
          <p className="mt-1 text-[12px] text-[hsl(var(--muted-foreground))]">{message}</p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-3 rounded-lg bg-[hsl(var(--destructive))] px-3.5 py-1.5 text-[12px] font-medium text-white transition-colors hover:bg-[hsl(var(--destructive)/0.9)]"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
