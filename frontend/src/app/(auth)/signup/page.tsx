/* ────────────────────────────────────────────────
   Signup Page - Create a new EmoraTest account
   ──────────────────────────────────────────────── */

"use client";

import { useState } from "react";

interface FieldError {
  name?: string;
  email?: string;
  password?: string;
  workspaceName?: string;
}

export default function SignupPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [workspaceName, setWorkspaceName] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [fieldErrors, setFieldErrors] = useState<FieldError>({});

  const validateForm = (): boolean => {
    const errors: FieldError = {};

    if (!name.trim()) {
      errors.name = "Name is required";
    }

    if (!email.trim()) {
      errors.email = "Email is required";
    } else if (!email.includes("@")) {
      errors.email = "Please enter a valid email";
    }

    if (!password) {
      errors.password = "Password is required";
    } else if (password.length < 8) {
      errors.password = "Password must be at least 8 characters";
    }

    if (!workspaceName.trim()) {
      errors.workspaceName = "Workspace name is required";
    }

    setFieldErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSignup = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");

    if (!validateForm()) {
      return;
    }

    setLoading(true);

    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/auth/signup`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({
          name,
          email,
          password,
          workspace_name: workspaceName,
        }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || "Signup failed");
      }

      window.location.href = "/dashboard";
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full max-w-[440px]">
      {/* Logo */}
      <div className="flex items-center justify-center gap-2.5 mb-8">
        <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-[#007BFF] to-[#7C3AED] flex items-center justify-center text-white font-bold text-lg">
          E
        </div>
        <span className="text-xl font-bold bg-gradient-to-r from-[#007BFF] to-[#7C3AED] bg-clip-text text-transparent">
          EmoraTest
        </span>
      </div>

      {/* Card */}
      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-sm">
        {/* Header */}
        <div className="mb-6">
          <h2 className="text-2xl font-bold text-[#111318] mb-1">Start for free</h2>
          <p className="text-sm text-[#6B7280]">No credit card required. 2-min setup.</p>
        </div>

        {/* Error banner */}
        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSignup} className="space-y-4">
          {/* Full Name */}
          <div>
            <label htmlFor="name" className="block text-sm font-medium text-[#111318] mb-1.5">
              Full Name
            </label>
            <input
              id="name"
              type="text"
              placeholder="Your name"
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setFieldErrors((prev) => ({ ...prev, name: undefined }));
              }}
              className={`w-full px-4 py-2.5 rounded-lg border text-[#111318] placeholder:text-gray-400 focus:outline-none focus:ring-2 transition-colors ${
                fieldErrors.name
                  ? "border-red-300 focus:border-red-500 focus:ring-red-500/20"
                  : "border-gray-300 focus:border-[#007BFF] focus:ring-[#007BFF]/20"
              }`}
              disabled={loading}
            />
            {fieldErrors.name && <p className="mt-1 text-xs text-red-500">{fieldErrors.name}</p>}
          </div>

          {/* Work Email */}
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-[#111318] mb-1.5">
              Work Email
            </label>
            <input
              id="email"
              type="email"
              placeholder="you@company.com"
              value={email}
              onChange={(e) => {
                setEmail(e.target.value);
                setFieldErrors((prev) => ({ ...prev, email: undefined }));
              }}
              className={`w-full px-4 py-2.5 rounded-lg border text-[#111318] placeholder:text-gray-400 focus:outline-none focus:ring-2 transition-colors ${
                fieldErrors.email
                  ? "border-red-300 focus:border-red-500 focus:ring-red-500/20"
                  : "border-gray-300 focus:border-[#007BFF] focus:ring-[#007BFF]/20"
              }`}
              disabled={loading}
            />
            {fieldErrors.email && <p className="mt-1 text-xs text-red-500">{fieldErrors.email}</p>}
          </div>

          {/* Password */}
          <div>
            <label htmlFor="password" className="block text-sm font-medium text-[#111318] mb-1.5">
              Password
            </label>
            <input
              id="password"
              type="password"
              placeholder="Min. 8 characters"
              value={password}
              onChange={(e) => {
                setPassword(e.target.value);
                setFieldErrors((prev) => ({ ...prev, password: undefined }));
              }}
              className={`w-full px-4 py-2.5 rounded-lg border text-[#111318] placeholder:text-gray-400 focus:outline-none focus:ring-2 transition-colors ${
                fieldErrors.password
                  ? "border-red-300 focus:border-red-500 focus:ring-red-500/20"
                  : "border-gray-300 focus:border-[#007BFF] focus:ring-[#007BFF]/20"
              }`}
              disabled={loading}
            />
            {fieldErrors.password && <p className="mt-1 text-xs text-red-500">{fieldErrors.password}</p>}
          </div>

          {/* Workspace Name */}
          <div>
            <label htmlFor="workspace" className="block text-sm font-medium text-[#111318] mb-1.5">
              Workspace Name
            </label>
            <input
              id="workspace"
              type="text"
              placeholder="Your company name"
              value={workspaceName}
              onChange={(e) => {
                setWorkspaceName(e.target.value);
                setFieldErrors((prev) => ({ ...prev, workspaceName: undefined }));
              }}
              className={`w-full px-4 py-2.5 rounded-lg border text-[#111318] placeholder:text-gray-400 focus:outline-none focus:ring-2 transition-colors ${
                fieldErrors.workspaceName
                  ? "border-red-300 focus:border-red-500 focus:ring-red-500/20"
                  : "border-gray-300 focus:border-[#007BFF] focus:ring-[#007BFF]/20"
              }`}
              disabled={loading}
            />
            {fieldErrors.workspaceName && (
              <p className="mt-1 text-xs text-red-500">{fieldErrors.workspaceName}</p>
            )}
          </div>

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full py-3 rounded-lg bg-gradient-to-r from-[#007BFF] to-[#7C3AED] text-white font-semibold hover:brightness-110 disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {loading ? "Creating account..." : "Create Free Account"}
          </button>
        </form>

        {/* Sign in link */}
        <p className="mt-6 text-center text-sm text-[#6B7280]">
          Already have an account?{" "}
          <a href="/login" className="text-[#007BFF] font-semibold hover:underline">
            Sign in →
          </a>
        </p>
      </div>
    </div>
  );
}
