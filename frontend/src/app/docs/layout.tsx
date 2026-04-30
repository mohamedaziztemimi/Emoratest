import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Documentation — EmoraTest Emotion Analytics",
  description: "Complete guide to installing and using EmoraTest emotion tracking SDK. Learn how to detect user emotions from mouse behavior.",
};

export default function DocsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return children;
}
