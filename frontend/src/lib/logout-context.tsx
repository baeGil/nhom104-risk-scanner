"use client";

import { createContext, useContext, useState, useCallback, ReactNode } from "react";
import { useRouter } from "next/navigation";
import { X } from "lucide-react";
import { broadcastLogout } from "@/lib/auth-sync";

interface LogoutContextType {
  showLogoutConfirm: () => void;
}

const LogoutContext = createContext<LogoutContextType | null>(null);

export function LogoutProvider({ children }: { children: ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);
  const router = useRouter();

  const handleLogout = useCallback(async () => {
    await fetch("/api/auth/signout", { method: "POST" });
    broadcastLogout();
    router.push("/");
    router.refresh();
  }, [router]);

  const showLogoutConfirm = useCallback(() => {
    setIsOpen(true);
  }, []);

  return (
    <LogoutContext.Provider value={{ showLogoutConfirm }}>
      {children}

      {isOpen && (
        <div
          className="fixed inset-0 flex items-center justify-center bg-black/40 backdrop-blur-sm"
          style={{ zIndex: 9999 }}
          onClick={() => setIsOpen(false)}
        >
          <div
            className="bg-white border-2 border-fg p-6 w-80 shadow-lg"
            style={{ borderRadius: "120px 8px 90px 8px / 8px 90px 8px 120px" }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-heading text-xl text-fg">Xác nhận đăng xuất</h3>
              <button
                onClick={() => setIsOpen(false)}
                className="w-7 h-7 flex items-center justify-center border-2 border-fg/20 hover:border-fg transition-colors"
                style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
            <p className="font-body text-fg/70 mb-4">Bạn chắc chắn muốn đăng xuất chứ?</p>
            <div className="flex gap-3">
              <button
                onClick={() => setIsOpen(false)}
                className="flex-1 py-2 px-4 border-2 border-fg/30 font-body text-lg hover:border-fg transition-colors"
                style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
              >
                Huỷ
              </button>
              <button
                onClick={handleLogout}
                className="flex-1 py-2 px-4 bg-fg text-white font-body text-lg hover:bg-accent transition-colors"
                style={{ borderRadius: "255px 15px 225px 15px / 15px 225px 15px 255px" }}
              >
                Đăng xuất
              </button>
            </div>
          </div>
        </div>
      )}
    </LogoutContext.Provider>
  );
}

export function useLogoutConfirm() {
  const context = useContext(LogoutContext);
  if (!context) {
    throw new Error("useLogoutConfirm must be used within LogoutProvider");
  }
  return context;
}
