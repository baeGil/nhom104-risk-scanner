import { cn } from "@/lib/utils";
import { WOBBLY, WOBBLY_MD, WOBBLY_SM } from "@/lib/radius";

interface WobblyBoxProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "emphasized";
  radius?: "sm" | "md" | "lg";
}

export function WobblyBox({
  children,
  className,
  variant = "default",
  radius = "md",
  ...props
}: WobblyBoxProps) {
  const radiusMap = {
    sm: WOBBLY_SM,
    md: WOBBLY_MD,
    lg: WOBBLY,
  };

  const shadowMap = {
    default: "shadow-[4px_4px_0px_0px_#2d2d2d]",
    emphasized: "shadow-[8px_8px_0px_0px_#2d2d2d]",
  };

  return (
    <div
      className={cn(
        "border-2 border-fg bg-white p-6 transition-all duration-100",
        shadowMap[variant],
        "hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0px_0px_#2d2d2d]",
        className
      )}
      style={{ borderRadius: radiusMap[radius] }}
      {...props}
    >
      {children}
    </div>
  );
}
