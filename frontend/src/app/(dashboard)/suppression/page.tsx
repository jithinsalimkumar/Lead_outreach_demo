/**
 * Suppression list page — view, search, add, and remove suppressed entries.
 *
 * Shows a searchable table of suppressed emails/domains with the ability
 * to manually add new entries or remove existing ones.
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import { toast } from "sonner";
import { apiRequest } from "@/lib/api";
import { SuppressionEntry, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDate, formatStatus, getStatusColor } from "@/lib/utils";
import {
  ShieldBan,
  Plus,
  Trash2,
  Search,
  X,
  ChevronLeft,
  ChevronRight,
  AlertTriangle,
} from "lucide-react";

const REASONS = ["bounced", "complained", "unsubscribed", "manual"];

export default function SuppressionPage() {
  const [entries, setEntries] = useState<SuppressionEntry[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Add form state
  const [showAddForm, setShowAddForm] = useState(false);
  const [newEmail, setNewEmail] = useState("");
  const [newReason, setNewReason] = useState("manual");
  const [newCountry, setNewCountry] = useState("");
  const [addError, setAddError] = useState("");

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: page.toString(), page_size: "20" });
      if (search) params.set("search", search);

      const data = await apiRequest<PaginatedResponse<SuppressionEntry>>(
        `/api/suppression?${params}`
      );
      setEntries(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error("Failed to fetch suppression list:", err);
      setError("Failed to load suppression list. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchEntries();
  }, [fetchEntries]);

  const handleAdd = async () => {
    if (!newEmail.trim()) {
      setAddError("Email or domain is required");
      return;
    }

    setAddError("");
    try {
      await apiRequest("/api/suppression", {
        method: "POST",
        body: JSON.stringify({
          email_or_domain: newEmail.trim(),
          reason: newReason,
          country: newCountry.trim() || null,
        }),
      });
      // Reset form and refresh
      setNewEmail("");
      setNewReason("manual");
      setNewCountry("");
      setShowAddForm(false);
      toast.success("Added to suppression list");
      fetchEntries();
    } catch (err) {
      setAddError(err instanceof Error ? err.message : "Failed to add entry");
      toast.error("Failed to add entry");
    }
  };

  const handleRemove = async (id: string) => {
    if (!confirm("Remove this entry from the suppression list?")) return;

    try {
      await apiRequest(`/api/suppression/${id}`, { method: "DELETE" });
      toast.success("Entry removed from suppression list");
      fetchEntries();
    } catch (err) {
      console.error("Failed to remove entry:", err);
      toast.error("Failed to remove entry");
    }
  };

  const getReasonVariant = (reason: string) => {
    switch (reason) {
      case "bounced": return "destructive" as const;
      case "complained": return "warning" as const;
      case "unsubscribed": return "secondary" as const;
      default: return "outline" as const;
    }
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Suppression List</h1>
          <p className="text-sm text-slate-500">{total} suppressed emails/domains</p>
        </div>
        <Button onClick={() => setShowAddForm(!showAddForm)}>
          {showAddForm ? (
            <><X className="mr-1 h-4 w-4" />Cancel</>
          ) : (
            <><Plus className="mr-1 h-4 w-4" />Add Entry</>
          )}
        </Button>
      </div>

      {/* Add Form */}
      {showAddForm && (
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-base">Add Suppression Entry</CardTitle>
          </CardHeader>
          <CardContent>
            {addError && (
              <div className="mb-3 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-600">
                {addError}
              </div>
            )}
            <div className="flex flex-wrap items-end gap-3">
              <div className="flex-1 min-w-[200px]">
                <label className="mb-1 block text-xs font-medium text-slate-500">Email or Domain *</label>
                <Input
                  value={newEmail}
                  onChange={(e) => setNewEmail(e.target.value)}
                  placeholder="e.g. spam@example.com or example.com"
                />
              </div>
              <div className="w-40">
                <label className="mb-1 block text-xs font-medium text-slate-500">Reason</label>
                <select
                  value={newReason}
                  onChange={(e) => setNewReason(e.target.value)}
                  className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
                >
                  {REASONS.map((r) => (
                    <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                  ))}
                </select>
              </div>
              <div className="w-24">
                <label className="mb-1 block text-xs font-medium text-slate-500">Country</label>
                <Input
                  value={newCountry}
                  onChange={(e) => setNewCountry(e.target.value)}
                  placeholder="US"
                />
              </div>
              <Button onClick={handleAdd}>Add</Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Search Bar */}
      <div className="mb-4 flex items-center gap-2">
        <div className="relative flex-1 max-w-sm">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <Input
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            placeholder="Search emails or domains..."
            className="pl-9"
          />
        </div>
      </div>

      {/* Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="flex flex-col items-center text-slate-500">
                <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
                <p className="text-sm font-medium">Loading suppression list...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex h-64 items-center justify-center text-red-500">
              <div className="text-center">
                <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-red-400" />
                <p className="font-medium">{error}</p>
                <Button variant="outline" size="sm" onClick={fetchEntries} className="mt-4">
                  Try Again
                </Button>
              </div>
            </div>
          ) : entries.length === 0 ? (
            <div className="flex h-64 items-center justify-center text-slate-400">
              <div className="text-center">
                <ShieldBan className="mx-auto mb-2 h-8 w-8 text-slate-300" />
                <p className="font-medium">No suppressed entries</p>
                <p className="text-sm mt-1">Your suppression list is clean.</p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50">
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Email / Domain</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Reason</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Country</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Added</th>
                    <th className="px-4 py-3 text-right font-medium text-slate-500">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => (
                    <tr key={entry.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-3 font-mono text-sm text-slate-900">
                        {entry.email_or_domain}
                      </td>
                      <td className="px-4 py-3">
                        <Badge variant={getReasonVariant(entry.reason)}>
                          {entry.reason.charAt(0).toUpperCase() + entry.reason.slice(1)}
                        </Badge>
                      </td>
                      <td className="px-4 py-3 text-slate-500">{entry.country || "—"}</td>
                      <td className="px-4 py-3 text-slate-400">{formatDate(entry.created_at)}</td>
                      <td className="px-4 py-3 text-right">
                        <Button
                          variant="ghost"
                          size="icon"
                          className="h-8 w-8 text-slate-400 hover:text-red-500"
                          onClick={() => handleRemove(entry.id)}
                        >
                          <Trash2 className="h-4 w-4" />
                        </Button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
              <p className="text-sm text-slate-500">
                Page {page} of {totalPages} ({total} entries)
              </p>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
                  <ChevronLeft className="mr-1 h-4 w-4" />Previous
                </Button>
                <Button variant="outline" size="sm" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
                  Next<ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
