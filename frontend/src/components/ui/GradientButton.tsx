/* ────────────────────────────────────────────────
   GradientButton - Multi-variant gradient button
   ──────────────────────────────────────────────── */

"use client";

import { clsx } from "clsx";
import { ButtonHTMLAttributes, ReactNode, forwardRef } from "react";

type ButtonVariant = "primary" | "outline" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

interface GradientButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  glow?: boolean;
  loading?: boolean;
  href?: string;
}

const sizeClasses: Record<ButtonSize, string> = {
  sm: "px-3 py-1.5 text-sm",
  md: "px-4 py-2 text-base",
  lg: "px-6 py-3 text-lg",
};

const loaderSizes: Record<ButtonSize, string> = {
  sm: "w-3 h-3 border-2",
  md: "w-4 h-4 border-2",
  lg: "w-5 h-4 border-3",
};

export const GradientButton = forwardRef<HTMLButtonElement, GradientButtonProps>(
  (
    {
      children,
      variant = "primary",
      size = "md",
      glow = false,
      loading = false,
      href,
      className,
      disabled,
      onClick,
      ...props
    },
    ref
  ) => {
    const baseClasses = clsx(
      "relative inline-flex items-center justify-center",
      "font-medium rounded-full",
      "transition-all duration-200",
      "cursor-pointer",
      "disabled:cursor-not-allowed disabled:opacity-50",
      sizeClasses[size],
      glow && "hover:shadow-lg",
      className
    );

    const variantClasses: Record<ButtonVariant, string> = {
      primary: clsx(
        "text-white",
        "bg-gradient-to-r from-[#007BFF] to-[#7C3AED]",
        "hover:brightness-110"
      ),
      outline: clsx(
        "bg-gradient-to-r from-[#007BFF] to-[#7C3AED]",
        "[background-clip:text] text-transparent",
        "border border-gray-300",
        "hover:border-[#7C3AED]"
      ),
      ghost: clsx(
        "hover:bg-gray-100",
        "[background-clip:text] bg-gradient-to-r",
        "from-[#007BFF] to-[#7C3AED]",
        "text-transparent"
      ),
    };

    const Loader = () => (
      <div
        className={clsx(
          "border-white border-t-transparent rounded-full animate-spin mr-2",
          loaderSizes[size]
        )}
      />
    );

    if (href && !disabled) {
      return (
        <a
          href={href}
          className={clsx(baseClasses, variantClasses[variant])}
        >
          {loading && <Loader />}
          {children}
        </a>
      );
    }

    return (
      <button
        ref={ref}
        onClick={onClick}
        disabled={disabled || loading}
        className={clsx(baseClasses, variantClasses[variant])}
        {...props}
      >
        {loading && <Loader />}
        {children}
      </button>
    );
  }
);

GradientButton.displayName = "GradientButton";
