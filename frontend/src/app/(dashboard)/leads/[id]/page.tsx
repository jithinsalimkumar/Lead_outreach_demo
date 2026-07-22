/**
 * Lead detail page — full information about a single lead.
 *
 * Shows:
 * - Company info, job posting that triggered discovery
 * - Enrichment data (email, phone, verification, score)
 * - Campaign send history with engagement indicators
 * - "Mark as excluded" toggle
 */

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { LeadDetail } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  formatDate,
  formatDateTime,
  formatStatus,
  getStatusColor,
} from "@/lib/utils";
import {
  ArrowLeft,
  Building2,
  Briefcase,
  Mail,
  Phone,
  ShieldBan,
  ShieldCheck,
  CheckCircle,
  XCircle,
  Clock,
  Send,
  MousePointerClick,
  MessageSquareReply,
  AlertTriangle,
} from "lucide-react";

import { toast } from "sonner";

export default function LeadDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [lead, setLead] = useState<LeadDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [excluding, setExcluding] = useState(false);

  useEffect(() => {
    async function fetchLead() {
      try {
        setError(null);
        const data = await apiRequest<LeadDetail>(`/api/leads/${params.id}`);
        setLead(data);
      } catch (err) {
        console.error("Failed to fetch lead:", err);
        setError("Failed to load lead details. Please try again.");
      } finally {
        setLoading(false);
      }
    }
    fetchLead();
  }, [params.id]);

  const toggleExclude = async () => {
    if (!lead) return;
    setExcluding(true);
    try {
      await apiRequest(`/api/leads/${lead.id}/exclude`, {
        method: "PATCH",
        body: JSON.stringify({ is_excluded: !lead.is_excluded }),
      });
      setLead({ ...lead, is_excluded: !lead.is_excluded });
      toast.success(`Lead ${!lead.is_excluded ? "excluded" : "restored"} successfully`);
    } catch (err) {
      console.error("Failed to toggle exclude:", err);
      toast.error("Failed to update lead status");
    } finally {
      setExcluding(false);
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex flex-col items-center text-slate-500">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
          <p className="text-sm font-medium">Loading lead details...</p>
        </div>
      </div>
    );
  }

  if (error || !lead) {
    return (
      <div className="flex h-64 items-center justify-center text-red-500">
        <div className="text-center">
          <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-red-400" />
          <p className="font-medium">{error || "Lead not found"}</p>
        </div>
      </div>
    );
  }

  const statusColors = getStatusColor(lead.status);

  return (
    <div>
      {/* Header */}
      <div className="mb-6">
        <Button variant="ghost" size="sm" onClick={() => router.push("/leads")} className="mb-3">
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back to Leads
        </Button>
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{lead.full_name}</h1>
            <p className="text-sm text-slate-500">{lead.job_title || "No title"}</p>
            <div className="mt-2 flex items-center gap-2">
              <Badge className={`${statusColors.bg} ${statusColors.text}`}>
                {formatStatus(lead.status)}
              </Badge>
              {lead.is_excluded && (
                <Badge variant="destructive">Excluded</Badge>
              )}
            </div>
          </div>
          <Button
            variant={lead.is_excluded ? "outline" : "destructive"}
            size="sm"
            onClick={toggleExclude}
            disabled={excluding}
          >
            {lead.is_excluded ? (
              <><ShieldCheck className="mr-1 h-4 w-4" />Restore Lead</>
            ) : (
              <><ShieldBan className="mr-1 h-4 w-4" />Mark Excluded</>
            )}
          </Button>
        </div>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Company Info */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Building2 className="h-4 w-4 text-slate-500" />
              Company
            </CardTitle>
          </CardHeader>
          <CardContent>
            {lead.company ? (
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-slate-500">Name</span>
                  <span className="font-medium">{lead.company.name}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Domain</span>
                  <a href={lead.company.domain?.startsWith('http') ? lead.company.domain : `https://${lead.company.domain}`} target="_blank" rel="noopener" className="text-blue-600 hover:underline">
                    {lead.company.domain}
                  </a>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Country</span>
                  <Badge variant="outline">{lead.company.country}</Badge>
                </div>
                <div className="flex justify-between">
                  <span className="text-slate-500">Size</span>
                  <span>{lead.company.employee_size_estimate ?? "Unknown"} employees ({lead.company.size_bucket})</span>
                </div>
              </div>
            ) : (
              <p className="text-slate-400">No company data</p>
            )}
          </CardContent>
        </Card>

        {/* LinkedIn / Contact */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Phone className="h-4 w-4 text-slate-500" />
              Contact Info
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2 text-sm">
              {lead.linkedin_url && (
                <div className="flex justify-between">
                  <span className="text-slate-500">LinkedIn</span>
                  <a href={lead.linkedin_url} target="_blank" rel="noopener" className="text-blue-600 hover:underline">
                    View Profile →
                  </a>
                </div>
              )}
              <div className="flex justify-between">
                <span className="text-slate-500">Created</span>
                <span>{formatDate(lead.created_at)}</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Job Postings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Briefcase className="h-4 w-4 text-slate-500" />
              Job Postings ({lead.job_postings.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {lead.job_postings.length === 0 ? (
              <p className="text-sm text-slate-400">No job postings</p>
            ) : (
              <div className="space-y-3">
                {lead.job_postings.map((jp) => (
                  <div key={jp.id} className="rounded-lg border border-slate-100 p-3">
                    <div className="flex items-center justify-between">
                      <p className="font-medium text-slate-900 text-sm">{jp.title}</p>
                      <Badge variant="secondary" className="text-xs">{jp.portal}</Badge>
                    </div>
                    <div className="mt-1 flex gap-2 text-xs text-slate-400">
                      <span>{formatStatus(jp.tier_signal)}</span>
                      <span>·</span>
                      <span>{jp.location || "Unknown location"}</span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Enrichment Data */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Mail className="h-4 w-4 text-slate-500" />
              Enrichment Data ({lead.enrichment_data.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            {lead.enrichment_data.length === 0 ? (
              <p className="text-sm text-slate-400">No enrichment data yet</p>
            ) : (
              <div className="space-y-3">
                {lead.enrichment_data.map((e) => {
                  const vColors = getStatusColor(e.verification_status);
                  return (
                    <div key={e.id} className="rounded-lg border border-slate-100 p-3">
                      <div className="flex items-center justify-between mb-2">
                        <Badge className={`${vColors.bg} ${vColors.text}`}>
                          {formatStatus(e.verification_status)}
                        </Badge>
                        <Badge variant="secondary" className="text-xs">{e.provider}</Badge>
                      </div>
                      <div className="space-y-1 text-sm">
                        {e.email && (
                          <div className="flex items-center gap-2 text-slate-600">
                            <Mail className="h-3 w-3" />
                            {e.email}
                          </div>
                        )}
                        {e.phone && (
                          <div className="flex items-center gap-2 text-slate-600">
                            <Phone className="h-3 w-3" />
                            {e.phone}
                          </div>
                        )}
                        {e.score !== null && (
                          <div className="flex items-center gap-2 text-slate-600">
                            Score: <span className="font-mono font-semibold">{e.score}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Send History */}
      <Card className="mt-6">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-base">
            <Send className="h-4 w-4 text-slate-500" />
            Send History ({lead.campaign_sends.length})
          </CardTitle>
        </CardHeader>
        <CardContent>
          {lead.campaign_sends.length === 0 ? (
            <p className="text-sm text-slate-400">No sends yet</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50">
                    <th className="px-3 py-2 text-left font-medium text-slate-500">Campaign</th>
                    <th className="px-3 py-2 text-left font-medium text-slate-500">Step</th>
                    <th className="px-3 py-2 text-left font-medium text-slate-500">Sent At</th>
                    <th className="px-3 py-2 text-center font-medium text-slate-500">Opened</th>
                    <th className="px-3 py-2 text-center font-medium text-slate-500">Clicked</th>
                    <th className="px-3 py-2 text-center font-medium text-slate-500">Replied</th>
                    <th className="px-3 py-2 text-center font-medium text-slate-500">Bounced</th>
                  </tr>
                </thead>
                <tbody>
                  {lead.campaign_sends.map((send) => (
                    <tr key={send.id} className="border-b border-slate-50">
                      <td className="px-3 py-2 font-medium text-slate-700">{send.campaign_name || "—"}</td>
                      <td className="px-3 py-2"><Badge variant="outline">Step {send.sequence_step}</Badge></td>
                      <td className="px-3 py-2 text-slate-500">{send.sent_at ? formatDateTime(send.sent_at) : "—"}</td>
                      <td className="px-3 py-2 text-center">{send.opened ? <CheckCircle className="mx-auto h-4 w-4 text-blue-500" /> : <XCircle className="mx-auto h-4 w-4 text-slate-200" />}</td>
                      <td className="px-3 py-2 text-center">{send.clicked ? <CheckCircle className="mx-auto h-4 w-4 text-indigo-500" /> : <XCircle className="mx-auto h-4 w-4 text-slate-200" />}</td>
                      <td className="px-3 py-2 text-center">{send.replied ? <CheckCircle className="mx-auto h-4 w-4 text-green-500" /> : <XCircle className="mx-auto h-4 w-4 text-slate-200" />}</td>
                      <td className="px-3 py-2 text-center">{send.bounced ? <AlertTriangle className="mx-auto h-4 w-4 text-red-500" /> : <XCircle className="mx-auto h-4 w-4 text-slate-200" />}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
