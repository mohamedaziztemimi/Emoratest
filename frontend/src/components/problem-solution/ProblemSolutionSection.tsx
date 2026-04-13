/* ────────────────────────────────────────────────────────
   ProblemSolutionSection - Why EmoraTest section with persona tabs
   ──────────────────────────────────────────────────────── */

"use client";

import { useEffect, useState } from "react";
import { GlassCard } from "../ui";
import { EmotionBadge } from "../ui";
import { BeforeAfterSlide, type SlideContent } from "./BeforeAfterSlide";

// Persona configurations
const PERSONAS = [
  { id: "growth", name: "Alex", role: "Growth" },
  { id: "pm", name: "Jordan", role: "PM" },
  { id: "ux", name: "Taylor", role: "UX" },
  { id: "cro", name: "Riley", role: "CRO" },
] as const;

type PersonaId = typeof PERSONAS[number]["id"];

// Slide content for each persona
const SLIDE_CONTENT: Record<PersonaId, { before: SlideContent; after: SlideContent }> = {
  growth: {
    before: {
      title: "Metrics don't explain drop-offs",
      description: "Conversion dropped 23% last week. Funnel analytics show where users left, but not why. Is it confusion? Frustration? Or something else?",
      stats: ["↓ 23% conversion drop", "No root cause visible", "Manual session review takes hours"],
    },
    after: {
      title: "Emotion heatmap finds the leak instantly",
      description: "EmoraTest detected 68% confusion on the pricing plan CTA. Users hovered but hesitated. A/B tested a clearer variant → +32% lift.",
      stats: ["↓ 40% drop-off explained", "Confusion pinpointed in 2s", "Fix deployed same day"],
    },
  },
  pm: {
    before: {
      title: "Manual heatmaps too slow",
      description: "Setting up traditional heatmaps takes days. By the time you see the data, the experiment is over. No real-time feedback loop.",
      stats: ["2-3 days setup time", "Delayed insights", "Missed optimization windows"],
    },
    after: {
      title: "Instant emotion session replay",
      description: "EmoraTest captures emotions in real-time. Watch confusion spike on a specific form field, iterate, and validate—all in the same session.",
      stats: ["Zero setup, instant data", "Live emotion tracking", "Same-day iteration cycle"],
    },
  },
  ux: {
    before: {
      title: "Clicks miss the emotional story",
      description: "Heatmaps show where users clicked, but not how they felt. Did they click confidently? Hesitantly? In frustration? Click data alone can't tell.",
      stats: ["Clicks ≠ engagement quality", "Missing user sentiment", "Design decisions feel risky"],
    },
    after: {
      title: "Valence-arousal maps with user quotes",
      description: "See the emotional journey: excitement on discovery → hesitation at checkout → frustration on error. User quotes add context: \"I couldn't find the button.\"",
      stats: ["8 emotions, not just clicks", "User voice + visual data", "Design backed by feelings"],
    },
  },
  cro: {
    before: {
      title: "Scale tests without bias",
      description: "Running 50+ A/B tests across segments? Sample ratio mismatch (SRM) silently skews results. Segmentation is manual and error-prone.",
      stats: ["SRM goes undetected", "Manual segmentation pain", "Biased experiment results"],
    },
    after: {
      title: "SRM-safe segmented tests",
      description: "EmoraTest auto-detects SRM anomalies before they affect conclusions. Emotion segmentation ensures fair testing across cohorts.",
      stats: ["Auto SRM detection", "Fair cohort segmentation", "Statistically sound winners"],
    },
  },
};

// Feature cards
const FEATURES = [
  {
    title: "8 Emotions Detected",
    description: "Confusion, frustration, delight, anxiety, hesitation, focus, boredom, satisfaction.",
    badges: ["confusion", "frustration", "delight", "anxiety", "satisfaction", "hesitation", "focus", "boredom"] as const,
    chip: "Real-time",
  },
  {
    title: "Auto Variant Generation",
    description: "AI suggests test variants based on detected pain points. No more guessing what to A/B test.",
    chip: "AI-powered",
  },
  {
    title: "Why-Analysis",
    description: "Links emotion spikes to revenue drop-off automatically. Know exactly which feeling costs you conversions.",
    chip: "Revenue-aware",
  },
];

// Customer quotes
const QUOTES = [
  {
    text: "EmoraTest cut our experiment cycle time by 80%. We went from guessing to knowing what moves the needle.",
    name: "Sarah Chen",
    role: "Head of Growth, ShopFlow",
    avatar: "SC",
  },
  {
    text: "The emotion heatmap is like having a user researcher watching every single session, at scale.",
    name: "Marcus Johnson",
    role: "VP of Product, Taskly",
    avatar: "MJ",
  },
];

