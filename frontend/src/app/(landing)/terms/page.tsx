import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service — EmoraTest",
  description: "EmoraTest terms of service. Learn about your rights and responsibilities when using our emotion analytics platform.",
};

const currentDate = new Date().toLocaleDateString("en-US", {
  year: "numeric",
  month: "long",
  day: "numeric",
});

export default function TermsPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-6 py-20">
        <h1 className="text-4xl font-bold text-[#111318] mb-4">Terms of Service</h1>
        <p className="text-sm text-[#6B7280] mb-12">Last updated: {currentDate}</p>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">1. Service</h2>
          <p className="text-[#4B5563] leading-relaxed">
            EmoraTest provides emotion detection and A/B testing tools for websites.
            The service is currently in beta.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">2. Beta Disclaimer</h2>
          <p className="text-[#4B5563] leading-relaxed">
            EmoraTest is currently in beta. The service is provided as-is without warranty.
            Features may change, and we cannot guarantee uptime during the beta period.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">3. Your Responsibilities</h2>
          <p className="text-[#4B5563] leading-relaxed">
            You are responsible for obtaining proper consent from your website visitors
            before using EmoraTest tracking SDK, especially if your visitors are in
            the EU/EEA. You must display a cookie or tracking consent notice.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">4. Data</h2>
          <p className="text-[#4B5563] leading-relaxed">
            You retain ownership of your data. We process it solely to provide the
            service. See our Privacy Policy for details.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">5. Acceptable Use</h2>
          <p className="text-[#4B5563] leading-relaxed">
            Do not use EmoraTest to track users without consent, on websites containing
            illegal content, or in ways that violate applicable laws.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">6. Termination</h2>
          <p className="text-[#4B5563] leading-relaxed">
            You can delete your account at any time. We can suspend accounts that
            violate these terms.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">7. Liability</h2>
          <p className="text-[#4B5563] leading-relaxed">
            To the maximum extent permitted by law, our liability is limited to the
            amount you paid us in the last 12 months.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-[#111318] mb-4">8. Governing Law</h2>
          <p className="text-[#4B5563] leading-relaxed">
            These terms are governed by German law.
          </p>
        </section>
      </div>
    </div>
  );
}
