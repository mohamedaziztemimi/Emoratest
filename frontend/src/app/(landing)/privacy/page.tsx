/* ────────────────────────────────────────────────────────
   Privacy Policy Page - GDPR Compliance
   ──────────────────────────────────────────────────────── */

import { Metadata } from "next";

export const metadata: Metadata = {
  title: "Privacy Policy - EmoraTest",
  description: "Learn how EmoraTest collects, processes, and protects your data.",
};

export default function PrivacyPage() {
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
          Privacy Policy
        </h1>
        <p style={{ fontSize: "16px", color: "#6B7280", margin: 0 }}>
          Last updated: April 2026
        </p>
      </div>

      <div
        style={{
          background: "#EFF6FF",
          border: "1px solid #BFDBFE",
          borderRadius: "12px",
          padding: "20px",
          marginBottom: "32px",
        }}
      >
        <p style={{ margin: 0, fontSize: "14px", color: "#1E40AF" }}>
          <strong>Important:</strong> Under GDPR, EmoraTest acts as a <strong>Data Processor</strong> for
          behavioral data collected via our SDK. Our merchant customers are the <strong>Data
          Controllers</strong> and are responsible for obtaining consent from their end users. This
          policy covers our use of cookies on emoratest.com and data we process on behalf of merchants.
        </p>
      </div>

      <section style={{ marginBottom: "48px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          1. Data We Collect on emoratest.com
        </h2>
        <p style={paragraphStyle}>
          When you visit the EmoraTest website or use our dashboard, we collect:
        </p>
        <ul style={listStyle}>
          <li>
            <strong>Account Data:</strong> Email, password (hashed), workspace name, and settings
          </li>
          <li>
            <strong>Authentication Cookies:</strong> HTTP-only cookies for secure session management
          </li>
          <li>
            <strong>Usage Data:</strong> Dashboard interactions, feature usage, and support communications
          </li>
        </ul>
      </section>

      <section style={{ marginBottom: "48px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          2. Data Processed on Behalf of Merchants
        </h2>
        <p style={paragraphStyle}>
          Merchants install the EmoraTest SDK on <strong>their own websites</strong> to collect
          behavioral data from <strong>their visitors</strong>. As a Data Processor, we process this
          data on merchants' behalf:
        </p>
        <ul style={listStyle}>
          <li>
            <strong>Behavioral Events:</strong> Clicks, scrolls, mouse movements, rage clicks
          </li>
          <li>
            <strong>Session Data:</strong> Duration, page visits, timestamps
          </li>
          <li>
            <strong>Emotion Predictions:</strong> 8-emotion classification
          </li>
        </ul>
      </section>

      <section style={{ marginBottom: "48px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          3. Your Rights Under GDPR
        </h2>
        <ul style={listStyle}>
          <li>
            <strong>Right to Access:</strong> Request a copy of your account data
          </li>
          <li>
            <strong>Right to Erasure:</strong> Request deletion of your account
          </li>
          <li>
            <strong>Right to Portability:</strong> Receive your data in a structured format
          </li>
        </ul>
      </section>

      <section style={{ marginBottom: "48px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          4. Data Location and Security
        </h2>
        <p style={paragraphStyle}>
          All data is processed and stored within the European Union (Hetzner, Germany).
        </p>
      </section>

      <section style={{ marginBottom: "48px" }}>
        <h2
          style={{
            fontSize: "20px",
            fontWeight: "600",
            color: "#111318",
            marginBottom: "16px",
          }}
        >
          5. Contact
        </h2>
        <p style={paragraphStyle}>
          Email:{" "}
          <a href="mailto:privacy@emoratest.com" style={{ color: "#007BFF" }}>
            privacy@emoratest.com
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
