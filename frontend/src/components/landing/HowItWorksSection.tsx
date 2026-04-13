/* ────────────────────────────────────────────────
   HowItWorksSection - Timeline of 4 steps
   ──────────────────────────────────────────────── */

"use client";

import { GlassCard, GradientButton } from "../ui";

const STEPS = [
  {
    number: "01",
    title: "Install the Snippet",
    description: "Add one line of JavaScript to your site. No engineering required. Works with any stack.",
    tag: "2 min setup",
  },
  {
    number: "02",
    title: "Emotion ML Activates",
    description: "Our ML immediately starts reading mouse patterns, rage-clicks, scroll hesitation, and dwell time to classify emotions in real-time.",
    tag: "Instant, automatic",
  },
  {
    number: "03",
    title: "See the Why",
    description: "Your dashboard shows exactly which pages trigger confusion or frustration, with revenue impact attached to every insight.",
    tag: "Live dashboard",
  },
  {
    number: "04",
    title: "Test and Win",
    description: "Launch AI-suggested variants targeting confused segments. Watch conversion lift happen in days, not months.",
    tag: "30-50% faster winners",
  },
];

const QUOTES = [
  {
    text: "EmoraTest found that 73% of our checkout abandonment was confusion-driven. Fixed it in one sprint.",
    name: "Sarah K.",
    role: "Head of Growth @ Series B SaaS",
    result: "$2.1M revenue recovered",
  },
  {
    text: "Finally a tool that tells me WHY users leave. Our UX team cut research time by 60%.",
    name: "Marcus T.",
    role: "Senior PM @ E-commerce Platform",
    result: "40% faster shipping",
  },
];

interface HowItWorksSectionProps {
  id: string;
}

export function HowItWorksSection({ id }: HowItWorksSectionProps) {
  return (
    <section id={id} className="py-[100px]" style={{ background: "#F8F9FF" }}>
      <div className="max-w-7xl mx-auto px-6">
        {/* Header */}
        <div className="text-center max-w-2xl mx-auto mb-16">
          <p className="text-sm font-semibold text-blue-600 tracking-widest uppercase mb-3">
            How It Works
          </p>
          <h2 className="text-[clamp(32px,4vw,40px)] font-bold text-gray-900 mb-4">
            From Confusion to Conversion in 4 Steps
          </h2>
          <p className="text-lg text-gray-600 leading-relaxed">
            Set up in 2 minutes. Insights in hours. Revenue lift in days.
          </p>
        </div>

        {/* Steps timeline */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {STEPS.map((step, index) => (
            <div key={index} className="relative">
              {/* Connector line (desktop only) */}
              {index < STEPS.length - 1 && (
                <div className="hidden md:block absolute top-12 left-full w-12 h-0.5 bg-gradient-to-r from-blue-500 to-transparent" />
              )}

              <GlassCard padding="lg" className="bg-white h-full border-gray-200">
                {/* Step number */}
                <div className="text-5xl font-bold bg-gradient-to-br from-blue-500 to-purple-600 bg-clip-text text-transparent mb-4">
                  {step.number}
                </div>

                {/* Title */}
                <h3 className="text-xl font-bold text-gray-900 mb-3">
                  {step.title}
                </h3>

                {/* Description */}
                <p className="text-base text-gray-600 leading-relaxed mb-4">
                  {step.description}
                </p>

                {/* Tag */}
                <span className="inline-block px-3 py-1 rounded-full text-xs font-semibold text-blue-600 bg-blue-100">
                  {step.tag}
                </span>
              </GlassCard>
            </div>
          ))}
        </div>

        {/* Customer quotes */}
        <div className="grid md:grid-cols-2 gap-6">
          {QUOTES.map((quote, index) => (
            <GlassCard key={index} padding="lg" className="bg-white border-gray-200">
              {/* Quote */}
              <p className="text-base text-gray-700 italic leading-relaxed mb-4">
                "{quote.text}"
              </p>

              {/* Attribution */}
              <div className="flex items-start justify-between gap-4">
                <div>
                  <p className="font-semibold text-gray-900">{quote.name}</p>
                  <p className="text-sm text-gray-600">{quote.role}</p>
                </div>
                <span className="px-3 py-1 rounded-full text-xs font-semibold text-green-600 bg-green-100 whitespace-nowrap">
                  {quote.result}
                </span>
              </div>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  );
}
