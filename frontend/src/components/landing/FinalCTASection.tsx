/* ────────────────────────────────────────────────
   FinalCTASection - Bottom conversion section with animation
   ──────────────────────────────────────────────── */

"use client";

import { GradientButton } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";

export function FinalCTASection() {
  return (
    <section className="py-[100px] relative overflow-hidden">
      {/* Gradient background */}
      <div
        className="absolute inset-0 -z-10"
        style={{
          background: "linear-gradient(135deg, #007BFF 0%, #7C3AED 100%)",
        }}
      />

      <div className="max-w-[1200px] mx-auto px-6 text-center">
        <FadeInOnScroll>
          <h2 className="text-[clamp(32px,4vw,48px)] font-bold text-white mb-6">
            Ready to See What Your Users Actually Feel?
          </h2>
          <p className="text-lg text-white/80 mb-10 max-w-2xl mx-auto">
            Join 2,400+ growth teams who stopped guessing and started winning with emotion-powered testing.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row gap-4 items-center justify-center mb-8">
            <a
              href="/signup"
              className="px-8 py-4 rounded-full bg-white text-[#007BFF] font-bold text-base hover:bg-white/90 transition-colors duration-200 whitespace-nowrap"
            >
              Start Free — No Credit Card
            </a>
            <a
              href="/demo"
              className="px-8 py-4 rounded-full bg-transparent border-2 border-white text-white font-bold text-base hover:bg-white/10 transition-colors duration-200 whitespace-nowrap"
            >
              Book a Demo
            </a>
          </div>

          {/* Checkmarks */}
          <p className="text-sm text-white flex items-center justify-center gap-4 flex-wrap">
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 001.414 1.414z" clipRule="evenodd" />
              </svg>
              Free forever plan
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 001.414 1.414z" clipRule="evenodd" />
              </svg>
              2-min setup
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 001.414 1.414z" clipRule="evenodd" />
              </svg>
              No credit card
            </span>
            <span className="flex items-center gap-1">
              <svg className="w-4 h-4 text-green-400" fill="currentColor" viewBox="0 0 20 20">
                <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 001.414 1.414z" clipRule="evenodd" />
              </svg>
              Cancel anytime
            </span>
          </p>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
