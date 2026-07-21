/**
 * Leads page — data table with filtering and sorting.
 *
 * Shows all leads in a paginated table with filters for:
 * - Country, status, size bucket, score range
 * Clicking a row navigates to the lead detail page.
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { Lead, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDate, formatStatus, getStatusColor } from "@/lib/utils";
import { Users, ChevronLeft, ChevronRight, Filter, AlertTriangle } from "lucide-react";

const STATUSES = [
  "", "new", "filtered", "scraping_contacts", "contacts_found", "enriching",
  "enriched", "queued_for_outreach", "sent", "replied", "bounced", "unsubscribed",
];
const COUNTRIES = ["", "US", "UK", "CA"];
const SIZE_BUCKETS = ["", "small", "large"];

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);
  const router = useRouter();

  // Filters
  const [status, setStatus] = useState("");
  const [country, setCountry] = useState("");
  const [sizeBucket, setSizeBucket] = useState("");
  const [scoreMin, setScoreMin] = useState("");
  const [scoreMax, setScoreMax] = useState("");

  const [error, setError] = useState<string | null>(null);

  const fetchLeads = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: page.toString(), page_size: "15" });
      if (status) params.set("status", status);
      if (country) params.set("country", country);
      if (sizeBucket) params.set("size_bucket", sizeBucket);
      if (scoreMin) params.set("score_min", scoreMin);
      if (scoreMax) params.set("score_max", scoreMax);

      const data = await apiRequest<PaginatedResponse<Lead>>(`/api/leads?${params}`);
      setLeads(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error("Failed to fetch leads:", err);
      setError("Failed to load leads. Please check your connection and try again.");
    } finally {
      setLoading(false);
    }
  }, [page, status, country, sizeBucket, scoreMin, scoreMax]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchLeads();
  }, [fetchLeads]);

  // Reset to page 1 when filters change
  const handleFilterChange = () => {
    setPage(1);
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Leads</h1>
          <p className="text-sm text-slate-500">{total} total leads in the pipeline</p>
        </div>
      </div>

      {/* Filters */}
      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center gap-2 text-sm font-medium text-slate-600">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-3">
            <select
              value={status}
              onChange={(e) => { setStatus(e.target.value); handleFilterChange(); }}
              className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-950"
            >
              <option value="">All Statuses</option>
              {STATUSES.filter(Boolean).map((s) => (
                <option key={s} value={s}>{formatStatus(s)}</option>
              ))}
            </select>

            <select
              value={country}
              onChange={(e) => { setCountry(e.target.value); handleFilterChange(); }}
              className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-950"
            >
              <option value="">All Countries</option>
              {COUNTRIES.filter(Boolean).map((c) => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>

            <select
              value={sizeBucket}
              onChange={(e) => { setSizeBucket(e.target.value); handleFilterChange(); }}
              className="h-9 rounded-md border border-slate-200 bg-white px-3 text-sm text-slate-700 focus:outline-none focus:ring-1 focus:ring-slate-950"
            >
              <option value="">All Sizes</option>
              {SIZE_BUCKETS.filter(Boolean).map((s) => (
                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
              ))}
            </select>

            <div className="flex items-center gap-1">
              <Input
                type="number"
                placeholder="Score min"
                value={scoreMin}
                onChange={(e) => { setScoreMin(e.target.value); handleFilterChange(); }}
                className="w-24"
              />
              <span className="text-slate-400">–</span>
              <Input
                type="number"
                placeholder="Score max"
                value={scoreMax}
                onChange={(e) => { setScoreMax(e.target.value); handleFilterChange(); }}
                className="w-24"
              />
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Leads Table */}
      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="flex flex-col items-center text-slate-500">
                <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
                <p className="text-sm font-medium">Loading leads...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex h-64 items-center justify-center text-red-500">
              <div className="text-center">
                <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-red-400" />
                <p className="font-medium">{error}</p>
                <Button variant="outline" size="sm" onClick={fetchLeads} className="mt-4">
                  Try Again
                </Button>
              </div>
            </div>
          ) : leads.length === 0 ? (
            <div className="flex h-64 items-center justify-center text-slate-400">
              <div className="text-center">
                <Users className="mx-auto mb-2 h-8 w-8" />
                <p className="font-medium">No leads discovered yet</p>
                <p className="text-sm mt-1">Adjust your filters or run the discovery scraper to find new leads.</p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50">
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Name</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Company</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Country</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Status</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Score</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Created</th>
                  </tr>
                </thead>
                <tbody>
                  {leads.map((lead) => {
                    const statusColors = getStatusColor(lead.status);
                    return (
                      <tr
                        key={lead.id}
                        onClick={() => router.push(`/leads/${lead.id}`)}
                        className="cursor-pointer border-b border-slate-50 transition-colors hover:bg-slate-50"
                      >
                        <td className="px-4 py-3">
                          <div>
                            <p className="font-medium text-slate-900">{lead.full_name}</p>
                            <p className="text-xs text-slate-400">{lead.job_title || "—"}</p>
                          </div>
                        </td>
                        <td className="px-4 py-3 text-slate-600">{lead.company_name || "—"}</td>
                        <td className="px-4 py-3">
                          <Badge variant="outline" className="text-xs">{lead.company_country || "—"}</Badge>
                        </td>
                        <td className="px-4 py-3">
                          <Badge className={`${statusColors.bg} ${statusColors.text}`}>
                            {formatStatus(lead.status)}
                          </Badge>
                          {lead.is_excluded && (
                            <Badge variant="destructive" className="ml-1 text-xs">Excluded</Badge>
                          )}
                        </td>
                        <td className="px-4 py-3 font-mono text-slate-600">
                          {lead.best_score ?? "—"}
                        </td>
                        <td className="px-4 py-3 text-slate-400">{formatDate(lead.created_at)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
              <p className="text-sm text-slate-500">
                Page {page} of {totalPages} ({total} leads)
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="mr-1 h-4 w-4" />
                  Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next
                  <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
