/* ────────────────────────────────────────────────
   IntegrationsSection - Integration cards with animations
   ──────────────────────────────────────────────── */

"use client";

import { GlassCard } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";

const INTEGRATIONS = [
  {
    name: "Amplitude",
    description: "Sync experiment exposures and emotion events to your Amplitude workspace automatically.",
  },
  {
    name: "PostHog",
    description: "Send emotion signals and A/B results to PostHog for unified product analytics.",
  },
  {
    name: "Slack",
    description: "Get instant alerts when frustration spikes or a test reaches significance.",
  },
  {
    name: "Jira",
    description: "Auto-create tickets for high-frustration pages detected by EmoraTest.",
  },
  {
    name: "Snowflake",
    description: "Stream all experiment and emotion data to your Snowflake warehouse in real-time.",
  },
  {
    name: "BigQuery",
    description: "Full data export to BigQuery for custom analysis and BI dashboards.",
  },
];

const COMPLIANCE = [
  { icon: "🔒", text: "GDPR Compliant" },
  { icon: "🏥", text: "HIPAA Ready" },
  { icon: "⚡", text: "99.9% Uptime SLA" },
];

interface IntegrationsSectionProps {
  id: string;
}

export function IntegrationsSection({ id }: IntegrationsSectionProps) {
  return (
    <section id={id} className="py-[100px] bg-white">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Header */}
        <FadeInOnScroll>
          <div className="text-center max-w-2xl mx-auto mb-16">
            <p className="text-sm font-semibold text-[#007BFF] tracking-widest uppercase mb-3">
              Integrations
            </p>
            <h2 className="text-[clamp(32px,4vw,40px)] font-bold text-[#111318] mb-4">
              Works With Your Entire Stack
            </h2>
            <p className="text-lg text-[#4B5563]">
              Connect EmoraTest to tools your team already lives in.
            </p>
          </div>
        </FadeInOnScroll>

        {/* Integration cards */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6 mb-16">
          {INTEGRATIONS.map((integration, index) => (
            <FadeInOnScroll key={index} delay={index * 100}>
              <GlassCard
                padding="lg"
                className="bg-white border border-gray-200 hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              >
                {/* Logo placeholder */}
                <div className="text-3xl font-bold text-[#111318] mb-3">
                  {integration.name}
                </div>

                {/* Description */}
                <p className="text-base text-[#4B5563] leading-relaxed">
                  {integration.description}
                </p>
              </GlassCard>
            </FadeInOnScroll>
          ))}
        </div>

        {/* Compliance strip */}
        <FadeInOnScroll delay={600}>
          <div className="flex flex-wrap justify-center gap-6 md:gap-12">
            {COMPLIANCE.map((item, index) => (
              <div
                key={index}
                className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-50 border border-gray-200"
              >
                <span className="text-xl">{item.icon}</span>
                <span className="text-sm font-semibold text-[#374151]">{item.text}</span>
              </div>
            ))}
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
