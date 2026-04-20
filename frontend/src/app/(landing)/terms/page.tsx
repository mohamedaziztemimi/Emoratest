/* ────────────────────────────────────────────────────────
   Terms of Service Page
   ──────────────────────────────────────────────────────── */

import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Terms of Service - EmoraTest",
  description: "Terms and conditions for using EmoraTest services.",
};

export default function TermsPage() {
  return (
    <div
      style={{
        maxWidth: "800px",
        margin: "0 auto",
        padding: "120px 24px 80px",
      }}
    >
      <div style={{ marginBottom: "48px" }}>
        <h1
          style={{
            fontSize: "clamp(32px, 4vw, 48px)",
            fontWeight: "700",
            color: "#111318",
            margin: "0 0 16px 0",
            letterSpacing: "-0.5px",
          }}
        >
          Terms of Service
        </h1>
        <p style={{ fontSize: "16px", color: "#6B7280", margin: 0 }}>
          Last updated: April 2026
        </p>
      </div>

      <div
        style={{
          background: "#FEF3C7",
          border: "1px solid #FCD34D",
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "32px",
        }}
      >
        <p style={{ margin: 0, fontSize: "14px", color: "#92400E" }}>
          <strong>Important:</strong> By installing the EmoraTest SDK, you collect behavioral data from
          your website visitors. You are responsible as the Data Controller under GDPR for obtaining
          appropriate consent and updating your privacy policy.
        </p>
      </div>

      <section style={{ marginBottom: "32px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          1. Your Privacy Responsibilities
        </h2>
        <p style={paragraphStyle}>
          <strong>You are the Data Controller.</strong> When you install the EmoraTest SDK on your
          website, you must:
        </p>
        <ul style={listStyle}>
          <li>
            <strong>Update Your Privacy Policy:</strong> Disclose that you use EmoraTest for behavioral
            analytics
          </li>
          <li>
            <strong>Obtain Consent:</strong> Get appropriate consent from your users where required by
            law
          </li>
          <li>
            <strong>Inform Users:</strong> Provide clear information about data collection
          </li>
        </ul>
      </section>

      <section style={{ marginBottom: "32px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          2. Data Processing Agreement
        </h2>
        <p style={paragraphStyle}>
          EmoraTest acts as a Data Processor. For merchants subject to GDPR, we offer a Data
          Processing Agreement (DPA). Contact{" "}
          <a href="mailto:legal@emoratest.com" style={{ color: "#007BFF" }}>
            legal@emoratest.com
          </a>{" "}
          to request one.
        </p>
      </section>

      <section style={{ marginBottom: "32px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          3. Payment & Termination
        </h2>
        <p style={paragraphStyle}>
          Paid plans are billed monthly or annually. You may terminate your account at any time.
        </p>
      </section>

      <section style={{ marginBottom: "32px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          4. Limitation of Liability
        </h2>
        <p style={paragraphStyle}>
          Our total liability shall not exceed the amount you paid in the 12 months preceding the claim.
        </p>
      </section>

      <section style={{ marginBottom: "32px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          5. Governing Law
        </h2>
        <p style={paragraphStyle}>
          These terms are governed by the laws of the European Union, specifically Germany.
        </p>
      </section>

      <section style={{ marginBottom: "32px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          6. Contact
        </h2>
        <p style={paragraphStyle}>
          Email:{" "}
          <a href="mailto:legal@emoratest.com" style={{ color: "#007BFF" }}>
            legal@emoratest.com
          </a>
        </p>
      </section>

      <div
        style={{
          borderTop: "1px solid #E5E7EB",
          paddingTop: "24px",
          marginTop: "48px",
          textAlign: "center",
        }}
      >
        <p style={{ fontSize: "14px", color: "#6B7280", margin: 0 }}>
          <a href="/" style={{ color: "#007BFF", textDecoration: "none" }}>
            ← Back to Home
          </a>
        </p>
      </div>
    </div>
  );
}

const paragraphStyle = {
  fontSize: "15px",
  lineHeight: "1.7",
  color: "#374151",
  marginBottom: "16px",
};

const listStyle = {
  fontSize: "15px",
  lineHeight: "1.7",
  color: "#374151",
  paddingLeft: "20px",
  marginBottom: "16px",
};
