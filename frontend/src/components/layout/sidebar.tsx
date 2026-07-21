/**
 * Sidebar navigation — main nav for the app.
 *
 * Shows navigation links and highlights the active page.
 * Settings link is only visible to admin users.
 */

"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useAuth } from "@/lib/auth";
import { cn } from "@/lib/utils";
import {
  LayoutDashboard,
  Users,
  Megaphone,
  ShieldBan,
  Settings,
  LogOut,
  Briefcase,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/scraped-jobs", label: "Scraped Jobs", icon: Briefcase },
  { href: "/leads", label: "Leads", icon: Users },
  { href: "/campaigns", label: "Campaigns", icon: Megaphone },
  { href: "/suppression", label: "Suppression", icon: ShieldBan },
];

export function Sidebar() {
  const pathname = usePathname();
  const { user, logout } = useAuth();

  return (
    <aside className="fixed left-0 top-0 z-40 flex h-screen w-64 flex-col border-r border-slate-800 bg-slate-950 text-slate-300">
      {/* Logo / Brand */}
      <div className="flex h-16 items-center gap-2 border-b border-slate-800 px-6">
        <Image src="/logo.png" alt="LeadOutreach Logo" width={32} height={32} className="object-contain" />
        <span className="text-lg font-bold text-white">LeadOutreach</span>
      </div>

      {/* Navigation Links */}
      <nav className="flex-1 space-y-1 px-3 py-4">
        {navItems.map((item) => {
          const isActive = pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
                isActive
                  ? "bg-slate-800 text-white"
                  : "text-slate-400 hover:bg-slate-900 hover:text-white"
              )}
            >
              <item.icon className="h-5 w-5" />
              {item.label}
            </Link>
          );
        })}

        {/* Settings — admin only */}
        {user?.role === "admin" && (
          <Link
            href="/settings"
            className={cn(
              "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors",
              pathname.startsWith("/settings")
                ? "bg-slate-800 text-white"
                : "text-slate-400 hover:bg-slate-900 hover:text-white"
            )}
          >
            <Settings className="h-5 w-5" />
            Settings
          </Link>
        )}
      </nav>

      {/* User Info & Logout */}
      <div className="border-t border-slate-800 p-4">
        <div className="mb-2 px-3">
          <p className="text-sm font-medium text-white">{user?.email}</p>
          <p className="text-xs text-slate-500 capitalize">{user?.role}</p>
        </div>
        <button
          onClick={logout}
          className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm text-slate-400 transition-colors hover:bg-slate-900 hover:text-white"
        >
          <LogOut className="h-4 w-4" />
          Sign out
        </button>
      </div>
    </aside>
  );
}
