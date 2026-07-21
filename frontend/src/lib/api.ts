/**
 * API client — handles all HTTP requests to the backend.
 *
 * Features:
 * - Attaches JWT access token to every request
 * - Automatically refreshes the token on 401 responses
 * - Base URL configurable via NEXT_PUBLIC_API_URL env var
 */

import { TokenResponse } from "@/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * Get stored tokens from localStorage.
 * Returns null if not logged in.
 */
function getTokens(): { access: string; refresh: string } | null {
  if (typeof window === "undefined") return null;
  const access = localStorage.getItem("access_token");
  const refresh = localStorage.getItem("refresh_token");
  if (!access || !refresh) return null;
  return { access, refresh };
}

/**
 * Save tokens to localStorage after login or refresh.
 */
export function saveTokens(access: string, refresh: string): void {
  localStorage.setItem("access_token", access);
  localStorage.setItem("refresh_token", refresh);
}

/**
 * Clear tokens from localStorage (logout).
 */
export function clearTokens(): void {
  localStorage.removeItem("access_token");
  localStorage.removeItem("refresh_token");
}

/**
 * Try to refresh the access token using the refresh token.
 * Returns true if successful, false if the refresh token is also expired.
 */
async function tryRefreshToken(): Promise<boolean> {
  const tokens = getTokens();
  if (!tokens) return false;

  try {
    const response = await fetch(`${API_BASE}/api/auth/refresh`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ refresh_token: tokens.refresh }),
    });

    if (!response.ok) return false;

    const data: TokenResponse = await response.json();
    saveTokens(data.access_token, data.refresh_token);
    return true;
  } catch {
    return false;
  }
}

/**
 * Main API request function.
 *
 * Wraps fetch() with:
 * - Automatic Authorization header
 * - JSON content type
 * - Token refresh on 401
 * - Error handling with meaningful messages
 */
export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const tokens = getTokens();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  // Add auth header if we have a token
  if (tokens) {
    headers["Authorization"] = `Bearer ${tokens.access}`;
  }

  let response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers,
  });

  // If we get a 401 and have a refresh token, try refreshing
  if (response.status === 401 && tokens) {
    const refreshed = await tryRefreshToken();
    if (refreshed) {
      // Retry the request with the new token
      const newTokens = getTokens();
      if (newTokens) {
        headers["Authorization"] = `Bearer ${newTokens.access}`;
      }
      response = await fetch(`${API_BASE}${path}`, {
        ...options,
        headers,
      });
    } else {
      // Refresh failed — redirect to login
      clearTokens();
      if (typeof window !== "undefined") {
        window.location.href = "/login";
      }
      throw new Error("Session expired. Please log in again.");
    }
  }

  // Handle error responses
  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "An error occurred" }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

/**
 * Login — authenticates with email/password and stores tokens.
 */
export async function login(email: string, password: string): Promise<TokenResponse> {
  const response = await fetch(`${API_BASE}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: "Login failed" }));
    throw new Error(error.detail || "Login failed");
  }

  const data: TokenResponse = await response.json();
  saveTokens(data.access_token, data.refresh_token);
  return data;
}
