/* ────────────────────────────────────────────────
   FeaturesSection - Feature cards grid with animations
   ──────────────────────────────────────────────── */

"use client";

import { GlassCard } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";

const FEATURES = [
  {
    icon: "🔥",
    title: "Emotion Heatmaps",
    description: "See where users feel confused, frustrated, or delighted on any page. Color-coded overlays update in real-time.",
  },
  {
    icon: "⚡",
    title: "A/B & Multivariate Testing",
    description: "Run A/B, MVT, split URL, and multi-page tests with flicker-free delivery and auto-stopping when winners emerge.",
  },
  {
    icon: "🎯",
    title: "Multi-Armed Bandits",
    description: "Automatically shift traffic to winning variants 30-50% faster than fixed splits using Thompson Sampling.",
  },
  {
    icon: "🧠",
    title: "8-Emotion ML Classifier",
    description: "Our ML detects confusion, frustration, delight, anxiety, hesitation, focus, boredom, and satisfaction with 85-95% accuracy.",
  },
  {
    icon: "🔍",
    title: "Why-Analysis",
    description: "Automatically links emotions to revenue. See exactly which confusion event caused a 34% drop-off — and what to fix.",
  },
  {
    icon: "🚩",
    title: "Feature Flags",
    description: "Progressive rollouts, kill switches, and targeting rules. Ship safely to segments based on emotional behavior.",
  },
];

interface FeaturesSectionProps {
  id: string;
}

export function FeaturesSection({ id }: FeaturesSectionProps) {
  return (
    <section id={id} className="py-[100px] bg-white">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Header */}
        <FadeInOnScroll>
          <div className="text-center max-w-2xl mx-auto mb-16">
            <p className="text-sm font-semibold text-[#007BFF] tracking-widest uppercase mb-3">
              Features
            </p>
            <h2 className="text-[clamp(32px,4vw,40px)] font-bold text-[#111318] mb-4">
              Everything You Need to Win
            </h2>
            <p className="text-lg text-[#4B5563]">
              From emotion detection to A/B testing — one platform, zero guesswork.
            </p>
          </div>
        </FadeInOnScroll>

        {/* Features grid with staggered animations */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {FEATURES.map((feature, index) => (
            <FadeInOnScroll key={index} delay={index * 100}>
              <GlassCard
                padding="lg"
                className="bg-white border border-gray-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              >
                {/* Icon */}
                <div className="text-4xl mb-4">{feature.icon}</div>

                {/* Title */}
                <h3 className="text-xl font-bold text-[#111318] mb-3">
                  {feature.title}
                </h3>

                {/* Description */}
                <p className="text-base text-[#4B5563] leading-relaxed">
                  {feature.description}
                </p>
              </GlassCard>
            </FadeInOnScroll>
          ))}
        </div>
      </div>
    </section>
  );
}
