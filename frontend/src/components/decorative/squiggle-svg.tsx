import { cn } from "@/lib/utils";

interface SquiggleSVGProps {
  className?: string;
  direction?: "horizontal" | "vertical";
}

export function SquiggleSVG({ className, direction = "horizontal" }: SquiggleSVGProps) {
  if (direction === "vertical") {
    return (
      <svg
        className={cn("w-4 h-16", className)}
        viewBox="0 0 10 60"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <path
          d="M5 0 Q10 10 5 20 Q0 30 5 40 Q10 50 5 60"
          stroke="#2d2d2d"
          strokeWidth="2"
          fill="none"
          strokeDasharray="4 4"
        />
      </svg>
    );
  }

  return (
    <svg
      className={cn("w-32 h-4 hidden md:block", className)}
      viewBox="0 0 128 10"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
    >
      <path
        d="M0 5 Q16 0 32 5 Q48 10 64 5 Q80 0 96 5 Q112 10 128 5"
        stroke="#2d2d2d"
        strokeWidth="2"
        fill="none"
        strokeDasharray="4 4"
      />
    </svg>
  );
}
