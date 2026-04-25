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
  { label: "Detect 8 Emotions", value: "Real-Time", delta: "From mouse behavior patterns" },
  { label: "80%+ Accuracy", value: "XGBoost", delta: "ML classifier" },
  { label: "Works Everywhere", value: "One Tag", delta: "Any website" },
];

export function HeroSection({ id }: HeroSectionProps) {
  const handleWatchDemo = () => {
    document.getElementById("how-it-works")?.scrollIntoView({ behavior: "smooth", block: "start" });
  };

  return (
    <section id={id} className="relative" style={{ background: "linear-gradient(180deg, #F0F4FF 0%, #F8F0FF 100%)", paddingTop: "clamp(80px, 12vw, 140px)", paddingBottom: "60px" }}>
      <div className="max-w-[1200px] mx-auto px-4 sm:px-6">
        {/* Two column layout - single column on mobile, two columns on lg+ */}
        <div className="grid grid-cols-1 lg:grid-cols-[55%_45%] gap-10 lg:gap-16 items-center w-full">
          {/* Left Column */}
          <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
            {/* H1 */}
            <h1 style={{ fontSize: "clamp(32px, 3.5vw, 52px)", fontWeight: 700, lineHeight: 1.05, margin: 0 }}>
              <span style={{ color: "#111318" }}>See What Your Users </span>
              <span style={{
                background: "linear-gradient(135deg, #007BFF, #7C3AED)",
                WebkitBackgroundClip: "text",
                WebkitTextFillColor: "transparent",
                backgroundClip: "text",
              }}>Actually Feel.</span>
            </h1>

            {/* Subtext */}
            <p style={{ fontSize: "18px", color: "#4B5563", maxWidth: "480px", lineHeight: 1.7, margin: 0, marginBottom: 0 }}>
              EmoraTest detects 8 emotions from mouse behavior including frustration, confusion, delight, and more. Find your conversion killer in hours, not weeks.
            </p>

            {/* CTA Buttons */}
            <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", alignItems: "center" }}>
              <GradientButton variant="primary" size="lg" glow href="/signup">
                Start Free. No Credit Card
              </GradientButton>
              <GradientButton variant="outline" size="lg" onClick={handleWatchDemo}>
                See How It Works
              </GradientButton>
            </div>

            {/* Social proof - honest */}
            <div style={{ marginTop: "4px" }}>
              <p className="text-[14px] text-[#4B5563] font-medium">
                Built for growth teams, PMs, and CRO leads at SaaS and e-commerce companies
              </p>
              <p className="text-[12px] text-[#6B7280] mt-1">
                Currently in free beta. No credit card required.
              </p>
            </div>
          </div>

          {/* Right Column - Heatmap with floating card */}
          <div className="relative">
            {/* Hero Heatmap */}
            <HeroHeatmap />

            {/* Floating feature highlight card */}
            <div className="absolute -top-3 -left-3 bg-white rounded-2xl p-4 shadow-lg max-w-[180px] z-10 border border-gray-100">
              <div className="text-[#007BFF] text-[28px] font-bold leading-none">8 Emotions</div>
              <div className="text-xs text-[#6B7280] mt-1 leading-tight">
                Detected from mouse behavior
              </div>
            </div>
          </div>
        </div>

        {/* Stat Cards - below columns in normal flow */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 sm:gap-6" style={{ marginTop: "32px" }}>
          {STATS.map((stat, index) => (
            <div
              key={index}
              className="bg-white/80 backdrop-blur-sm rounded-2xl p-6 shadow-sm text-center border border-gray-100 hover:shadow-md transition-shadow duration-300"
            >
              <div className="text-4xl font-bold bg-gradient-to-r from-[#007BFF] to-[#7C3AED] bg-clip-text text-transparent mb-1">{stat.value}</div>
              <div className="text-sm font-semibold text-[#111318] mb-1">{stat.label}</div>
              <div className="text-xs text-[#6B7280]">{stat.delta}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
