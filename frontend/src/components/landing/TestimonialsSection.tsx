/* ────────────────────────────────────────
   TestimonialsSection - Customer reviews and social proof
   ──────────────────────────────────────── */

"use client";

import { GlassCard } from "../ui";
import { StarRating } from "../ui/StarRating";

const TESTIMONIALS = [
  {
    name: "Sarah Chen",
    role: "Head of Growth, ShopFlow",
    avatar: "SC",
    text: "EmoraTest cut our experiment cycle time by 80%. We went from guessing to knowing what moves is needle. The emotion heatmap feature is exactly what we needed to identify friction points we were missing.",
    rating: 5,
  },
  {
    name: "Marcus Johnson",
    role: "VP of Product, Taskly",
    avatar: "MJ",
    text: "The emotion heatmap is like having a user researcher watching every single session, at scale. We identified a 23% conversion drop-off on our checkout that was caused by confusion, and EmoraTest ML models helped us pinpoint exactly where.",
    rating: 5,
  },
  {
    name: "Jessica Torres",
    role: "CRO Lead, Retailify",
    avatar: "JT",
    text: "After implementing EmoraTest, our A/B test win rate went from 15% to 42%. The emotional insights helped us understand not just IF users converted, but WHY they did or didn't.",
    rating: 5,
  },
  {
    name: "David Park",
    role: "Founder, StartupXYZ",
    avatar: "DP",
    text: "We integrated EmoraTest in a weekend and saw immediate value. Confusion dropped 34% in the first week, and our team could iterate 3x faster on fixes. Game changer for our growth strategy.",
    rating: 5,
  },
  {
    name: "Emily Watson",
    role: "PM Manager, CloudScale",
    avatar: "EW",
    text: "The segmentation feature is brilliant. We can run targeted tests for different user personas and see which emotional responses are driving outcomes. This alone saved us weeks of manual analysis.",
    rating: 5,
  },
  {
    name: "Michael Lee",
    role: "Engineering Lead, TechFlow",
    avatar: "ML",
    text: "Finally, an emotion analytics tool that actually works. The ML predictions match our user feedback surveys within 85% accuracy. The dashboard is intuitive and insights are actionable.",
    rating: 5,
  },
];

export function TestimonialsSection() {
  return (
    <section className="py-24 bg-[var(--et-bg-900)]">
      <div className="container mx-auto px-4">
        {/* Section Header */}
        <div className="text-center mb-16">
          <h2 className="text-[clamp(28px,4vw,42px)] font-bold text-[var(--et-text-primary)] mb-4">
            Loved by 2,400+ Teams
          </h2>
          <p className="text-[16px] text-[var(--et-text-muted)] max-w-2xl mx-auto leading-relaxed">
            See why product and growth teams trust EmoraTest to understand user emotions and optimize conversions.
          </p>
        </div>

        {/* Testimonials Grid */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {TESTIMONIALS.map((testimonial, index) => (
            <GlassCard key={index} padding="lg" hover glow="blue">
              <div className="flex gap-4">
                {/* Avatar */}
                <div className="shrink-0 w-14 h-14 rounded-full bg-gradient-to-br from-[var(--et-blue)] to-[var(--et-purple)] flex items-center justify-center text-white font-bold text-lg">
                  {testimonial.avatar}
                </div>

                {/* Content */}
                <div className="flex-1">
                  <div className="mb-3">
                    <div className="font-semibold text-[var(--et-text-primary)] text-lg">
                      {testimonial.name}
                    </div>
                    <div className="text-[13px] text-[var(--et-text-muted)]">
                      {testimonial.role}
                    </div>
                  </div>

                  {/* Quote */}
                  <p className="text-[15px] text-[var(--et-text-secondary)] leading-relaxed mb-4 italic">
                    {testimonial.text}
                  </p>

                  {/* Rating */}
                  <div className="flex items-center gap-1">
                    <StarRating rating={testimonial.rating} />
                  </div>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>

        {/* Trust Indicators */}
        <div className="mt-16 grid grid-cols-2 md:grid-cols-4 gap-8 text-center">
          <div>
            <div className="text-4xl font-bold text-[var(--et-text-primary)] mb-2">
              2,400+
            </div>
            <div className="text-[13px] text-[var(--et-text-muted)]">
              Teams using EmoraTest
            </div>
          </div>
          <div>
            <div className="text-4xl font-bold text-[var(--et-text-primary)] mb-2">
              99.9%
            </div>
            <div className="text-[13px] text-[var(--et-text-muted)]">
              Uptime guaranteed
            </div>
          </div>
          <div>
            <div className="text-4xl font-bold text-[var(--et-satisfaction)] mb-2">
              85%
            </div>
            <div className="text-[13px] text-[var(--et-text-muted)]">
              Accuracy rate
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
