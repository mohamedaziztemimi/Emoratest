import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy — EmoraTest",
  description: "EmoraTest privacy policy and data handling practices. Learn how we collect, process, and protect your data.",
};

const currentDate = new Date().toLocaleDateString("en-US", {
  year: "numeric",
  month: "long",
  day: "numeric",
});

export default function PrivacyPage() {
  return (
    <div className="min-h-screen bg-white">
      <div className="max-w-3xl mx-auto px-6 py-20">
        <h1 className="text-4xl font-bold text-[#111318] mb-4">Privacy Policy</h1>
        <p className="text-sm text-[#6B7280] mb-12">Last updated: {currentDate}</p>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">1. Who We Are</h2>
          <p className="text-[#4B5563] leading-relaxed">
            EmoraTest is operated by an individual entity in Germany. Contact us at{" "}
            <a href="mailto:hello@emoratest.com" className="text-[#007BFF] hover:underline">
              hello@emoratest.com
            </a>
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">2. What Data We Collect</h2>
          <div className="space-y-4 text-[#4B5563] leading-relaxed">
            <p>
              <strong>When you use our dashboard:</strong> We collect your email address
              and account information to provide our service. We store this data on
              servers in Germany.
            </p>
            <p>
              <strong>When our SDK is installed on a website:</strong> We collect
              anonymous behavioral data from website visitors, including mouse
              movements, clicks, scroll patterns, and page URLs.
            </p>
            <p className="text-[#6B7280] italic">
              We do NOT collect: names, email addresses, IP addresses (hashed immediately),
              keystrokes, form inputs, screenshots, or camera/microphone data.
            </p>
            <p>
              All behavioral data is processed to detect behavioral states (frustrated,
              confused, engaged, etc.) using machine learning. No individual
              identification is possible from this data.
            </p>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">3. Legal Basis (GDPR)</h2>
          <div className="space-y-4 text-[#4B5563] leading-relaxed">
            <p>
              <strong>For dashboard users:</strong> Contract performance (Art. 6(1)(b) GDPR)
            </p>
            <p>
              <strong>For website visitors tracked by SDK:</strong> Consent (Art. 6(1)(a) GDPR).
              Website operators using EmoraTest must obtain visitor consent before the
              SDK begins tracking.
            </p>
          </div>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">4. Data Retention</h2>
          <p className="text-[#4B5563] leading-relaxed">
            Session data is retained for 90 days, then automatically deleted.
            Account data is retained until you delete your account.
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">5. Your Rights</h2>
          <p className="text-[#4B5563] leading-relaxed mb-4">
            Under GDPR, you have the right to access your data, correct your data,
            delete your data, restrict processing, data portability, and object to
            processing.
          </p>
          <p className="text-[#4B5563] leading-relaxed">
            To exercise these rights, contact{" "}
            <a href="mailto:hello@emoratest.com" className="text-[#007BFF] hover:underline">
              hello@emoratest.com
            </a>
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">6. Data Processing Location</h2>
          <p className="text-[#4B5563] leading-relaxed">
            All data is processed and stored on servers within the European Union
            (Germany).
          </p>
        </section>

        <section className="mb-10">
          <h2 className="text-xl font-semibold text-[#111318] mb-4">7. Cookies</h2>
          <p className="text-[#4B5563] leading-relaxed">
            EmoraTest uses essential cookies for authentication (session management).
            Our tracking SDK uses a consent cookie (emoratest_consent) to remember
            your tracking preference. We do not use advertising or third-party
            tracking cookies.
          </p>
        </section>

        <section>
          <h2 className="text-xl font-semibold text-[#111318] mb-4">8. Changes</h2>
          <p className="text-[#4B5563] leading-relaxed">
            We may update this policy. The latest version is always available at this URL.
          </p>
        </section>
      </div>
    </div>
  );
}
