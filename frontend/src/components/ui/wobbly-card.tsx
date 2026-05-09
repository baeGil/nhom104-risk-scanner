import { cn } from "@/lib/utils";
import { WOBBLY_MD } from "@/lib/radius";

interface WobblyCardProps extends React.HTMLAttributes<HTMLDivElement> {
  decoration?: "none" | "tape" | "tack";
  variant?: "default" | "postit";
}

export function WobblyCard({
  children,
  className,
  decoration = "none",
  variant = "default",
  ...props
}: WobblyCardProps) {
  const bgMap = {
    default: "bg-white",
    postit: "bg-postit",
  };

  return (
    <div
      className={cn(
        "relative border-2 border-fg p-6 transition-all duration-100",
        "shadow-card",
        bgMap[variant],
        className
      )}
      style={{ borderRadius: WOBBLY_MD }}
      {...props}
    >
      {decoration === "tape" && (
        <div className="absolute -top-3 left-1/2 -translate-x-1/2 w-16 h-5 bg-muted/60 rotate-1" />
      )}
      {decoration === "tack" && (
        <div className="absolute -top-2 left-1/2 -translate-x-1/2 w-4 h-4 rounded-full bg-accent border border-fg" />
      )}
      {children}
    </div>
  );
}
