/* ────────────────────────────────────────────────
   HeroSection - Emotion-optimized hero with animations
   ──────────────────────────────────────────────── */

"use client";

import { useState, useEffect } from "react";
import { HeroHeatmap } from "./HeroHeatmap";
import { GradientButton } from "../ui";

interface HeroSectionProps {
  id: string;
}

const STATS = [
  { label: "Churn Reduction", value: "40%", delta: "Average lift" },
  { label: "Emotion Accuracy", value: "90%", delta: "ML-powered" },
  { label: "Tests Run", value: "10K+", delta: "And counting" },
];

export function HeroSection({ id }: HeroSectionProps) {
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    setIsLoaded(true);
  }, []);

  const handleWatchDemo = () => {
    document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <section id={id} className="relative min-h-screen overflow-hidden" style={{ background: "linear-gradient(180deg, #F8FAFC 0%, #F0F4FF 50%, #F8F0FF 100%)" }}>
      {/* Animated background blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-20 right-0 w-[600px] h-[600px] bg-blue-500/5 rounded-full blur-3xl animate-float_6s_ease-in-out_infinite" />
        <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-purple-500/5 rounded-full blur-3xl animate-float_6s_ease-in-out_infinite" style={{ animationDelay: "2s" }} />
      </div>

      <div className="max-w-[1280px] mx-auto px-6 pt-[120px] pb-20 relative">
        {/* Two column layout */}
        <div className="grid lg:grid-cols-[50%_50%] gap-10 items-center mb-16">
          {/* Left Column */}
          <div className={`space-y-8 transition-all duration-700 ${isLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
            {/* Badge pill - updated */}
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full border border-[#007BFF]/20 bg-white/80 backdrop-blur-sm shadow-sm">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#007BFF] opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-[#007BFF]"></span>
              </span>
              <span className="text-sm font-semibold text-[#007BFF]">AI-Powered Emotion Detection</span>
            </div>

            {/* H1 - no colon, updated copy */}
            <h1 className="text-[clamp(40px,5vw,64px)] font-bold leading-[1.05] tracking-tight">
              <span className="text-[#0A1628]">Decode Why Users Quit</span>
              <br />
              <span className="bg-gradient-to-r from-[#007BFF] via-[#3B82F6] to-[#7C3AED] bg-clip-text text-transparent">
                AI Spots Confusion
              </span>
              <br />
              <span className="text-[#0A1628]">→ Unlock 32% More Conversions</span>
            </h1>

            {/* Subtext - updated */}
            <p className="text-xl text-[#475569] leading-relaxed max-w-xl">
              Emotion-Powered A/B Testing. No Setup. Instant Clarity. Find the frustration killing your funnel—before it kills your revenue.
            </p>

            {/* CTA Buttons - updated labels */}
            <div className="flex flex-wrap gap-4 pt-2">
              <GradientButton variant="primary" size="lg" glow href="/signup" className="px-8 py-4 text-base">
                Start Free Heatmap
              </GradientButton>
              <GradientButton variant="outline" size="lg" onClick={handleWatchDemo} className="px-8 py-4 text-base">
                See Live Demo
              </GradientButton>
            </div>

            {/* Social proof - enhanced */}
            <div className="flex items-center gap-4 pt-4">
              <div className="flex -space-x-3">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#007BFF] to-[#3B82F6] border-3 border-white flex items-center justify-center text-white text-sm font-bold shadow-lg">A</div>
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#7C3AED] to-[#A855F7] border-3 border-white flex items-center justify-center text-white text-sm font-bold shadow-lg">J</div>
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#10B981] to-[#34D399] border-3 border-white flex items-center justify-center text-white text-sm font-bold shadow-lg">T</div>
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-[#F59E0B] to-[#FBBF24] border-3 border-white flex items-center justify-center text-white text-sm font-bold shadow-lg">R</div>
              </div>
              <div className="text-sm text-[#475569]">
                <span className="font-bold text-[#0A1628]">2,400+ teams</span> stopped guessing
              </div>
            </div>
          </div>

          {/* Right Column - Heatmap aligned with headline */}
          <div className={`relative transition-all duration-700 delay-200 ${isLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
            {/* Hero Heatmap */}
            <div className="relative">
              <HeroHeatmap />

              {/* Glow effect behind heatmap */}
              <div className="absolute inset-0 bg-gradient-to-br from-[#007BFF]/20 to-[#7C3AED]/20 rounded-3xl blur-2xl -z-10" />
            </div>

            {/* Floating +32% card - animated */}
            <div className="absolute bottom-6 left-6 bg-white rounded-2xl p-5 shadow-xl max-w-[200px] z-10 animate-bounce-slight border border-gray-100/50">
              <div className="flex items-center gap-2 mb-1">
                <div className="w-8 h-8 rounded-lg bg-green-100 flex items-center justify-center">
                  <svg className="w-5 h-5 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M5 10l7-7m0 0l7 7m-7-7v18" />
                  </svg>
                </div>
              </div>
              <div className="text-[#10B981] text-[36px] font-bold leading-none">+32%</div>
              <div className="text-sm text-[#64748B] mt-1 leading-tight font-medium">
                Conversions after fixing confusion
              </div>
            </div>

            {/* Secondary floating card - new */}
            <div className="absolute top-4 right-4 bg-white rounded-xl p-3 shadow-lg max-w-[160px] z-10 animate-float_6s_ease-in-out_infinite">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse"></div>
                <span className="text-xs font-semibold text-[#64748B]">Detected</span>
              </div>
              <div className="text-sm font-bold text-[#0A1628] mt-1">Confusion on CTA</div>
              <div className="text-xs text-[#94A3B8]">3 users affected</div>
            </div>
          </div>
        </div>

        {/* Stat Cards - enhanced design */}
        <div className={`grid grid-cols-3 gap-6 transition-all duration-700 delay-400 ${isLoaded ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"}`}>
          {STATS.map((stat, index) => (
            <div
              key={index}
              className="group bg-white rounded-2xl p-6 shadow-sm text-center border border-gray-100 hover:shadow-lg hover:border-[#007BFF]/30 transition-all duration-300 hover:-translate-y-1"
            >
              <div className="text-5xl font-bold bg-gradient-to-br from-[#007BFF] to-[#7C3AED] bg-clip-text text-transparent mb-2">
                {stat.value}
              </div>
              <div className="text-sm font-semibold text-[#0A1628] mb-1">{stat.label}</div>
              <div className="text-xs text-[#64748B]">{stat.delta}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