export function ProblemSolutionSection() {
  const [activePersona, setActivePersona] = useState<PersonaId>("growth");
  const [hasInteracted, setHasInteracted] = useState(false);

  // Auto-cycle tabs every 5s
  useEffect(() => {
    if (hasInteracted) return;

    const interval = setInterval(() => {
      setActivePersona((current) => {
        const currentIndex = PERSONAS.findIndex((p) => p.id === current);
        return PERSONAS[(currentIndex + 1) % PERSONAS.length].id;
      });
    }, 5000);

    return () => clearInterval(interval);
  }, [hasInteracted]);

  const handleTabChange = (personaId: PersonaId) => {
    setActivePersona(personaId);
    setHasInteracted(true);
  };

  return (
    <section className="py-24 bg-[var(--et-bg-900)] min-h-[600px]">
      <div className="container mx-auto px-4 light-mode text-[var(--et-text-primary)]">
        {/* Section header */}
        <div className="text-center max-w-2xl mx-auto mb-12">
          <h2 className="text-[clamp(28px,4vw,42px)] font-bold text-[var(--et-text-primary)] mb-4">
            Stop Guessing. Start Feeling.
          </h2>
          <p className="text-[16px] text-[var(--et-text-muted)] leading-relaxed">
            Traditional analytics show what happened. EmoraTest shows why — with ML
            that reads confusion, frustration, and delight in real-time.
          </p>
        </div>

        {/* Persona tabs - horizontal scroll on mobile (<640px) */}
        <div className="flex md:flex-wrap justify-start md:justify-center gap-2 mb-8 md:mb-12 overflow-x-auto snap-x snap-mandatory -mx-4 px-4 md:mx-0 md:px-0 no-scrollbar">
          {PERSONAS.map((persona) => (
            <button
              key={persona.id}
              onClick={() => handleTabChange(persona.id)}
              className={`
                relative px-4 py-2 rounded-full text-sm font-medium transition-all duration-300
                ${activePersona === persona.id
                  ? "text-[var(--et-text-primary)]"
                  : "text-[var(--et-text-muted)] hover:text-[var(--et-text-secondary)]"
                }
              `}
            >
              {persona.name}
              <span className="hidden md:inline text-[var(--et-text-muted)]"> ({persona.role})</span>
              {/* Active underline */}
              {activePersona === persona.id && (
                <span className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full bg-gradient-to-r from-[var(--et-blue)] to-[var(--et-purple)] transition-all duration-300" />
              )}
            </button>
          ))}
        </div>

        {/* Before/After slide with crossfade */}
        <div className="max-w-4xl mx-auto mb-16">
          <div className="relative min-h-[380px]">
            {PERSONAS.map((persona) => (
              <div
                key={persona.id}
                className={`
                  absolute inset-0 transition-opacity duration-300 ease-in-out
                  ${activePersona === persona.id ? "opacity-100" : "opacity-0 pointer-events-none"}
                `}
              >
                <BeforeAfterSlide
                  persona={persona.id as any}
                  before={SLIDE_CONTENT[persona.id].before}
                  after={SLIDE_CONTENT[persona.id].after}
                />
              </div>
            ))}
          </div>
        </div>

        {/* Feature grid */}
        <div className="grid md:grid-cols-3 gap-6 mb-16">
          {FEATURES.map((feature, index) => (
            <GlassCard key={index} padding="lg" hover glow="blue">
              <div className="mb-3 flex items-center gap-2">
                <span className="text-[11px] font-bold px-2 py-0.5 rounded-full bg-[var(--et-blue)]/20 text-[var(--et-blue)]">
                  {feature.chip}
                </span>
              </div>
              <h3 className="text-lg font-semibold text-[var(--et-text-primary)] mb-2">
                {feature.title}
              </h3>
              <p className="text-[14px] text-[var(--et-text-muted)] leading-relaxed mb-3">
                {feature.description}
              </p>
              {feature.badges && (
                <div className="flex flex-wrap gap-1.5">
                  {feature.badges.map((badge) => (
                    <EmotionBadge key={badge} emotion={badge} size="sm" />
                  ))}
                </div>
              )}
            </GlassCard>
          ))}
        </div>

        {/* Quote strip */}
        <div className="grid md:grid-cols-2 gap-6">
          {QUOTES.map((quote, index) => (
            <GlassCard key={index} padding="lg">
              <div className="flex gap-4">
                <div className="shrink-0 w-12 h-12 rounded-full bg-gradient-to-br from-[var(--et-blue)] to-[var(--et-purple)] flex items-center justify-center text-white font-bold">
                  {quote.avatar}
                </div>
                <div>
                  <p className="text-[15px] italic text-[var(--et-text-secondary)] mb-3">
                    "{quote.text}"
                  </p>
                  <div>
                    <div className="font-medium text-[var(--et-text-primary)]">
                      {quote.name}
                    </div>
                    <div className="text-[13px] text-[var(--et-text-muted)]">
                      {quote.role}
                    </div>
                  </div>
                </div>
              </div>
            </GlassCard>
          ))}
        </div>
      </div>
    </section>
  );
}
