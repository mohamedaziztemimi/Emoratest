/* ────────────────────────────────────────────────
   EmoraTest Landing Page - Single scrollable page
   ──────────────────────────────────────────────── */

import { HeroSection } from "@/components/hero/HeroSection";
import { FeaturesSection } from "@/components/landing/FeaturesSection";
import { HowItWorksSection } from "@/components/landing/HowItWorksSection";
import { IntegrationsSection } from "@/components/landing/IntegrationsSection";
import { PricingSection } from "@/components/landing/PricingSection";
import { FAQSection } from "@/components/landing/FAQSection";
import { FinalCTASection } from "@/components/landing/FinalCTASection";
import { Footer } from "@/components/landing/Footer";
import { StickyAuditBar } from "@/components/navigation/StickyAuditBar";
import { CookieConsentBanner } from "@/components/ui/CookieConsentBanner";

export default function LandingPage() {
  return (
    <>
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

      {/* Cookie Consent Banner */}
      <CookieConsentBanner />
    </>
  );
}
