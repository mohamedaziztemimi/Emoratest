import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Sign Up Free — EmoraTest Emotion Analytics",
  description: "Create your free EmoraTest account. No credit card required. Start detecting user emotions from mouse behavior today.",
};

export default function SignupLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
