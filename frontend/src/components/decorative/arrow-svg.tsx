import { cn } from "@/lib/utils";

interface ArrowSVGProps {
  className?: string;
  direction?: "right" | "down" | "left";
}

export function ArrowSVG({ className, direction = "right" }: ArrowSVGProps) {
  const rotationMap = {
    right: "rotate(0)",
    down: "rotate(90)",
    left: "rotate(180)",
  };

  return (
    <svg
      className={cn("w-16 h-8 hidden md:block", className)}
      viewBox="0 0 64 32"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      style={{ transform: rotationMap[direction] }}
    >
      <path
        d="M2 16 Q16 4 32 16 Q48 28 56 16"
        stroke="#2d2d2d"
        strokeWidth="2.5"
        fill="none"
        strokeDasharray="4 3"
      />
      <path
        d="M50 10 L58 16 L50 22"
        stroke="#2d2d2d"
        strokeWidth="2.5"
        fill="none"
      />
    </svg>
  );
}
