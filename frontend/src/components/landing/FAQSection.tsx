/* ────────────────────────────────────────────────
   FAQSection - Accordion FAQ with 5 questions
   ──────────────────────────────────────────────── */

"use client";

import { useState } from "react";

const FAQ_ITEMS = [
  {
    question: "How is EmoraTest different from Hotjar or FullStory?",
    answer: "Hotjar and FullStory show you WHERE users click and scroll. EmoraTest shows you HOW they feel while doing it. Our emotion ML classifies behavioral states from signals like confusion, frustration, and engagement. No other tool does this automatically.",
  },
  {
    question: "Will the tracking snippet slow down my website?",
    answer: "No. The EmoraTest snippet is under 8KB gzipped and loads asynchronously. It never blocks your page render. We are built for performance-sensitive production sites. Most customers see zero measurable impact on Core Web Vitals.",
  },
  {
    question: "How accurate is the emotion detection?",
    answer: "Our ML model detects behavioral patterns from mouse movements, rage clicks, scroll hesitation, and dwell time. It's designed to identify trends and patterns across sessions rather than classify individual sessions with perfect accuracy.",
  },
  {
    question: "Is my users' data safe and GDPR compliant?",
    answer: "Yes. EmoraTest is GDPR compliant by design. All behavioral data is anonymized by default. We use cookie consent for tracking. Your data is never sold or shared with third parties.",
  },
  {
    question: "How long does it take to see results?",
    answer: "Most teams see their first emotion insights within hours of installing the snippet. Statistically significant A/B test results typically appear within 7-14 days depending on your traffic volume.",
  },
];

export interface FAQSectionProps {
  id?: string;
}

export function FAQSection({ id = "faq" }: FAQSectionProps) {
  const [openIndex, setOpenIndex] = useState<number | null>(null);

  const toggle = (index: number) => {
    setOpenIndex(openIndex === index ? null : index);
  };

  return (
    <section id={id} style={{ background: "#FFFFFF", padding: "100px 24px" }}>
      <div style={{ maxWidth: "700px", margin: "0 auto" }}>
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "48px" }}>
          <p style={{
            fontSize: "13px",
            fontWeight: 600,
            color: "#007BFF",
            letterSpacing: "2px",
            textTransform: "uppercase",
            marginBottom: "12px",
          }}>
            FAQ
          </p>
          <h2 style={{
            fontSize: "clamp(28px, 4vw, 40px)",
            fontWeight: 700,
            color: "#111318",
            marginBottom: "16px",
          }}>
            FAQ
          </h2>
          <p style={{ fontSize: "16px", color: "#6B7280" }}>
            If you have others, we&apos;re always at hello@emoratest.com
          </p>
        </div>

        {/* FAQ Accordion */}
        <div>
          {FAQ_ITEMS.map((item, index) => (
            <div
              key={index}
              style={{
                borderBottom: "1px solid #E5E7EB",
              }}
            >
              <button
                onClick={() => toggle(index)}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: "20px 0",
                  background: "transparent",
                  border: "none",
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <span style={{
                  fontSize: "16px",
                  fontWeight: 600,
                  color: "#111318",
                  flex: 1,
                  paddingRight: "16px",
                }}>
                  {item.question}
                </span>
                <span style={{
                  fontSize: "24px",
                  color: "#007BFF",
                  transition: "transform 0.2s ease",
                  transform: openIndex === index ? "rotate(45deg)" : "rotate(0deg)",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  minWidth: "24px",
                }}>
                  {openIndex === index ? "×" : "+"}
                </span>
              </button>

              <div
                style={{
                  maxHeight: openIndex === index ? "500px" : "0",
                  overflow: "hidden",
                  transition: "max-height 0.3s ease-out",
                }}
              >
                <p style={{
                  fontSize: "15px",
                  color: "#4B5563",
                  lineHeight: 1.6,
                  paddingBottom: openIndex === index ? "20px" : "0",
                  margin: 0,
                }}>
                  {item.answer}
                </p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
