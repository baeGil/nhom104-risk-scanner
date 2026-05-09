import { cn } from "@/lib/utils";

interface WobblyDividerProps {
  className?: string;
  variant?: "dashed" | "squiggle";
}

export function WobblyDivider({
  className,
  variant = "dashed",
}: WobblyDividerProps) {
  if (variant === "squiggle") {
    return (
      <svg
        className={cn("w-full h-4", className)}
        viewBox="0 0 200 10"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M0 5 Q10 0 20 5 Q30 10 40 5 Q50 0 60 5 Q70 10 80 5 Q90 0 100 5 Q110 10 120 5 Q130 0 140 5 Q150 10 160 5 Q170 0 180 5 Q190 10 200 5"
          stroke="#2d2d2d"
          strokeWidth="2"
          fill="none"
        />
      </svg>
    );
  }

  return (
    <div
      className={cn("border-t-2 border-dashed border-fg/40 my-4", className)}
    />
  );
}
