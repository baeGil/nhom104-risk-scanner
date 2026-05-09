import { cn } from "@/lib/utils";

interface TapeStripProps {
  className?: string;
}

export function TapeStrip({ className }: TapeStripProps) {
  return (
    <div
      className={cn(
        "absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-muted/60",
        className
      )}
      style={{ transform: "translateX(-50%) rotate(1deg)" }}
    />
  );
}
