/**
 * Campaigns page — list all campaigns with performance metrics.
 *
 * Each campaign card shows name, sending account, daily limit,
 * and aggregated send/open/click/reply/bounce stats.
 */

"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { Campaign, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { percentage } from "@/lib/utils";
import {
  Megaphone,
  Plus,
  Mail,
  MousePointerClick,
  MessageSquareReply,
  AlertTriangle,
  ChevronRight,
  Send,
  Globe,
} from "lucide-react";

export default function CampaignsPage() {
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  const fetchCampaigns = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiRequest<PaginatedResponse<Campaign>>("/api/campaigns?page_size=50");
      setCampaigns(data.items);
    } catch (err) {
      console.error("Failed to fetch campaigns:", err);
      setError("Failed to load campaigns. Please try again.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    fetchCampaigns();
  }, [fetchCampaigns]);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="flex flex-col items-center text-slate-500">
          <div className="mb-4 h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
          <p className="text-sm font-medium">Loading campaigns...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center text-red-500">
        <div className="text-center">
          <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-red-400" />
          <p className="font-medium">{error}</p>
          <Button variant="outline" size="sm" onClick={fetchCampaigns} className="mt-4">
            Try Again
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Campaigns</h1>
          <p className="text-sm text-slate-500">{campaigns.length} campaigns</p>
        </div>
        <Button onClick={() => router.push("/campaigns/new")}>
          <Plus className="mr-1 h-4 w-4" />
          Create Campaign
        </Button>
      </div>

      {campaigns.length === 0 ? (
        <Card>
          <CardContent className="flex h-48 items-center justify-center">
            <div className="text-center text-slate-400">
              <Megaphone className="mx-auto mb-2 h-8 w-8" />
              <p>No campaigns yet</p>
              <Button variant="outline" size="sm" className="mt-3" onClick={() => router.push("/campaigns/new")}>
                Create your first campaign
              </Button>
            </div>
          </CardContent>
        </Card>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
          {campaigns.map((campaign) => (
            <Card
              key={campaign.id}
              className="cursor-pointer transition-shadow hover:shadow-md"
              onClick={() => router.push(`/campaigns/${campaign.id}`)}
            >
              <CardHeader className="pb-3">
                <div className="flex items-start justify-between">
                  <CardTitle className="text-base">{campaign.name}</CardTitle>
                  <ChevronRight className="h-4 w-4 text-slate-400" />
                </div>
                <div className="flex items-center gap-2 text-xs text-slate-500">
                  {campaign.sending_account && (
                    <span className="flex items-center gap-1">
                      <Mail className="h-3 w-3" />
                      {campaign.sending_account}
                    </span>
                  )}
                  <span>·</span>
                  <span>{campaign.daily_limit}/day limit</span>
                </div>
                {campaign.country_scope && campaign.country_scope.length > 0 && (
                  <div className="mt-1 flex gap-1">
                    <Globe className="h-3 w-3 text-slate-400 mt-0.5" />
                    {campaign.country_scope.map((c) => (
                      <Badge key={c} variant="outline" className="text-xs">{c}</Badge>
                    ))}
                  </div>
                )}
              </CardHeader>
              <CardContent>
                {/* Performance Metrics */}
                <div className="grid grid-cols-5 gap-2 text-center">
                  <div className="rounded-lg bg-slate-50 p-2">
                    <Send className="mx-auto mb-1 h-3.5 w-3.5 text-slate-400" />
                    <p className="text-lg font-bold text-slate-900">{campaign.total_sends}</p>
                    <p className="text-xs text-slate-400">Sent</p>
                  </div>
                  <div className="rounded-lg bg-blue-50 p-2">
                    <Mail className="mx-auto mb-1 h-3.5 w-3.5 text-blue-400" />
                    <p className="text-lg font-bold text-blue-600">
                      {percentage(campaign.total_opened, campaign.total_sends)}
                    </p>
                    <p className="text-xs text-blue-400">Opens</p>
                  </div>
                  <div className="rounded-lg bg-indigo-50 p-2">
                    <MousePointerClick className="mx-auto mb-1 h-3.5 w-3.5 text-indigo-400" />
                    <p className="text-lg font-bold text-indigo-600">
                      {percentage(campaign.total_clicked, campaign.total_sends)}
                    </p>
                    <p className="text-xs text-indigo-400">Clicks</p>
                  </div>
                  <div className="rounded-lg bg-green-50 p-2">
                    <MessageSquareReply className="mx-auto mb-1 h-3.5 w-3.5 text-green-400" />
                    <p className="text-lg font-bold text-green-600">
                      {percentage(campaign.total_replied, campaign.total_sends)}
                    </p>
                    <p className="text-xs text-green-400">Replies</p>
                  </div>
                  <div className="rounded-lg bg-red-50 p-2">
                    <AlertTriangle className="mx-auto mb-1 h-3.5 w-3.5 text-red-400" />
                    <p className="text-lg font-bold text-red-600">
                      {percentage(campaign.total_bounced, campaign.total_sends)}
                    </p>
                    <p className="text-xs text-red-400">Bounced</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </div>
  );
}
