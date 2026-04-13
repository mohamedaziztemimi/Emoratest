/* ────────────────────────────────────────────────
   EmoraTest Landing Page - Single scrollable page
   ──────────────────────────────────────────────── */

import { HeroSection } from "@/components/hero/HeroSection";
import { FeaturesSection } from "@/components/landing/FeaturesSection";
import { SocialProofSection } from "@/components/landing/SocialProofSection";
import { HowItWorksSection } from "@/components/landing/HowItWorksSection";
import { IntegrationsSection } from "@/components/landing/IntegrationsSection";
import { PricingSection } from "@/components/landing/PricingSection";
import { FinalCTASection } from "@/components/landing/FinalCTASection";
import { Footer } from "@/components/landing/Footer";
import { StickyAuditBar } from "@/components/navigation/StickyAuditBar";

export default function LandingPage() {
  return (
    <>
      {/* Hero Section */}
      <HeroSection id="hero" />

      {/* Features Section - Pain-Agitation-Solution */}
      <FeaturesSection id="features" />

      {/* Social Proof Section */}
      <SocialProofSection />

      {/* How It Works Section - Interactive Demo */}
      <HowItWorksSection id="how-it-works" />

      {/* Integrations Section */}
      <IntegrationsSection id="integrations" />

      {/* Pricing Section */}
      <PricingSection id="pricing" />

      {/* Final CTA Section */}
      <FinalCTASection />

      {/* Footer */}
      <Footer />

      {/* Sticky Audit Bar */}
      <StickyAuditBar />
    </>
  );
}
