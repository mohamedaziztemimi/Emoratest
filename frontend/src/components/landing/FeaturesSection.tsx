/* ────────────────────────────────────────────────
   FeaturesSection - Feature cards grid with animations
   ──────────────────────────────────────────────── */

"use client";

import { GlassCard } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";

const FEATURES = [
  {
    icon: "🔥",
    title: "Page Insights",
    description: "See which pages cause frustration, confusion, or delight. Every page ranked by emotional friction with actionable breakdowns.",
  },
  {
    icon: "🧠",
    title: "8-Emotion ML Classifier",
    description: "Our XGBoost model detects confusion, frustration, delight, anxiety, hesitation, focus, boredom, and satisfaction from mouse behavior with 80%+ accuracy. No cameras. No surveys. Just behavior.",
  },
  {
    icon: "🔍",
    title: "Automatic Diagnosis",
    description: "EmoraTest automatically detects issues like rage clicks, hesitation spikes, and high drop-offs. It tells you exactly why users struggle and what to fix.",
  },
  {
    icon: "🎯",
    title: "Session Explorer",
    description: "Browse every user session with emotion labels. Filter by frustrated, confused, or satisfied sessions. Click into any session to see the full emotion breakdown and behavior signals.",
  },
  {
    icon: "📊",
    title: "Emotion Alerts",
    description: "Get notified when frustration spikes on any page. Set thresholds, choose your channel (email or Slack), and never miss a conversion-killing issue.",
  },
  {
    icon: "⚡",
    title: "Real-time Alerts",
    description: "Configure alerts for any emotion on any page. Set thresholds like 'email me when frustration exceeds 30% on checkout.' Works with email and Slack.",
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
              What you get
            </h2>
            <p className="text-lg text-[#4B5563]">
              Track emotions. Find problems. Fix them.
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
