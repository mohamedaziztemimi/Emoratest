import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Log In — EmoraTest",
  description: "Sign in to your EmoraTest dashboard to access emotion analytics and session insights.",
};

export default function LoginLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
