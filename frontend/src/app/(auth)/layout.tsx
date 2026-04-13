/* ────────────────────────────────────────────────
   Auth Layout - Centered layout for login/signup
   ──────────────────────────────────────────────── */

export default function AuthLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div
      style={{
        minHeight: "100vh",
        background: "linear-gradient(135deg, #F0F4FF 0%, #F8F0FF 100%)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "24px",
      }}
    >
      {children}
    </div>
  );
}
