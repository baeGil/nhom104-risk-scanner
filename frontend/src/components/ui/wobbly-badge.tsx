import { cn } from "@/lib/utils";
import { WOBBLY_SM } from "@/lib/radius";

interface WobblyBadgeProps {
  children: React.ReactNode;
  variant?: "default" | "accent" | "secondary" | "postit";
  className?: string;
}

export function WobblyBadge({
  children,
  variant = "default",
  className,
}: WobblyBadgeProps) {
  const variantMap = {
    default: "bg-white text-fg border-fg",
    accent: "bg-accent text-white border-accent",
    secondary: "bg-secondary text-white border-secondary",
    postit: "bg-postit text-fg border-fg",
  };

  return (
    <span
      className={cn(
        "inline-block border-2 px-3 py-1 font-body text-sm font-bold",
        "-rotate-1",
        variantMap[variant],
        className
      )}
      style={{ borderRadius: WOBBLY_SM }}
    >
      {children}
    </span>
  );
}
