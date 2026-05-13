"use client";

import { createContext, useContext, ReactNode } from "react";
import { Session } from "next-auth";

interface AuthContextType {
  session: Session | null;
  user: {
    id?: string;
    name?: string | null;
    email?: string | null;
    image?: string | null;
    role?: "free" | "premium" | "admin";
  };
  isAuthenticated: boolean;
}

const AuthContext = createContext<AuthContextType | null>(null);

interface AuthProviderProps {
  children: ReactNode;
  session: Session | null;
}

export function AuthProvider({ children, session }: AuthProviderProps) {
  const value: AuthContextType = {
    session,
    user: session?.user
      ? {
          id: session.user.id,
          name: session.user.name,
          email: session.user.email,
          image: session.user.image,
          role: (session.user as any).role || "free",
        }
      : { role: "free" },
    isAuthenticated: !!session,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
