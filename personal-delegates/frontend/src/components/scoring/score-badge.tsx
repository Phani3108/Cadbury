"use client";

import { cn } from "@/lib/utils";

interface ScoreBadgeProps {
  score: number; // 0-1
  size?: "sm" | "md" | "lg";
  className?: string;
  showLabel?: boolean;
}

function getColor(score: number) {
  if (score >= 0.8) return { stroke: "#22c55e", text: "#16a34a" }; // green
  if (score >= 0.5) return { stroke: "#f59e0b", text: "#d97706" }; // amber
  return { stroke: "#ef4444", text: "#dc2626" };                    // red
}

const SIZE_MAP = {
  sm: { size: 32, stroke: 3, fontSize: 9 },
  md: { size: 48, stroke: 4, fontSize: 13 },
  lg: { size: 64, stroke: 5, fontSize: 17 },
};

export function ScoreBadge({ score, size = "md", className, showLabel }: ScoreBadgeProps) {
  const { size: dim, stroke, fontSize } = SIZE_MAP[size];
  const { stroke: strokeColor, text: textColor } = getColor(score);
  const radius = (dim - stroke * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const progress = score * circumference;
  const pct = Math.round(score * 100);

  return (
    <div className={cn("flex flex-col items-center gap-1", className)}>
      <svg width={dim} height={dim} className="-rotate-90">
        {/* Background ring */}
        <circle
          cx={dim / 2}
          cy={dim / 2}
          r={radius}
          fill="none"
          stroke="#e2e8f0"
          strokeWidth={stroke}
        />
        {/* Progress ring */}
        <circle
          cx={dim / 2}
          cy={dim / 2}
          r={radius}
          fill="none"
          stroke={strokeColor}
          strokeWidth={stroke}
          strokeDasharray={`${progress} ${circumference}`}
          strokeLinecap="round"
          style={{ transition: "stroke-dasharray 0.5s ease" }}
        />
        {/* Center text */}
        <text
          x={dim / 2}
          y={dim / 2}
          textAnchor="middle"
          dominantBaseline="central"
          fill={textColor}
          fontSize={fontSize}
          fontWeight="600"
          fontFamily="var(--font-geist-mono), monospace"
          className="rotate-90"
          style={{ transform: `rotate(90deg)`, transformOrigin: `${dim / 2}px ${dim / 2}px` }}
        >
          {pct}
        </text>
      </svg>
      {showLabel && (
        <span className="text-[10px] text-slate-400 font-medium">Match</span>
      )}
    </div>
  );
}
