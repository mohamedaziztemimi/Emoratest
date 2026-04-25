/* ────────────────────────────────────────
   TestimonialsSection - Use cases for different teams
   ──────────────────────────────────────── */

"use client";

import { GlassCard } from "../ui";

const USE_CASES = [
  {
    icon: "🚀",
    title: "Growth Teams",
    description: "Find the pages killing your conversion rate and fix them with data, not guesswork.",
  },
  {
    icon: "📊",
    title: "Product Managers",
    description: "Understand why users drop off at every step of your funnel with emotion-level detail.",
  },
  {
    icon: "🔍",
    title: "UX Researchers",
    description: "Replace hours of user interviews with automated emotion detection on every session.",
  },
];

export function TestimonialsSection() {
  return (
    <section className="py-24 bg-[var(--et-bg-900)]">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-[clamp(28px,4vw,42px)] font-bold text-[var(--et-text-primary)] mb-4">
            Built for teams who care about user experience
          </h2>
          <p className="text-[16px] text-[var(--et-text-muted)] max-w-2xl mx-auto leading-relaxed">
            EmoraTest helps you understand user emotions at scale — without surveys, interviews, or guesswork.
          </p>
        </div>

        {/* Use Cases Grid */}
        <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {USE_CASES.map((useCase, index) => (
            <GlassCard key={index} padding="lg" hover glow="blue">
              <div className="text-center">
                {/* Icon */}
                <div className="text-5xl mb-4">{useCase.icon}</div>

                {/* Title */}
                <h3 className="text-xl font-bold text-[var(--et-text-primary)] mb-3">
                  {useCase.title}
                </h3>

                {/* Description */}
                <p className="text-[15px] text-[var(--et-text-secondary)] leading-relaxed">
                  {useCase.description}
                </p>
              </div>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  );
}
