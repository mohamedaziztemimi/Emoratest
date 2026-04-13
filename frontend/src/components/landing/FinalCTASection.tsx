/* ────────────────────────────────────────────────
   FinalCTASection - Empowering conversion section
   ──────────────────────────────────────────────── */

"use client";

import { GradientButton } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";

export function FinalCTASection() {
  return (
    <section className="py-[120px] relative overflow-hidden">
      {/* Animated gradient background */}
      <div className="absolute inset-0 -z-10 bg-gradient-to-br from-[#007BFF] via-[#3B82F6] to-[#7C3AED] animate-gradient-shift" />

      {/* Animated blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-10 left-10 w-64 h-64 bg-white/10 rounded-full blur-3xl animate-float_6s_ease-in-out_infinite" />
        <div className="absolute bottom-10 right-10 w-80 h-80 bg-purple-500/20 rounded-full blur-3xl animate-float_6s_ease-in-out_infinite" style={{ animationDelay: "3s" }} />
      </div>

      <div className="max-w-[1000px] mx-auto px-6 text-center relative">
        <FadeInOnScroll>
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-white/10 backdrop-blur-sm border border-white/20 mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-green-400"></span>
            </span>
            <span className="text-sm font-semibold text-white">Limited Beta — 500 Spots</span>
          </div>

          {/* Headline - first-person, empowering */}
          <h2 className="text-[clamp(36px,5vw,56px)] font-bold text-white mb-6 leading-tight">
            Get My Free Emotion Audit
          </h2>
          <p className="text-xl text-white/90 mb-10 max-w-2xl mx-auto leading-relaxed">
            Stop guessing why users leave. See exactly where confusion kills your conversions—in 2 minutes flat.
          </p>

          {/* CTA Button */}
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-center mb-10">
            <GradientButton
              variant="primary"
              size="lg"
              glow
              href="/signup"
              className="px-10 py-5 text-lg bg-white text-[#007BFF] hover:bg-white/90"
            >
              Start Free Heatmap →
            </GradientButton>
          </div>

          {/* Trust signals */}
          <div className="flex flex-wrap items-center justify-center gap-6 text-white/90 text-sm">
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <span>Free forever plan</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <span>2-min setup</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <span>No credit card required</span>
            </div>
            <div className="flex items-center gap-2">
              <svg className="w-5 h-5 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
              </svg>
              <span>GDPR-ready</span>
            </div>
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
