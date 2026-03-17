import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Conversiono",
  description: "AI behavioral intelligence for e-commerce",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
