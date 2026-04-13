/* ────────────────────────────────────────────────
   HeroSection - Light mode hero with heatmap
   ──────────────────────────────────────────────── */

"use client";

import { HeroHeatmap } from "./HeroHeatmap";
import { GradientButton } from "../ui";

interface HeroSectionProps {
  id: string;
}

const STATS = [
  { label: "Less Churn", value: "40%", delta: "vs baseline" },
  { label: "Emotion Accuracy", value: "85-95%", delta: "ML-powered" },
  { label: "Faster Winners", value: "2x", delta: "via A/B tests" },
];

export function HeroSection({ id }: HeroSectionProps) {
  const handleWatchDemo = () => {
    document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <section id={id} className="relative min-h-screen" style={{ background: "linear-gradient(180deg, #F0F4FF 0%, #F8F0FF 100%)" }}>
      <div className="max-w-[1200px] mx-auto px-6 pt-[120px] pb-20">
        {/* Two column layout */}
        <div className="grid lg:grid-cols-[55%_45%] gap-12 items-start mb-16">
          {/* Left Column */}
          <div className="space-y-6">
            {/* H1 */}
            <h1 className="text-[clamp(36px,4.5vw,56px)] font-bold leading-[1.1] tracking-tight font-sans">
              <span className="text-[#111318]">See Why Users Quit:</span>
              <br />
              <span className="bg-gradient-to-r from-[#007BFF] to-[#7C3AED] bg-clip-text text-transparent">
                AI Detects Confusion
              </span>
              <br />
              <span className="text-[#111318]">in Real-Time</span>
            </h1>

            {/* Subtext */}
            <p className="text-lg text-[#4B5563] leading-relaxed max-w-xl font-medium">
              Emotion ML + A/B Testing. No Setup. Instant Insights. Find the confusion killing your
              conversions in minutes, not months.
            </p>

            {/* CTA Buttons */}
            <div className="flex flex-wrap gap-4 pt-2">
              <GradientButton variant="primary" size="lg" glow href="/signup">
                Start Free Heatmap →
              </GradientButton>
              <GradientButton variant="outline" size="lg" onClick={handleWatchDemo}>
                Watch 60s Demo
              </GradientButton>
            </div>

            {/* Social proof */}
            <div className="flex items-center gap-3 pt-2">
              <div className="flex -space-x-2">
                <div className="w-8 h-8 rounded-full bg-[#007BFF] border-2 border-white flex items-center justify-center text-white text-xs font-bold">A</div>
                <div className="w-8 h-8 rounded-full bg-[#7C3AED] border-2 border-white flex items-center justify-center text-white text-xs font-bold">B</div>
                <div className="w-8 h-8 rounded-full bg-[#10B981] border-2 border-white flex items-center justify-center text-white text-xs font-bold">C</div>
              </div>
              <span className="text-sm text-[#4B5563]">
                <span className="font-semibold text-[#111318]">2,400+ teams</span> run emotion-powered tests
              </span>
            </div>
          </div>

          {/* Right Column - Heatmap with floating card */}
          <div className="relative mt-8">
            {/* Hero Heatmap */}
            <HeroHeatmap />

            {/* Floating +32% card */}
            <div className="absolute bottom-4 left-4 bg-white rounded-2xl p-4 shadow-lg max-w-[180px] z-10">
              <div className="text-[#10B981] text-[32px] font-bold leading-none">+32%</div>
              <div className="text-xs text-[#6B7280] mt-1 leading-tight">
                Conversions after fixing CTA confusion
              </div>
            </div>
          </div>
        </div>

        {/* Stat Cards - below columns in normal flow */}
        <div className="grid grid-cols-3 gap-6">
          {STATS.map((stat, index) => (
            <div
              key={index}
              className="bg-white rounded-2xl p-6 shadow-sm text-center border border-gray-100"
            >
              <div className="text-4xl font-bold text-[#111318] mb-1">{stat.value}</div>
              <div className="text-sm font-medium text-[#111318] mb-1">{stat.label}</div>
              <div className="text-xs text-[#6B7280]">{stat.delta}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
