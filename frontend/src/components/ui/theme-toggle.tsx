"use client";

import { useTheme } from "@/lib/theme-context";
import { Sun, Moon } from "lucide-react";

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();

  return (
    <button
      onClick={toggleTheme}
      className="flex items-center justify-center w-8 h-8 border-2 border-fg/30 dark:border-fg-dark/30 hover:border-fg dark:hover:border-fg-dark hover:bg-muted dark:hover:bg-muted-dark transition-all duration-200"
      style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
      aria-label={theme === "dark" ? "Chuyển sang giao diện sáng" : "Chuyển sang giao diện tối"}
    >
      {theme === "dark" ? (
        <Sun className="w-4 h-4 text-fg-dark" />
      ) : (
        <Moon className="w-4 h-4 text-fg" />
      )}
    </button>
  );
}
