"use client";

import { Component, ReactNode } from "react";

interface ErrorBoundaryProps {
  children: ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: any) {
    console.error("Heatmap ErrorBoundary caught an error:", error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
    return (
      <div className="flex items-center justify-center h-screen bg-[hsl(var(--background))]">
        <div className="text-center p-8">
          <div className="w-20 h-20 mx-auto mb-6 bg-red-100 rounded-full flex items-center justify-center">
            <svg className="w-10 h-10 text-red-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h-4m-4 4v6h4m-4-4h4" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-[hsl(var(--foreground))] mb-4">
            Something went wrong
          </h1>
          <p className="text-[hsl(var(--muted-foreground))] mb-6">
            {this.state.error?.message || "An unexpected error occurred while rendering the heatmap."}
          </p>
          <button
            onClick={() => window.location.reload()}
            className="px-6 py-3 bg-[hsl(var(--primary))] text-white rounded-lg hover:bg-[hsl(var(--primary-dark))] transition-colors"
          >
            Reload Page
          </button>
          <button
            onClick={() => (window.location.href = "/dashboard")}
            className="ml-4 px-6 py-3 bg-[hsl(var(--muted))] text-[hsl(var(--foreground))] rounded-lg hover:bg-[hsl(var(--accent))] transition-colors"
          >
            Back to Dashboard
          </button>
        </div>
      </div>
    );
    }

    return this.props.children;
  }
}
