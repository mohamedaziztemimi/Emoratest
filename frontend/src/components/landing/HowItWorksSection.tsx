/* ────────────────────────────────────────────────
   HowItWorksSection - Timeline of 4 steps with animations
   ──────────────────────────────────────────────── */

"use client";

import { GlassCard } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";

const STEPS = [
  {
    number: "01",
    title: "Install the Snippet",
    description: "Add one script tag to your site. Works with HTML, React, Next.js, Vue, or any JavaScript framework. Takes 2 minutes.",
    tag: "2 min setup",
  },
  {
    number: "02",
    title: "Behavior Tracking Starts",
    description: "The SDK automatically tracks mouse movements, clicks, scroll patterns, rage clicks, and exit intent. No configuration needed.",
    tag: "Zero config",
  },
  {
    number: "03",
    title: "Emotions Are Detected",
    description: "Our XGBoost model analyzes behavior patterns and classifies each session into one of 8 emotions. Results appear on your dashboard within seconds of the session ending.",
    tag: "8 emotions detected",
  },
  {
    number: "04",
    title: "Take Action",
    description: "See which pages cause frustration, get automated diagnosis of issues, set up alerts, and run experiments (coming soon) — all from one dashboard.",
    tag: "Detect → Diagnose → Fix",
  },
];

const USE_CASES = [
  {
    title: "Growth Teams",
    description: "Find the pages killing your conversion rate and fix them with data, not guesswork.",
    icon: "📈",
  },
  {
    title: "Product Managers",
    description: "Understand why users drop off at every step of your funnel with emotion-level detail.",
    icon: "🎯",
  },
  {
    title: "UX Researchers",
    description: "Replace hours of user interviews with automated emotion detection on every session.",
    icon: "🔍",
  },
];

interface HowItWorksSectionProps {
  id: string;
}

export function HowItWorksSection({ id }: HowItWorksSectionProps) {
  return (
    <section id={id} className="py-[100px]" style={{ background: "#F8F9FF" }}>
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Header */}
        <FadeInOnScroll>
          <div className="text-center max-w-2xl mx-auto mb-16">
            <p className="text-sm font-semibold text-[#007BFF] tracking-widest uppercase mb-3">
              How It Works
            </p>
            <h2 className="text-[clamp(32px,4vw,40px)] font-bold text-[#111318] mb-4">
              How It Works
            </h2>
            <p className="text-lg text-[#4B5563]">
              Set up in 2 minutes. Get insights in hours.
            </p>
          </div>
        </FadeInOnScroll>

        {/* Steps timeline */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {STEPS.map((step, index) => (
            <FadeInOnScroll key={index} delay={index * 150}>
              <div className="relative">
                {/* Connector line (desktop only) */}
                {index < STEPS.length - 1 && (
                  <div className="hidden md:block absolute top-12 left-full w-12 h-0.5 bg-gradient-to-r from-[#007BFF] to-transparent" />
                )}

                <GlassCard padding="lg" className="bg-white h-full border-gray-200">
                  {/* Step number */}
                  <div className="text-5xl font-bold bg-gradient-to-br from-[#007BFF] to-[#7C3AED] bg-clip-text text-transparent mb-4">
                    {step.number}
                  </div>

                  {/* Title */}
                  <h3 className="text-xl font-bold text-[#111318] mb-3">
                    {step.title}
                  </h3>

                  {/* Description */}
                  <p className="text-base text-[#4B5563] leading-relaxed mb-4">
                    {step.description}
                  </p>

                  {/* Tag */}
                  <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold text-[#007BFF] bg-blue-100">
                    {step.tag}
                  </span>
                </GlassCard>
              </div>
            </FadeInOnScroll>
          ))}
        </div>

        {/* Use case cards */}
        <div className="text-center mb-8">
          <h3 className="text-2xl font-bold text-[#111318] mb-2">
            Built for teams who care about user experience
          </h3>
        </div>
        <div className="grid md:grid-cols-3 gap-6">
          {USE_CASES.map((useCase, index) => (
            <FadeInOnScroll key={index} delay={600 + index * 150}>
              <GlassCard padding="lg" className="bg-white border-gray-200 text-center">
                {/* Icon */}
                <div className="text-4xl mb-4">{useCase.icon}</div>

                {/* Title */}
                <h4 className="text-lg font-bold text-[#111318] mb-3">
                  {useCase.title}
                </h4>

                {/* Description */}
                <p className="text-sm text-[#4B5563] leading-relaxed">
                  {useCase.description}
                </p>
              </GlassCard>
            </FadeInOnScroll>
          ))}
        </div>
      </div>
    </section>
  );
}
