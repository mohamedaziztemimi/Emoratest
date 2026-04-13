/* ────────────────────────────────────────────────
   PricingSection - Light mode pricing tiers with animations
   ──────────────────────────────────────────────── */

"use client";

import { GradientButton } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";

interface PricingSectionProps {
  id: string;
}

const PRICING_TIERS = [
  {
    name: "STARTER",
    subtitle: "Perfect for individuals and small teams",
    price: "$0 / month",
    features: [
      "Up to 5,000 sessions/month",
      "3 active experiments",
      "Basic emotion heatmaps",
      "A/B testing",
      "Email support",
    ],
    highlighted: false,
    ctaText: "Start Free",
    ctaVariant: "outline" as const,
  },
  {
    name: "GROWTH",
    subtitle: "For growing teams serious about conversion",
    price: "$79 / month",
    features: [
      "Up to 100,000 sessions/month",
      "Unlimited experiments",
      "Full emotion ML (8 emotions)",
      "Multi-armed bandits",
      "Why-analysis & revenue linking",
      "Slack & Jira integrations",
      "Priority support",
    ],
    highlighted: true,
    ctaText: "Start Free Trial",
    ctaVariant: "primary" as const,
  },
  {
    name: "ENTERPRISE",
    subtitle: "For large teams needing scale and compliance",
    price: "Custom pricing",
    features: [
      "Unlimited sessions",
      "HIPAA & GDPR compliance",
      "SSO & advanced permissions",
      "Snowflake / BigQuery sync",
      "SLA guarantee",
      "Dedicated success manager",
      "Custom ML training",
    ],
    highlighted: false,
    ctaText: "Book a Demo",
    ctaVariant: "outline" as const,
  },
];

export function PricingSection({ id }: PricingSectionProps) {
  return (
    <section id={id} className="py-[100px]" style={{ background: "#F8F9FF" }}>
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Header */}
        <FadeInOnScroll>
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-[#007BFF] tracking-widest uppercase mb-3">
              PRICING
            </p>
            <h2 className="text-[clamp(32px,4vw,40px)] font-bold text-[#111318] mb-4">
              Simple, Transparent Pricing
            </h2>
            <p className="text-lg text-[#4B5563]">
              Start free. Scale as you grow. No hidden fees.
            </p>
          </div>
        </FadeInOnScroll>

        {/* Pricing Cards */}
        <div className="grid md:grid-cols-3 gap-6 mb-12">
          {PRICING_TIERS.map((tier, index) => (
            <FadeInOnScroll key={tier.name} delay={index * 150}>
              <div
                className={`
                  bg-white rounded-2xl p-8 border transition-all duration-300
                  ${tier.highlighted
                    ? "border-[#007BFF] shadow-xl relative scale-105"
                    : "border-gray-200 hover:shadow-lg"
                  }
                `}
              >
                {tier.highlighted && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-gradient-to-r from-[#007BFF] to-[#7C3AED] text-white text-xs font-bold px-4 py-1 rounded-full">
                      MOST POPULAR
                    </span>
                  </div>
                )}

                <div className="text-center mb-6">
                  <h3 className="text-lg font-bold text-[#111318] mb-2">{tier.name}</h3>
                  <p className="text-sm text-[#4B5563] mb-4">{tier.subtitle}</p>
                  <div className="text-4xl font-bold text-[#111318]">{tier.price}</div>
                </div>

                <ul className="space-y-3 mb-8">
                  {tier.features.map((feature, idx) => (
                    <li key={idx} className="flex items-start gap-2 text-sm">
                      <span className="text-[#10B981] font-bold shrink-0">✓</span>
                      <span className="text-[#4B5563]">{feature}</span>
                    </li>
                  ))}
                </ul>

                <GradientButton
                  variant={tier.ctaVariant}
                  size="md"
                  href={tier.name === "ENTERPRISE" ? "/demo" : "/signup"}
                  className="w-full"
                  glow={tier.highlighted}
                >
                  {tier.ctaText}
                </GradientButton>
              </div>
            </FadeInOnScroll>
          ))}
        </div>

        {/* Footer note */}
        <p className="text-center text-sm text-[#6B7280]">
          All plans include a 14-day free trial. No credit card required.
        </p>
      </div>
    </section>
  );
}
