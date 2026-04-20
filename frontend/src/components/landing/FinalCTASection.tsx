/* ────────────────────────────────────────────────
   FinalCTASection - Bottom conversion section with animation
   ──────────────────────────────────────────────── */

"use client";

export function FinalCTASection() {
  return (
    <section style={{
      background: "linear-gradient(135deg, #EEF5FF 0%, #F3EEFF 100%)",
      paddingTop: "100px",
      paddingBottom: "100px",
      textAlign: "center",
      marginTop: "0",
    }}>
      <div style={{ maxWidth: "700px", margin: "0 auto", display: "flex", flexDirection: "column", gap: "24px", alignItems: "center" }}>

        <h2 style={{ fontSize: "clamp(32px, 4vw, 48px)", fontWeight: 700, color: "#111318", margin: 0, lineHeight: 1.2 }}>
          Ready to See What Your Users Actually Feel?
        </h2>

        <p style={{ fontSize: "18px", color: "#4B5563", margin: 0, lineHeight: 1.7, maxWidth: "560px" }}>
          Join 2,400+ growth teams who stopped guessing and started
          winning with emotion-powered testing.
        </p>

        <div style={{ display: "flex", gap: "16px", flexWrap: "wrap", justifyContent: "center" }}>
          <a href="/signup" style={{
            background: "linear-gradient(135deg, #007BFF 0%, #7C3AED 100%)",
            color: "white",
            padding: "14px 28px",
            borderRadius: "9999px",
            fontWeight: 600,
            fontSize: "15px",
            textDecoration: "none",
            whiteSpace: "nowrap",
          }}>
            Start Free — No Credit Card
          </a>
          <a href="/demo" style={{
            background: "transparent",
            color: "#007BFF",
            padding: "14px 28px",
            borderRadius: "9999px",
            fontWeight: 600,
            fontSize: "15px",
            textDecoration: "none",
            border: "2px solid #007BFF",
            whiteSpace: "nowrap",
          }}>
            Book a Demo
          </a>
        </div>

        <p style={{ fontSize: "13px", color: "#9CA3AF", margin: 0 }}>
          ✓ Free forever plan &nbsp;&nbsp; ✓ 2-min setup &nbsp;&nbsp; ✓ No credit card &nbsp;&nbsp; ✓ Cancel anytime
        </p>

      </div>
    </section>
  );
}
