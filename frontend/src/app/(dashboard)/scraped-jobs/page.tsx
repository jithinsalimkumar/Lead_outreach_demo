/**
 * Scraped Jobs page — data table with filtering and CSV export.
 *
 * Shows all scraped job postings in a paginated table with filters for:
 * - Country, portal, tier signal
 * Includes a CSV export function.
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import { apiRequest } from "@/lib/api";
import { ScrapedJob, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { formatDate } from "@/lib/utils";
import { toast } from "sonner";
import { Download, ChevronLeft, ChevronRight, Filter, Search, AlertTriangle, Briefcase } from "lucide-react";

const COUNTRIES = ["", "US", "UK", "CA"];
const PORTALS = ["", "linkedin", "indeed"];
const TIER_SIGNALS = ["", "email_marketer", "digital_marketer", "general_marketer", "email_agency"];

export default function ScrapedJobsPage() {
  const [jobs, setJobs] = useState<ScrapedJob[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [totalPages, setTotalPages] = useState(1);
  const [loading, setLoading] = useState(true);

  // Filters
  const [search, setSearch] = useState("");
  const [country, setCountry] = useState("");
  const [portal, setPortal] = useState("");
  const [tierSignal, setTierSignal] = useState("");

  const [error, setError] = useState<string | null>(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = new URLSearchParams({ page: page.toString(), page_size: "15" });
      if (search) params.set("search", search);
      if (country) params.set("country", country);
      if (portal) params.set("portal", portal);
      if (tierSignal) params.set("tier_signal", tierSignal);

      const data = await apiRequest<PaginatedResponse<ScrapedJob>>(`/api/scraped-jobs?${params}`);
      setJobs(data.items);
      setTotal(data.total);
      setTotalPages(data.total_pages);
    } catch (err) {
      console.error("Failed to fetch scraped jobs:", err);
      setError("Failed to load scraped jobs. Please try again.");
    } finally {
      setLoading(false);
    }
  }, [page, search, country, portal, tierSignal]);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchJobs();
  }, [fetchJobs]);

  const handleExport = async () => {
    try {
      const params = new URLSearchParams();
      if (search) params.set("search", search);
      if (country) params.set("country", country);
      if (portal) params.set("portal", portal);
      if (tierSignal) params.set("tier_signal", tierSignal);

      const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/api/scraped-jobs/export?${params}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('access_token')}`
        }
      });
      
      if (!response.ok) throw new Error("Export failed");
      
      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `scraped_jobs_${new Date().toISOString().split('T')[0]}.csv`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
      toast.success("Export downloaded successfully");
    } catch (err) {
      console.error("Failed to export jobs:", err);
      toast.error("Failed to export jobs");
    }
  };

  const getTierSignalColor = (tier: string) => {
    switch (tier) {
      case "email_marketer": return "bg-green-100 text-green-700";
      case "digital_marketer": return "bg-blue-100 text-blue-700";
      case "email_agency": return "bg-purple-100 text-purple-700";
      default: return "bg-slate-100 text-slate-700";
    }
  };

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Scraped Jobs</h1>
          <p className="text-sm text-slate-500">{total} total job postings discovered</p>
        </div>
        <Button onClick={handleExport} variant="outline" className="gap-2">
          <Download className="h-4 w-4" />
          Export CSV
        </Button>
      </div>

      <Card className="mb-6">
        <CardHeader className="pb-3">
          <CardTitle className="flex items-center text-sm font-medium text-slate-500">
            <Filter className="mr-2 h-4 w-4" />
            Filters & Search
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap items-end gap-4">
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                <Input
                  value={search}
                  onChange={(e) => { setSearch(e.target.value); setPage(1); }}
                  placeholder="Search company or job title..."
                  className="pl-9"
                />
              </div>
            </div>
            <div className="w-40">
              <select
                value={country}
                onChange={(e) => { setCountry(e.target.value); setPage(1); }}
                className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm"
              >
                <option value="">All Countries</option>
                {COUNTRIES.filter(Boolean).map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </div>
            <div className="w-40">
              <select
                value={portal}
                onChange={(e) => { setPortal(e.target.value); setPage(1); }}
                className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm capitalize"
              >
                <option value="">All Portals</option>
                {PORTALS.filter(Boolean).map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </div>
            <div className="w-48">
              <select
                value={tierSignal}
                onChange={(e) => { setTierSignal(e.target.value); setPage(1); }}
                className="h-9 w-full rounded-md border border-slate-200 bg-white px-3 text-sm capitalize"
              >
                <option value="">All Tiers</option>
                {TIER_SIGNALS.filter(Boolean).map((t) => (
                  <option key={t} value={t}>{t.replace("_", " ")}</option>
                ))}
              </select>
            </div>
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardContent className="p-0">
          {loading ? (
            <div className="flex h-64 items-center justify-center">
              <div className="flex flex-col items-center text-slate-500">
                <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
                <p className="text-sm font-medium">Loading jobs...</p>
              </div>
            </div>
          ) : error ? (
            <div className="flex h-64 items-center justify-center text-red-500">
              <div className="text-center">
                <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-red-400" />
                <p className="font-medium">{error}</p>
                <Button variant="outline" size="sm" onClick={fetchJobs} className="mt-4">
                  Try Again
                </Button>
              </div>
            </div>
          ) : jobs.length === 0 ? (
            <div className="flex h-64 items-center justify-center text-slate-400">
              <div className="text-center">
                <Briefcase className="mx-auto mb-2 h-8 w-8" />
                <p className="font-medium">No companies discovered yet</p>
                <p className="text-sm mt-1">Run the discovery scraper to find new job postings.</p>
              </div>
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50">
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Company</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Company Domain</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Job Title</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Job URL</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Portal</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Country</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Tier Signal</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Scraped At</th>
                  </tr>
                </thead>
                <tbody>
                  {jobs.map((job) => (
                    <tr key={job.id} className="border-b border-slate-50 hover:bg-slate-50">
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900">{job.company_name}</div>
                      </td>
                      <td className="px-4 py-3">
                        <a 
                          href={`https://${job.company_domain}`} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:underline"
                        >
                          {job.company_domain}
                        </a>
                      </td>
                      <td className="px-4 py-3">
                        <div className="font-medium text-slate-900">{job.job_title}</div>
                        <div className="text-xs text-slate-500">{job.location || 'Remote'}</div>
                      </td>
                      <td className="px-4 py-3">
                        <a 
                          href={job.job_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-sm text-blue-600 hover:underline line-clamp-1 max-w-[200px]"
                          title={job.job_url}
                        >
                          View Job
                        </a>
                      </td>
                      <td className="px-4 py-3 capitalize">{job.portal}</td>
                      <td className="px-4 py-3">
                        <Badge variant="outline">{job.country}</Badge>
                      </td>
                      <td className="px-4 py-3">
                        <span className={`inline-flex items-center rounded-full px-2 py-0.5 text-xs font-medium ${getTierSignalColor(job.tier_signal)}`}>
                          {job.tier_signal.replace("_", " ")}
                        </span>
                      </td>
                      <td className="px-4 py-3 text-slate-500">
                        {formatDate(job.scraped_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {totalPages > 1 && (
            <div className="flex items-center justify-between border-t border-slate-100 px-4 py-3">
              <p className="text-sm text-slate-500">
                Page {page} of {totalPages}
              </p>
              <div className="flex gap-2">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage((p) => p - 1)}
                >
                  <ChevronLeft className="mr-1 h-4 w-4" /> Previous
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage((p) => p + 1)}
                >
                  Next <ChevronRight className="ml-1 h-4 w-4" />
                </Button>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
