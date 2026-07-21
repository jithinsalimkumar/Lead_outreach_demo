/**
 * Auth context — provides authentication state to the entire app.
 *
 * Wraps the React component tree and provides:
 * - Current user state
 * - Login/logout functions
 * - Loading state during initial auth check
 * - Route protection (redirects to /login if not authenticated)
 */

"use client";

import { createContext, useContext, useEffect, useState, ReactNode } from "react";
import { useRouter, usePathname } from "next/navigation";
import { User } from "@/types";
import { apiRequest, login as apiLogin, clearTokens } from "@/lib/api";

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  loading: true,
  login: async () => {},
  logout: () => {},
});

/**
 * Hook to access auth state from any component.
 * Usage: const { user, login, logout } = useAuth();
 */
export function useAuth() {
  return useContext(AuthContext);
}

/**
 * AuthProvider — wraps the app and handles auth state management.
 *
 * On mount, it checks for a stored token and fetches the current user.
 * If the token is expired, it tries to refresh it.
 * If no valid session exists, it redirects to /login.
 */
export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const router = useRouter();
  const pathname = usePathname();

  // Check for existing session on mount
  useEffect(() => {
    async function checkAuth() {
      const token = localStorage.getItem("access_token");
      if (!token) {
        setLoading(false);
        if (pathname !== "/login") {
          router.push("/login");
        }
        return;
      }

      try {
        // Fetch current user to verify the token is valid
        const userData = await apiRequest<User>("/api/auth/me");
        setUser(userData);
      } catch {
        // Token is invalid — clear and redirect
        clearTokens();
        if (pathname !== "/login") {
          router.push("/login");
        }
      } finally {
        setLoading(false);
      }
    }

    checkAuth();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleLogin = async (email: string, password: string) => {
    await apiLogin(email, password);
    // Fetch user data after successful login
    const userData = await apiRequest<User>("/api/auth/me");
    setUser(userData);
    router.push("/dashboard");
  };

  const handleLogout = () => {
    clearTokens();
    setUser(null);
    router.push("/login");
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        loading,
        login: handleLogin,
        logout: handleLogout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}
