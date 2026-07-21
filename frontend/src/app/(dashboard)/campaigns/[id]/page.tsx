/**
 * Campaign detail page — shows all leads in a campaign and their send status.
 *
 * Displays campaign metadata, aggregate performance metrics,
 * and a table of all leads with per-step engagement indicators.
 */

"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { CampaignDetail } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { formatDate, formatDateTime, percentage } from "@/lib/utils";
import {
  ArrowLeft,
  Mail,
  Send,
  MousePointerClick,
  MessageSquareReply,
  AlertTriangle,
  CheckCircle,
  XCircle,
  Globe,
} from "lucide-react";

export default function CampaignDetailPage() {
  const params = useParams();
  const router = useRouter();
  const [campaign, setCampaign] = useState<CampaignDetail | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchCampaign() {
      try {
        const data = await apiRequest<CampaignDetail>(`/api/campaigns/${params.id}`);
        setCampaign(data);
      } catch (err) {
        console.error("Failed to fetch campaign:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchCampaign();
  }, [params.id]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
      </div>
    );
  }

  if (!campaign) {
    return <div className="text-red-500">Campaign not found</div>;
  }

  return (
    <div>
      {/* Header */}
      <Button variant="ghost" size="sm" onClick={() => router.push("/campaigns")} className="mb-3">
        <ArrowLeft className="mr-1 h-4 w-4" />
        Back to Campaigns
      </Button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">{campaign.name}</h1>
        <div className="mt-1 flex flex-wrap items-center gap-3 text-sm text-slate-500">
          {campaign.sending_account && (
            <span className="flex items-center gap-1">
              <Mail className="h-3.5 w-3.5" />
              {campaign.sending_account}
            </span>
          )}
          <span>Daily limit: {campaign.daily_limit}</span>
          {campaign.country_scope && campaign.country_scope.length > 0 && (
            <span className="flex items-center gap-1">
              <Globe className="h-3.5 w-3.5" />
              {campaign.country_scope.join(", ")}
            </span>
          )}
          <span>Created {formatDate(campaign.created_at)}</span>
        </div>
      </div>

      {/* Performance Summary */}
      <div className="mb-6 grid grid-cols-5 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <Send className="mx-auto mb-1 h-5 w-5 text-slate-400" />
            <p className="text-2xl font-bold">{campaign.total_sends}</p>
            <p className="text-xs text-slate-500">Total Sends</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Mail className="mx-auto mb-1 h-5 w-5 text-blue-500" />
            <p className="text-2xl font-bold text-blue-600">
              {percentage(campaign.total_opened, campaign.total_sends)}
            </p>
            <p className="text-xs text-slate-500">{campaign.total_opened} Opens</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <MousePointerClick className="mx-auto mb-1 h-5 w-5 text-indigo-500" />
            <p className="text-2xl font-bold text-indigo-600">
              {percentage(campaign.total_clicked, campaign.total_sends)}
            </p>
            <p className="text-xs text-slate-500">{campaign.total_clicked} Clicks</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <MessageSquareReply className="mx-auto mb-1 h-5 w-5 text-green-500" />
            <p className="text-2xl font-bold text-green-600">
              {percentage(campaign.total_replied, campaign.total_sends)}
            </p>
            <p className="text-xs text-slate-500">{campaign.total_replied} Replies</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <AlertTriangle className="mx-auto mb-1 h-5 w-5 text-red-500" />
            <p className="text-2xl font-bold text-red-600">
              {percentage(campaign.total_bounced, campaign.total_sends)}
            </p>
            <p className="text-xs text-slate-500">{campaign.total_bounced} Bounced</p>
          </CardContent>
        </Card>
      </div>

      {/* Leads Table */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">
            Campaign Leads ({campaign.leads.length})
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {campaign.leads.length === 0 ? (
            <div className="flex h-32 items-center justify-center text-sm text-slate-400">
              No leads in this campaign yet
            </div>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-slate-100 bg-slate-50/50">
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Lead</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Company</th>
                    <th className="px-4 py-3 text-left font-medium text-slate-500">Email</th>
                    <th className="px-4 py-3 text-center font-medium text-slate-500">Step 1</th>
                    <th className="px-4 py-3 text-center font-medium text-slate-500">Step 2</th>
                    <th className="px-4 py-3 text-center font-medium text-slate-500">Step 3</th>
                  </tr>
                </thead>
                <tbody>
                  {campaign.leads.map((lead) => {
                    // Build a map of sends by step
                    const sendsByStep: Record<number, typeof lead.sends[0]> = {};
                    lead.sends.forEach((s) => { sendsByStep[s.sequence_step] = s; });

                    return (
                      <tr key={lead.lead_id} className="border-b border-slate-50 hover:bg-slate-50">
                        <td className="px-4 py-3">
                          <p className="font-medium text-slate-900">{lead.full_name}</p>
                          <p className="text-xs text-slate-400">{lead.job_title || "—"}</p>
                        </td>
                        <td className="px-4 py-3 text-slate-600">{lead.company_name || "—"}</td>
                        <td className="px-4 py-3 text-slate-600 font-mono text-xs">
                          {lead.email || "—"}
                        </td>
                        {[1, 2, 3].map((step) => {
                          const send = sendsByStep[step];
                          if (!send) {
                            return (
                              <td key={step} className="px-4 py-3 text-center text-slate-200">
                                —
                              </td>
                            );
                          }
                          return (
                            <td key={step} className="px-4 py-3">
                              <div className="flex items-center justify-center gap-1">
                                {send.bounced ? (
                                  <AlertTriangle className="h-3.5 w-3.5 text-red-500" title="Bounced" />
                                ) : send.replied ? (
                                  <MessageSquareReply className="h-3.5 w-3.5 text-green-500" title="Replied" />
                                ) : send.clicked ? (
                                  <MousePointerClick className="h-3.5 w-3.5 text-indigo-500" title="Clicked" />
                                ) : send.opened ? (
                                  <Mail className="h-3.5 w-3.5 text-blue-500" title="Opened" />
                                ) : send.sent_at ? (
                                  <Send className="h-3.5 w-3.5 text-slate-400" title="Sent" />
                                ) : (
                                  <span className="text-xs text-slate-300">Queued</span>
                                )}
                              </div>
                              {send.sent_at && (
                                <p className="mt-0.5 text-center text-xs text-slate-400">
                                  {formatDate(send.sent_at)}
                                </p>
                              )}
                            </td>
                          );
                        })}
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
