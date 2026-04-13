/* ────────────────────────────────────────────────
   FeaturesSection - Pain-Agitation-Solution with emotion triggers
   ──────────────────────────────────────────────── */

"use client";

import { GlassCard } from "../ui";
import { FadeInOnScroll } from "./FadeInOnScroll";

const PAIN_POINTS = [
  { icon: "📊", text: "Clicks lie" },
  { icon: "🔥", text: "Heatmaps guess" },
  { icon: "❓", text: "Emotions explain drop-offs" },
];

const SOLUTIONS = [
  {
    icon: "🧠",
    emotion: "Relief",
    title: "Emotion ML",
    description: "Detect frustration in 100ms → Auto-fix variants before users leave",
    color: "from-green-500 to-emerald-500",
  },
  {
    icon: "⚡",
    emotion: "Empowerment",
    title: "A/B Bandits",
    description: "Real-time winners, 50% faster. Traffic shifts to what works automatically",
    color: "from-blue-500 to-cyan-500",
  },
  {
    icon: "🎯",
    emotion: "Insight",
    title: "Insights Dashboard",
    description: "Why + ROI in one view. See exactly which emotion drives revenue",
    color: "from-purple-500 to-pink-500",
  },
];

interface FeaturesSectionProps {
  id: string;
}

export function FeaturesSection({ id }: FeaturesSectionProps) {
  return (
    <section id={id} className="py-[100px] bg-gradient-to-b from-white to-[#F8FAFC]">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Pain Section */}
        <FadeInOnScroll>
          <div className="text-center mb-12">
            <h2 className="text-[clamp(28px,4vw,42px)] font-bold text-[#0A1628] mb-6">
              Clicks Lie. Heatmaps Guess.
              <span className="relative inline-block mx-2">
                <span className="bg-gradient-to-r from-[#007BFF] to-[#7C3AED] bg-clip-text text-transparent">
                  Emotions Explain Drop-offs.
                </span>
                <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-[#007BFF] to-[#7C3AED] rounded-full opacity-30" />
              </span>
            </h2>
          </div>
        </FadeInOnScroll>

        {/* Pain Icons */}
        <div className="grid grid-cols-3 gap-8 max-w-3xl mx-auto mb-16">
          {PAIN_POINTS.map((point, index) => (
            <FadeInOnScroll key={index} delay={index * 100}>
              <div className="text-center group">
                <div className="w-20 h-20 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-red-50 to-orange-50 flex items-center justify-center text-4xl group-hover:scale-110 transition-transform duration-300">
                  {point.icon}
                </div>
                <p className="font-semibold text-[#0A1628]">{point.text}</p>
              </div>
            </FadeInOnScroll>
          ))}
        </div>

        {/* Agitation - Video placeholder */}
        <FadeInOnScroll delay={300}>
          <div className="relative max-w-4xl mx-auto mb-16 rounded-3xl overflow-hidden shadow-2xl bg-gradient-to-br from-[#0A1628] to-[#1E293B]">
            <div className="aspect-video flex items-center justify-center">
              <div className="text-center text-white">
                <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-white/10 backdrop-blur-sm flex items-center justify-center cursor-pointer hover:bg-white/20 transition-colors group">
                  <svg className="w-8 h-8 ml-1 group-hover:scale-110 transition-transform" fill="currentColor" viewBox="0 0 24 24">
                    <path d="M8 5v14l11-7z" />
                  </svg>
                </div>
                <p className="text-lg font-semibold">Watch Confusion Kill Your Funnel in Real-Time</p>
                <p className="text-sm text-white/60 mt-2">15 seconds that changes everything</p>
              </div>
            </div>
            {/* Animated scan line */}
            <div className="absolute inset-0 pointer-events-none">
              <div className="h-[2px] w-full bg-gradient-to-r from-transparent via-[#007BFF] to-transparent animate-[ping-slow_3s_ease-in-out_infinite]" style={{ top: "30%" }} />
            </div>
          </div>
        </FadeInOnScroll>

        {/* Solution Cards */}
        <FadeInOnScroll delay={400}>
          <div className="text-center mb-12">
            <p className="text-sm font-semibold text-[#007BFF] tracking-widest uppercase mb-3">
              The Solution
            </p>
            <h2 className="text-[clamp(32px,4vw,48px)] font-bold text-[#0A1628]">
              Finally, See What Users Feel
            </h2>
          </div>
        </FadeInOnScroll>

        <div className="grid md:grid-cols-3 gap-8">
          {SOLUTIONS.map((solution, index) => (
            <FadeInOnScroll key={index} delay={500 + index * 100}>
              <div className="group bg-white rounded-3xl p-8 shadow-sm hover:shadow-xl transition-all duration-300 hover:-translate-y-2 border border-gray-100">
                {/* Emotion tag */}
                <div className={`inline-block px-3 py-1 rounded-full text-xs font-bold text-white bg-gradient-to-r ${solution.color} mb-4`}>
                  {solution.emotion}
                </div>

                {/* Icon */}
                <div className={`w-16 h-16 mb-5 rounded-2xl bg-gradient-to-br ${solution.color} bg-opacity-10 flex items-center justify-center text-3xl group-hover:scale-110 transition-transform duration-300`}>
                  {solution.icon}
                </div>

                {/* Title */}
                <h3 className="text-xl font-bold text-[#0A1628] mb-3">{solution.title}</h3>

                {/* Description */}
                <p className="text-base text-[#475569] leading-relaxed">{solution.description}</p>

                {/* Arrow indicator */}
                <div className={`mt-4 w-8 h-8 rounded-full bg-gradient-to-r ${solution.color} bg-opacity-10 flex items-center justify-center group-hover:bg-opacity-20 transition-colors`}>
                  <svg className="w-4 h-4 text-[#007BFF]" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </FadeInOnScroll>
          ))}
        </div>
      </div>
    </section>
  );
}
