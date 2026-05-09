import { cn } from "@/lib/utils";
import { WOBBLY } from "@/lib/radius";

interface WobblyButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary";
  size?: "sm" | "md" | "lg";
}

export function WobblyButton({
  children,
  className,
  variant = "primary",
  size = "md",
  ...props
}: WobblyButtonProps) {
  const sizeMap = {
    sm: "px-4 py-2 text-base",
    md: "px-6 py-3 text-lg",
    lg: "px-8 py-4 text-xl",
  };

  const variantMap = {
    primary:
      "bg-white text-fg border-fg hover:bg-accent hover:text-white active:bg-accent",
    secondary:
      "bg-muted text-fg border-fg hover:bg-secondary hover:text-white active:bg-secondary",
  };

  return (
    <button
      className={cn(
        "font-body border-[3px] border-fg font-bold transition-all duration-100 cursor-pointer",
        "shadow-[4px_4px_0px_0px_#2d2d2d]",
        "hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_#2d2d2d]",
        "active:translate-x-[4px] active:translate-y-[4px] active:shadow-none",
        sizeMap[size],
        variantMap[variant],
        className
      )}
      style={{ borderRadius: WOBBLY }}
      {...props}
    >
      {children}
    </button>
  );
}
