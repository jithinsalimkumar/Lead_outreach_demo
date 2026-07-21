/**
 * Utility functions for the frontend.
 */

import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

/**
 * Merges Tailwind CSS classes intelligently.
 * Combines clsx (conditional classes) with tailwind-merge (deduplication).
 *
 * Usage: cn("bg-red-500", isActive && "bg-blue-500", "text-white")
 */
export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

/**
 * Format a date string for display.
 */
export function formatDate(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
  });
}

/**
 * Format a date string with time.
 */
export function formatDateTime(dateStr: string): string {
  return new Date(dateStr).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/**
 * Calculate a percentage, handling division by zero.
 */
export function percentage(value: number, total: number): string {
  if (total === 0) return "0%";
  return `${Math.round((value / total) * 100)}%`;
}

/**
 * Status color mapping for lead pipeline stages.
 * Returns Tailwind CSS classes for background and text colors.
 */
export function getStatusColor(status: string): { bg: string; text: string } {
  const colors: Record<string, { bg: string; text: string }> = {
    new: { bg: "bg-slate-100", text: "text-slate-700" },
    filtered: { bg: "bg-orange-100", text: "text-orange-700" },
    scraping_contacts: { bg: "bg-blue-100", text: "text-blue-700" },
    contacts_found: { bg: "bg-cyan-100", text: "text-cyan-700" },
    enriching: { bg: "bg-indigo-100", text: "text-indigo-700" },
    enriched: { bg: "bg-emerald-100", text: "text-emerald-700" },
    queued_for_outreach: { bg: "bg-violet-100", text: "text-violet-700" },
    sent: { bg: "bg-sky-100", text: "text-sky-700" },
    replied: { bg: "bg-green-100", text: "text-green-700" },
    bounced: { bg: "bg-red-100", text: "text-red-700" },
    unsubscribed: { bg: "bg-gray-100", text: "text-gray-500" },
    // Verification statuses
    verified: { bg: "bg-green-100", text: "text-green-700" },
    unverified: { bg: "bg-yellow-100", text: "text-yellow-700" },
    invalid: { bg: "bg-red-100", text: "text-red-700" },
  };
  return colors[status] || { bg: "bg-gray-100", text: "text-gray-700" };
}

/**
 * Format a status string for display (replace underscores with spaces, capitalize).
 */
export function formatStatus(status: string): string {
  return status
    .replace(/_/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}
