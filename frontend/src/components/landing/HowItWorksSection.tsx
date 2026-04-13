/* ────────────────────────────────────────────────
   HowItWorksSection - Interactive demo with emotion layers
   ──────────────────────────────────────────────── */

"use client";

import { useState } from "react";
import { GlassCard } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";

const STEPS = [
  {
    number: "01",
    title: "Install the Snippet",
    description: "Add one line of JavaScript. Works with any stack—React, Vue, vanilla, whatever.",
    tag: "2 min setup",
    color: "from-blue-500 to-cyan-500",
  },
  {
    number: "02",
    title: "Emotion ML Activates",
    description: "Our ML reads mouse patterns, rage-clicks, hesitation. 8 emotions classified in real-time.",
    tag: "Instant, automatic",
    color: "from-purple-500 to-pink-500",
  },
  {
    number: "03",
    title: "See the Why",
    description: "Dashboard shows exactly which pages trigger confusion—with revenue impact attached.",
    tag: "Live dashboard",
    color: "from-orange-500 to-red-500",
  },
  {
    number: "04",
    title: "Test and Win",
    description: "Launch AI-suggested variants. Watch conversion lift happen in days, not months.",
    tag: "50% faster winners",
    color: "from-green-500 to-emerald-500",
  },
];

interface HowItWorksSectionProps {
  id: string;
}

export function HowItWorksSection({ id }: HowItWorksSectionProps) {
  const [hoveredStep, setHoveredStep] = useState<number | null>(null);

  return (
    <section id={id} className="py-[100px] bg-gradient-to-b from-[#F8FAFC] to-white">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Header */}
        <FadeInOnScroll>
          <div className="text-center max-w-2xl mx-auto mb-16">
            <p className="text-sm font-semibold text-[#007BFF] tracking-widest uppercase mb-3">
              Interactive Demo
            </p>
            <h2 className="text-[clamp(32px,4vw,48px)] font-bold text-[#0A1628] mb-4">
              Hover to Reveal Emotion Layers
            </h2>
            <p className="text-lg text-[#475569]">
              See how EmoraTest exposes what users feel—step by step.
            </p>
          </div>
        </FadeInOnScroll>

        {/* Interactive Steps */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-16">
          {STEPS.map((step, index) => (
            <FadeInOnScroll key={index} delay={index * 100}>
              <div
                className="relative group cursor-pointer"
                onMouseEnter={() => setHoveredStep(index)}
                onMouseLeave={() => setHoveredStep(null)}
              >
                {/* Connector line */}
                {index < STEPS.length - 1 && (
                  <div className="hidden lg:block absolute top-12 left-full w-12 h-0.5 bg-gradient-to-r from-[#007BFF] to-transparent transition-opacity duration-300" />
                )}

                <div
                  className={`bg-white rounded-2xl p-6 border-2 transition-all duration-300 h-full ${
                    hoveredStep === index
                      ? "border-[#007BFF] shadow-xl -translate-y-2"
                      : "border-gray-100 shadow-sm hover:shadow-lg"
                  }`}
                >
                  {/* Animated gradient background on hover */}
                  {hoveredStep === index && (
                    <div className={`absolute inset-0 bg-gradient-to-br ${step.color} opacity-5 rounded-2xl animate-pulse-slow`} />
                  )}

                  {/* Step number */}
                  <div className={`text-5xl font-bold bg-gradient-to-br ${step.color} bg-clip-text text-transparent mb-4`}>
                    {step.number}
                  </div>

                  {/* Title */}
                  <h3 className="text-lg font-bold text-[#0A1628] mb-2">{step.title}</h3>

                  {/* Description */}
                  <p className="text-sm text-[#475569] leading-relaxed mb-4">{step.description}</p>

                  {/* Tag */}
                  <span
                    className={`inline-block px-3 py-1 rounded-full text-xs font-semibold bg-gradient-to-r ${step.color} text-white`}
                  >
                    {step.tag}
                  </span>

                  {/* Hover reveal - emotion insight */}
                  {hoveredStep === index && (
                    <div className="mt-4 pt-4 border-t border-gray-100 animate-fade-in">
                      <div className="flex items-center gap-2 text-sm">
                        <div className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                        <span className="font-medium text-[#0A1628]">Detecting emotions...</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            </FadeInOnScroll>
          ))}
        </div>

        {/* Interactive Preview Card */}
        <FadeInOnScroll delay={500}>
          <div className="bg-gradient-to-br from-[#0A1628] to-[#1E293B] rounded-3xl p-8 text-white relative overflow-hidden">
            {/* Scan line animation */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-[#007BFF] to-transparent animate-[ping-slow_3s_linear_infinite]" style={{ top: "20%" }} />
            </div>

            <div className="relative">
              <div className="flex items-center justify-between mb-6">
                <h3 className="text-xl font-bold">Interactive Preview</h3>
                <span className="px-3 py-1 rounded-full bg-green-500/20 text-green-400 text-xs font-semibold">
                  Live Demo
                </span>
              </div>

              <div className="grid md:grid-cols-2 gap-6">
                {/* Funnel visual */}
                <div className="bg-white/5 rounded-xl p-4">
                  <p className="text-xs text-white/60 mb-2">Your Funnel</p>
                  <div className="space-y-2">
                    <div className="h-8 bg-green-500/20 rounded flex items-center px-3 text-xs">
                      <span className="w-2 h-2 rounded-full bg-green-400 mr-2" />
                      Landing Page → 10,000 visitors
                    </div>
                    <div className="h-8 bg-yellow-500/20 rounded flex items-center px-3 text-xs">
                      <span className="w-2 h-2 rounded-full bg-yellow-400 mr-2 animate-pulse" />
                      Pricing → Confusion detected ⚠️
                    </div>
                    <div className="h-8 bg-red-500/20 rounded flex items-center px-3 text-xs">
                      <span className="w-2 h-2 rounded-full bg-red-400 mr-2" />
                      Checkout → 60% drop-off
                    </div>
                  </div>
                </div>

                {/* Test suggestion */}
                <div className="bg-white/5 rounded-xl p-4">
                  <p className="text-xs text-white/60 mb-2">AI Suggestion</p>
                  <div className="bg-gradient-to-r from-[#007BFF]/20 to-[#7C3AED]/20 rounded-lg p-3 border border-[#007BFF]/30">
                    <p className="text-sm font-semibold mb-1">Simplify CTA</p>
                    <p className="text-xs text-white/70">
                      Users show confusion on pricing. Test shorter copy.
                    </p>
                    <div className="mt-2 flex items-center gap-2">
                      <span className="text-xs text-green-400">+32% expected</span>
                      <button className="px-3 py-1 bg-[#007BFF] rounded text-xs font-semibold hover:bg-[#007BFF]/80 transition-colors">
                        Launch Test
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
