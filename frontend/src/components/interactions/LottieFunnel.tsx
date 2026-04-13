/* ────────────────────────────────────────────────────────
   LottieFunnel - SVG animated funnel visualization
   ──────────────────────────────────────────────────────── */

"use client";

import { clsx } from "clsx";
import { useEffect, useRef, useState } from "react";

interface FunnelStep {
  label: string;
  color: string;
  dropoff: number;
}

const STEPS: FunnelStep[] = [
  { label: "Landing", color: "var(--et-blue)", dropoff: 25 },
  { label: "Product", color: "var(--et-purple)", dropoff: 35 },
  { label: "Checkout", color: "#8B5CF6", dropoff: 45 },
  { label: "Purchase", color: "var(--et-delight)", dropoff: 0 },
];

const PARTICLE_COUNT = 20;

export interface LottieFunnelProps {
  className?: string;
  speed?: number;
}

export function LottieFunnel({ className, speed = 1 }: LottieFunnelProps) {
  const [currentStep, setCurrentStep] = useState(-1);
  const [dropoffCount, setDropoffCount] = useState(0);
  const [particles, setParticles] = useState<Array<{ id: number; x: number; y: number; state: "flowing" | "dropping" | "completed"; color: string }>>([]);
  const animationRef = useRef<number>();

  useEffect(() => {
    // Step 1: Draw funnel steps
    let stepIndex = 0;
    const drawInterval = setInterval(() => {
      if (stepIndex < STEPS.length) {
        setCurrentStep(stepIndex);
        stepIndex++;
      } else {
        clearInterval(drawInterval);
        // Step 2: Start particle animation
        startParticleAnimation();
      }
    }, 400 / speed);

    return () => {
      clearInterval(drawInterval);
      cancelAnimationFrame(animationRef.current!);
    };
  }, [speed]);

  const startParticleAnimation = () => {
    let frame = 0;
    const loopLength = 360; // 6 seconds at 60fps

    const animate = () => {
      frame = (frame + 1) % loopLength;

      // Create new particles periodically
      if (frame % 15 === 0 && particles.length < PARTICLE_COUNT) {
        const newId = Date.now() + Math.random();
        setParticles((prev) => [
          ...prev,
          {
            id: newId,
            x: 50 + (Math.random() - 0.5) * 20,
            y: 10,
            state: "flowing",
            color: "var(--et-blue)",
          },
        ]);
      }

      // Update particle positions
      setParticles((prev) =>
        prev.map((p, idx) => {
          const speed = 0.5 * speed;
          let newY = p.y + speed;
          let newX = p.x;
          let newState = p.state;
          let newColor = p.color;

          // State transitions based on Y position
          if (newY > 35 && newY < 40 && p.state === "flowing") {
            // At first dropoff point
            if (idx % 3 === 0) {
              newState = "dropping";
              newColor = "var(--et-confusion)";
              newX -= 15;
            }
          } else if (newY > 60 && newY < 65 && p.state === "flowing") {
            // At second dropoff point
            if (idx % 2 === 0) {
              newState = "dropping";
              newColor = "var(--et-confusion)";
              newX += 15;
            }
          } else if (newY > 85 && p.state === "flowing") {
            // Reached bottom
            newState = "completed";
            newColor = "var(--et-delight)";
          }

          // Animate dropping particles
          if (newState === "dropping") {
            newY += speed * 0.5;
            newX += (newX < 50 ? 1 : -1) * speed * 0.3;
          }

          // Reset completed particles
          if (newY > 95) {
            return {
              id: p.id,
              x: 50 + (Math.random() - 0.5) * 20,
              y: 10,
              state: "flowing" as const,
              color: "var(--et-blue)",
            };
          }

          return { id: p.id, x: newX, y: newY, state: newState, color: newColor };
        })
      );

      // Animate dropoff counter
      const dropoffFrame = Math.floor(frame / 30) % 3;
      const targetDropoff = [25, 35, 45][dropoffFrame];
      setDropoffCount((prev) => {
        if (prev < targetDropoff) return prev + 1;
        if (prev > targetDropoff) return prev - 1;
        return prev;
      });

      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);
  };

  return (
    <div className={clsx("relative w-full h-[400px]", className)}>
      <svg viewBox="0 0 100 100" className="w-full h-full">
        {/* Funnel steps */}
        {STEPS.map((step, i) => {
          const isDrawn = i <= currentStep;
          const opacity = isDrawn ? 1 : 0;
          const topY = 5 + i * 22;
          const bottomY = 27 + i * 22;
          const topWidth = 80 - i * 15;
          const bottomWidth = 65 - i * 15;

          return (
            <g key={step.label} style={{ opacity, transition: "opacity 0.4s ease" }}>
              {/* Trapezoid */}
              <path
                d={`
                  M ${50 - topWidth / 2} ${topY}
                  L ${50 + topWidth / 2} ${topY}
                  L ${50 + bottomWidth / 2} ${bottomY}
                  L ${50 - bottomWidth / 2} ${bottomY}
                  Z
                `}
                fill={step.color}
                fillOpacity="0.15"
                stroke={step.color}
                strokeWidth="0.5"
                strokeDasharray={isDrawn ? "0" : "100"}
                strokeDashoffset={isDrawn ? "0" : "100"}
                style={{
                  transition: "stroke-dasharray 0.4s ease, stroke-dashoffset 0.4s ease",
                }}
              />
              {/* Label */}
              <text
                x="50"
                y={(topY + bottomY) / 2}
                textAnchor="middle"
                dominantBaseline="middle"
                className="text-[2px] font-semibold"
                fill="var(--et-text-primary)"
              >
                {step.label}
              </text>
            </g>
          );
        })}

        {/* Particles */}
        {particles.map((p) => (
          <circle
            key={p.id}
            cx={p.x}
            cy={p.y}
            r={p.state === "completed" ? 1 : 0.5}
            fill={p.color}
            className={clsx(
              "transition-all duration-75",
              p.state === "completed" && "animate-pulse"
            )}
          />
        ))}

        {/* Drop-off percentage */}
        <g style={{ opacity: currentStep >= 1 ? 1 : 0, transition: "opacity 0.4s" }}>
          <text
            x="25"
            y="40"
            textAnchor="middle"
            className="text-[2.5px] font-bold"
            fill="var(--et-confusion)"
          >
            -{dropoffCount}%
          </text>
          <text
            x="25"
            y="42"
            textAnchor="middle"
            className="text-[1.2px]"
            fill="var(--et-text-secondary)"
          >
            confused
          </text>
        </g>

        {/* Success indicator */}
        <g style={{ opacity: currentStep >= 3 ? 1 : 0, transition: "opacity 0.4s" }}>
          <circle cx="50" cy="95" r="1.5" fill="var(--et-delight)" className="animate-pulse" />
          <text
            x="50"
            y="98"
            textAnchor="middle"
            className="text-[1.5px]"
            fill="var(--et-delight)"
          >
            delight!
          </text>
        </g>
      </svg>
    </div>
  );
}
