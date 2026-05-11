/* ────────────────────────────────────────────────────────
   ConfettiWin - Pure CSS/JS confetti burst animation
   ──────────────────────────────────────────────────────── */

"use client";

import { useEffect, useRef } from "react";
import { createPortal } from "react-dom";

export interface ConfettiWinProps {
  trigger: boolean;
  message?: string;
}

const PARTICLE_COUNT = 40;
const COLORS = ["var(--et-blue)", "var(--et-purple)", "var(--et-confused)", "var(--et-engaged)"];

export function ConfettiWin({ trigger, message }: ConfettiWinProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (!trigger) return;

    // Create container if not exists
    if (!containerRef.current) {
      containerRef.current = document.createElement("div");
      containerRef.current.className = "fixed inset-0 pointer-events-none z-[100] overflow-hidden";
      document.body.appendChild(containerRef.current);
    }

    const container = containerRef.current;

    // Create particles
    const particles: HTMLDivElement[] = [];

    for (let i = 0; i < PARTICLE_COUNT; i++) {
      const particle = document.createElement("div");
      const color = COLORS[Math.floor(Math.random() * COLORS.length)];
      const size = 6 + Math.random() * 6;
      const angle = (Math.PI * 2 * i) / PARTICLE_COUNT + Math.random() * 0.5;
      const distance = 150 + Math.random() * 100;
      const rotation = Math.random() * 720 - 360;

      particle.style.cssText = `
        position: absolute;
        left: 50%;
        top: 50%;
        width: ${size}px;
        height: ${size}px;
        background-color: ${color};
        border-radius: ${Math.random() > 0.5 ? "50%" : "2px"};
        transform: translate(-50%, -50%) rotate(0deg);
        opacity: 1;
      `;

      container.appendChild(particle);
      particles.push(particle);

      // Animate particle
      particle.animate(
        [
          {
            transform: `translate(-50%, -50%) rotate(0deg) scale(0)`,
            opacity: 0,
          },
          {
            transform: `translate(-50%, -50%) rotate(${rotation * 0.25}deg) scale(1)`,
            opacity: 1,
            offset: 0.1,
          },
          {
            transform: `translate(
              calc(-50% + ${Math.cos(angle) * distance}px),
              calc(-50% + ${Math.sin(angle) * distance}px)
            ) rotate(${rotation}deg) scale(0.5)`,
            opacity: 0,
          },
        ],
        {
          duration: 1200,
          easing: "cubic-bezier(0.16, 1, 0.3, 1)",
          fill: "forwards",
        }
      ).onfinish = () => {
        particle.remove();
      };
    }

    // Create message overlay if provided
    if (message) {
      const messageEl = document.createElement("div");
      messageEl.className = "absolute inset-0 flex items-center justify-center";

      const contentEl = document.createElement("div");
      contentEl.className = "text-center animate-confetti-message";

      const textEl = document.createElement("div");
      textEl.className = "text-3xl font-bold bg-gradient-to-r from-[var(--et-blue)] to-[var(--et-purple)] bg-clip-text text-transparent mb-2";
      // Use textContent to safely set message text (prevents XSS)
      textEl.textContent = message;

      contentEl.appendChild(textEl);
      messageEl.appendChild(contentEl);
      container.appendChild(messageEl);

      // Remove message after animation
      setTimeout(() => messageEl.remove(), 2500);
    }

    // Cleanup
    return () => {
      particles.forEach((p) => p.remove());
    };
  }, [trigger, message]);

  useEffect(() => {
    // Add keyframes for message animation
    if (trigger && !document.querySelector("#confetti-keyframes")) {
      const style = document.createElement("style");
      style.id = "confetti-keyframes";
      style.textContent = `
        @keyframes confetti-message {
          0% { opacity: 0; transform: scale(0.8) translateY(20px); }
          100% { opacity: 1; transform: scale(1) translateY(0); }
        }
        .animate-confetti-message {
          animation: confetti-message 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards;
        }
      `;
      document.head.appendChild(style);
    }
  }, [trigger]);

  if (!trigger) return null;

  return createPortal(<div ref={containerRef} />, document.body);
}
