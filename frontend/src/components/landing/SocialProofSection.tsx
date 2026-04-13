/* ────────────────────────────────────────────────
   SocialProofSection - Trust + FOMO with persona testimonials
   ──────────────────────────────────────────────── */

"use client";

import { FadeInOnScroll } from "./FadeInOnScroll";

const LOGOS = [
  { name: "Vercel", gradient: "from-black to-gray-600" },
  { name: "Stripe", gradient: "from-indigo-600 to-purple-600" },
  { name: "Linear", gradient: "from-blue-500 to-cyan-500" },
  { name: "Notion", gradient: "from-gray-700 to-gray-900" },
  { name: "Figma", gradient: "from-pink-500 to-rose-500" },
];

const TESTIMONIALS = [
  {
    quote: "EmoraTest revealed user pain I missed in my own product. The emotion layer is like having UX research on autopilot.",
    author: "Jordan M.",
    role: "PM at GrowthScale",
    avatar: "J",
    avatarGradient: "from-purple-500 to-pink-500",
    persona: "Product Manager",
  },
  {
    quote: "We went from guessing to knowing. +32% conversions in week one. The confusion heatmap alone is worth 10x the price.",
    author: "Alex R.",
    role: "Growth Lead at StartupXYZ",
    avatar: "A",
    avatarGradient: "from-blue-500 to-cyan-500",
    persona: "Growth Marketer",
  },
  {
    quote: "Finally, quant + qual in one view. I can show stakeholders exactly WHY users churn—with emotion data to back it up.",
    author: "Taylor K.",
    role: "UX Researcher at EnterpriseCo",
    avatar: "T",
    avatarGradient: "from-green-500 to-emerald-500",
    persona: "UX Researcher",
  },
];

const STATS = [
  { value: "40%", label: "Churn Drop" },
  { value: "90%", label: "Accuracy" },
  { value: "10K+", label: "Tests Run" },
];

export function SocialProofSection() {
  return (
    <section className="py-[100px] bg-[#F8FAFC]">
      <div className="max-w-[1200px] mx-auto px-6">
        {/* Trusted By */}
        <FadeInOnScroll>
          <div className="text-center mb-12">
            <p className="text-sm font-semibold text-[#64748B] tracking-widest uppercase mb-8">
              Trusted by fast-moving teams
            </p>
            <div className="flex flex-wrap justify-center items-center gap-12 opacity-60">
              {LOGOS.map((logo, index) => (
                <div key={index} className="text-2xl font-bold bg-gradient-to-r bg-clip-text text-transparent" style={{ backgroundImage: `linear-gradient(to right, var(--tw-gradient-stops))` }}>
                  {logo.name}
                </div>
              ))}
            </div>
          </div>
        </FadeInOnScroll>

        {/* Testimonials */}
        <div className="grid md:grid-cols-3 gap-8 mb-16">
          {TESTIMONIALS.map((testimonial, index) => (
            <FadeInOnScroll key={index} delay={index * 100}>
              <div className="bg-white rounded-3xl p-8 shadow-sm hover:shadow-lg transition-all duration-300 border border-gray-100 h-full flex flex-col">
                {/* Persona tag */}
                <div className="inline-block px-3 py-1 rounded-full text-xs font-semibold text-[#007BFF] bg-[#007BFF]/10 mb-4 w-fit">
                  {testimonial.persona}
                </div>

                {/* Quote */}
                <p className="text-[#0A1628] text-lg leading-relaxed mb-6 flex-grow">
                  "{testimonial.quote}"
                </p>

                {/* Author */}
                <div className="flex items-center gap-3">
                  <div className={`w-12 h-12 rounded-full bg-gradient-to-br ${testimonial.avatarGradient} flex items-center justify-center text-white font-bold`}>
                    {testimonial.avatar}
                  </div>
                  <div>
                    <p className="font-semibold text-[#0A1628]">{testimonial.author}</p>
                    <p className="text-sm text-[#64748B]">{testimonial.role}</p>
                  </div>
                </div>
              </div>
            </FadeInOnScroll>
          ))}
        </div>

        {/* Stats Bar - FOMO */}
        <FadeInOnScroll delay={400}>
          <div className="bg-gradient-to-r from-[#007BFF] to-[#7C3AED] rounded-3xl p-8 text-white">
            <div className="grid grid-cols-3 gap-8 text-center">
              {STATS.map((stat, index) => (
                <div key={index}>
                  <div className="text-5xl font-bold mb-2">{stat.value}</div>
                  <div className="text-white/80 font-medium">{stat.label}</div>
                </div>
              ))}
            </div>
            <p className="text-center mt-6 text-white/90 text-sm">
              Join 500+ teams in the exclusive beta program
            </p>
          </div>
        </FadeInOnScroll>
      </div>
    </section>
  );
}
