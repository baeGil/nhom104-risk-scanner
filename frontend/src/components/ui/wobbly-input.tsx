import { cn } from "@/lib/utils";
import { WOBBLY_MD } from "@/lib/radius";

interface WobblyInputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
}

export function WobblyInput({
  className,
  label,
  error,
  ...props
}: WobblyInputProps) {
  return (
    <div className="flex flex-col gap-1">
      {label && (
        <label className="font-heading text-lg text-fg">{label}</label>
      )}
      <input
        className={cn(
          "font-body border-2 border-fg bg-white px-4 py-3 text-lg text-fg",
          "placeholder:text-fg/40",
          "focus:border-secondary focus:ring-2 focus:ring-secondary/20 focus:outline-none",
          "transition-colors duration-100",
          error && "border-accent",
          className
        )}
        style={{ borderRadius: WOBBLY_MD }}
        {...props}
      />
      {error && (
        <span className="font-body text-sm text-accent">{error}</span>
      )}
    </div>
  );
}
