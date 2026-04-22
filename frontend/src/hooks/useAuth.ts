import { useEffect, useState } from "react";
import { cachedUser, clearSession, hasSession, type User } from "@/api/auth";

export function useAuth() {
  const [user, setUser] = useState<User | null>(cachedUser());

  useEffect(() => {
    // Listen for session changes from other tabs / login flow.
    const sync = () => setUser(cachedUser());
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);

  return {
    user,
    isAuthenticated: hasSession() && !!user,
    signOut: () => {
      clearSession();
      setUser(null);
      window.location.href = "/login";
    },
    refresh: () => setUser(cachedUser()),
  };
}
