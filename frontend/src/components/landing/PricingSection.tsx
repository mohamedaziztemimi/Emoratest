/* ────────────────────────────────────────────────
   PricingSection - Light mode pricing tiers with animations
   ──────────────────────────────────────────────── */

"use client";

import { useState } from "react";
import { GradientButton } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";
import { WaitlistModal } from "../WaitlistModal";

interface PricingSectionProps {
  id: string;
}

const PRICING_TIERS = [
  {
    name: "Free",
    subtitle: "Get started with emotion tracking",
    price: "$0 / month",
    features: [
      "Up to 1,000 sessions per month",
      "1 active experiment",
      "Basic emotion detection (8 emotions)",
      "Session explorer with filters",
      "Email support",
    ],
    highlighted: false,
    ctaText: "Start Free",
    ctaVariant: "primary" as const,
    badge: null,
  },
  {
    name: "Growth",
    subtitle: "For teams serious about conversion",
    price: "$79 / month",
    features: [
      "Unlimited sessions",
      "Unlimited experiments",
      "Full emotion detection (8 emotions)",
      "Automatic diagnosis",
      "Emotion alerts (email + Slack)",
      "Page insights",
      "Priority support",
    ],
    highlighted: true,
    ctaText: "Join Waiting List",
    ctaVariant: "outline" as const,
    badge: "Coming Soon",
  },
  {
    name: "Scale",
    subtitle: "For growing companies",
    price: "$149 / month",
    features: [
      "Unlimited sessions",
      "Everything in Growth",
      "Slack integration",
      "Data export (CSV)",
      "Team members (up to 10)",
      "Dedicated support",
    ],
    highlighted: false,
    ctaText: "Join Waiting List",
    ctaVariant: "outline" as const,
    badge: "Coming Soon",
  },
];

export function PricingSection({ id }: PricingSectionProps) {
  const [showWaitlist, setShowWaitlist] = useState(false);

  return (
    <section id={id} className="py-[100px] pb-[120px]" style={{ background: "#F8F9FF" }}>
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Header */}
        <FadeInOnScroll>
          <div className="text-center mb-16">
            <p className="text-sm font-semibold text-[#007BFF] tracking-widest uppercase mb-3">
              PRICING
            </p>
            <h2 className="text-[clamp(32px,4vw,40px)] font-bold text-[#111318] mb-4">
              Pricing
            </h2>
            <p className="text-lg text-[#4B5563]">
              Free plan available now. Paid plans coming soon.
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
                {tier.badge && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                    <span className="bg-[#007BFF] text-white text-xs font-bold px-4 py-1 rounded-full">
                      {tier.badge}
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
                  href={tier.name === "Free" ? "/signup" : undefined}
                  className="w-full"
                  glow={tier.highlighted}
                  onClick={(e) => {
                    if (tier.name !== "Free") {
                      e.preventDefault();
                      setShowWaitlist(true);
                    }
                  }}
                >
                  {tier.ctaText}
                </GradientButton>

                {tier.name === "Growth" && (
                  <p className="text-xs text-[#6B7280] text-center mt-3">
                    We are in beta. Join the list for early access.
                  </p>
                )}
              </div>
            </FadeInOnScroll>
          ))}
        </div>

        {/* Footer note */}
        <div className="text-center flex items-center justify-center gap-2 text-sm text-[#6B7280]">
          <span>GDPR Compliant</span>
          <span className="w-1 h-1 rounded-full bg-gray-300"></span>
          <span>Made in Germany</span>
        </div>
      </div>

      {/* Waitlist Modal */}
      <WaitlistModal isOpen={showWaitlist} onClose={() => setShowWaitlist(false)} />
    </section>
  );
}
