/* ────────────────────────────────────────────────
   EmoraTest Landing Page - Single scrollable page
   ──────────────────────────────────────────────── */

import { HeroSection } from "@/components/hero/HeroSection";
import Script from "next/script";

// FAQPage structured data for FAQ rich results
const FAQ_SCHEMA = {
  "@context": "https://schema.org",
  "@type": "FAQPage",
  mainEntity: [
    {
      "@type": "Question",
      name: "How is EmoraTest different from Hotjar or FullStory?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Hotjar and FullStory show you WHERE users click and scroll. EmoraTest shows you HOW they feel while doing it. Our emotion ML classifies 8 emotional states from behavioral signals like confusion, frustration, and delight.",
      },
    },
    {
      "@type": "Question",
      name: "Will the tracking snippet slow down my website?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "No. The EmoraTest snippet is under 8KB gzipped and loads asynchronously. It never blocks your page render. We are built for performance-sensitive production sites.",
      },
    },
    {
      "@type": "Question",
      name: "How accurate is the emotion detection?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Our ML model achieves 80% plus accuracy on confusion and frustration classification using behavioral signals including mouse patterns, rage clicks, scroll hesitation, and dwell time.",
      },
    },
    {
      "@type": "Question",
      name: "Is my users' data safe and GDPR compliant?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Yes. EmoraTest is GDPR compliant by design. All behavioral data is anonymized by default. We use cookie consent for tracking.",
      },
    },
    {
      "@type": "Question",
      name: "How long does it take to see results?",
      acceptedAnswer: {
        "@type": "Answer",
        text: "Most teams see their first emotion insights within hours of installing the snippet. Statistically significant A/B test results typically appear within 7-14 days.",
      },
    },
  ],
};
import { FeaturesSection } from "@/components/landing/FeaturesSection";
import { HowItWorksSection } from "@/components/landing/HowItWorksSection";
import { IntegrationsSection } from "@/components/landing/IntegrationsSection";
import { PricingSection } from "@/components/landing/PricingSection";
import { FAQSection } from "@/components/landing/FAQSection";
import { FinalCTASection } from "@/components/landing/FinalCTASection";
import { Footer } from "@/components/landing/Footer";
import { StickyAuditBar } from "@/components/navigation/StickyAuditBar";

export default function LandingPage() {
  return (
    <>
      {/* FAQPage structured data */}
      <Script
        id="faq-schema"
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(FAQ_SCHEMA) }}
      />
      {/* Hero Section */}
      <HeroSection id="hero" />

      {/* Features Section */}
      <FeaturesSection id="features" />

      {/* How It Works Section */}
      <HowItWorksSection id="how-it-works" />

      {/* Integrations Section */}
      <IntegrationsSection id="integrations" />

      {/* Pricing Section */}
      <PricingSection id="pricing" />

      {/* FAQ Section */}
      <FAQSection id="faq" />

      {/* Final CTA Section */}
      <FinalCTASection />

      {/* Footer */}
      <Footer />

      {/* Sticky Audit Bar */}
      <StickyAuditBar />
    </>
  );
}
