import { cn } from "@/lib/utils";

interface ThumbtackProps {
  className?: string;
  color?: "red" | "blue" | "yellow";
}

export function Thumbtack({ className, color = "red" }: ThumbtackProps) {
  const colorMap = {
    red: "bg-accent",
    blue: "bg-secondary",
    yellow: "bg-postit",
  };

  return (
    <div
      className={cn(
        "absolute -top-2 left-1/2 w-4 h-4 rounded-full border border-fg",
        colorMap[color],
        className
      )}
      style={{ transform: "translateX(-50%)" }}
    />
  );
}
