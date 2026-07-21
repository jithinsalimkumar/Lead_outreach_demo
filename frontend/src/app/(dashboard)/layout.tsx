/**
 * Dashboard layout — wraps all authenticated pages with sidebar.
 *
 * This is a Next.js layout group for all pages that require authentication.
 * The AuthProvider handles checking the token and redirecting to login.
 */

"use client";

import { AuthProvider } from "@/lib/auth";
import { Sidebar } from "@/components/layout/sidebar";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <AuthProvider>
      <div className="flex min-h-screen">
        <Sidebar />
        {/* Main content area — offset by sidebar width (16rem = w-64) */}
        <main className="ml-64 flex-1 p-8">{children}</main>
      </div>
    </AuthProvider>
  );
}
