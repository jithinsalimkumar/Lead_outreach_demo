/**
 * Dashboard page — overview of the lead pipeline and campaign performance.
 *
 * Shows:
 * - Total leads and companies counts
 * - Leads discovered this week
 * - Pipeline stage breakdown with color-coded badges
 * - Campaign performance metrics (open/click/reply/bounce rates)
 */

"use client";

import { useEffect, useState } from "react";
import { apiRequest } from "@/lib/api";
import { DashboardStats } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { formatStatus, getStatusColor, percentage } from "@/lib/utils";
import {
  Users,
  Building2,
  TrendingUp,
  Mail,
  MousePointerClick,
  MessageSquareReply,
  AlertTriangle,
  Sparkles,
} from "lucide-react";

export default function DashboardPage() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchStats() {
      try {
        setError(null);
        const data = await apiRequest<DashboardStats>("/api/dashboard/stats");
        setStats(data);
      } catch (err) {
        console.error("Failed to fetch dashboard stats:", err);
        setError("Failed to load dashboard statistics. Please try again.");
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <div className="h-8 w-8 animate-spin rounded-full border-4 border-slate-200 border-t-slate-900" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex h-64 items-center justify-center text-red-500">
        <div className="text-center">
          <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-red-400" />
          <p className="font-medium">{error}</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex h-64 items-center justify-center text-red-500">
        <div className="text-center">
          <AlertTriangle className="mx-auto mb-2 h-8 w-8 text-red-400" />
          <p className="font-medium">Failed to load dashboard data.</p>
        </div>
      </div>
    );
  }

  const cp = stats.campaign_performance;

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="text-sm text-slate-500">Overview of your lead outreach pipeline</p>
      </div>

      {/* Top-level KPI Cards */}
      <div className="mb-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Total Leads</CardTitle>
            <Users className="h-4 w-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total_leads}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Companies</CardTitle>
            <Building2 className="h-4 w-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{stats.total_companies}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Discovered This Week</CardTitle>
            <Sparkles className="h-4 w-4 text-emerald-500" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-600">{stats.leads_discovered_this_week}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-slate-500">Total Sends</CardTitle>
            <Mail className="h-4 w-4 text-slate-400" />
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">{cp.total_sends}</div>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Pipeline Breakdown */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="h-5 w-5 text-slate-500" />
              Lead Pipeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {Object.entries(stats.leads_by_status).map(([status, count]) => {
                const colors = getStatusColor(status);
                const total = stats.total_leads || 1;
                const pct = Math.round((count / total) * 100);
                return (
                  <div key={status} className="flex items-center gap-3">
                    <div className="w-36">
                      <Badge className={`${colors.bg} ${colors.text}`}>
                        {formatStatus(status)}
                      </Badge>
                    </div>
                    <div className="flex-1">
                      <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                        <div
                          className={`h-full rounded-full transition-all ${colors.bg.replace('100', '400')}`}
                          style={{ width: `${Math.max(pct, 1)}%` }}
                        />
                      </div>
                    </div>
                    <span className="w-10 text-right text-sm font-medium text-slate-600">
                      {count}
                    </span>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Campaign Performance */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Mail className="h-5 w-5 text-slate-500" />
              Campaign Performance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              {/* Open Rate */}
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <Mail className="h-4 w-4" />
                    Opens
                  </div>
                  <span className="text-sm font-semibold">{cp.open_rate}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-blue-400 transition-all" style={{ width: `${cp.open_rate}%` }} />
                </div>
                <p className="mt-1 text-xs text-slate-400">{cp.total_opened} of {cp.total_sends} emails opened</p>
              </div>

              {/* Click Rate */}
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <MousePointerClick className="h-4 w-4" />
                    Clicks
                  </div>
                  <span className="text-sm font-semibold">{cp.click_rate}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-indigo-400 transition-all" style={{ width: `${cp.click_rate}%` }} />
                </div>
                <p className="mt-1 text-xs text-slate-400">{cp.total_clicked} of {cp.total_sends} emails clicked</p>
              </div>

              {/* Reply Rate */}
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <MessageSquareReply className="h-4 w-4" />
                    Replies
                  </div>
                  <span className="text-sm font-semibold text-green-600">{cp.reply_rate}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-green-400 transition-all" style={{ width: `${cp.reply_rate}%` }} />
                </div>
                <p className="mt-1 text-xs text-slate-400">{cp.total_replied} of {cp.total_sends} emails replied</p>
              </div>

              {/* Bounce Rate */}
              <div>
                <div className="mb-1 flex items-center justify-between">
                  <div className="flex items-center gap-2 text-sm text-slate-600">
                    <AlertTriangle className="h-4 w-4" />
                    Bounces
                  </div>
                  <span className="text-sm font-semibold text-red-600">{cp.bounce_rate}%</span>
                </div>
                <div className="h-2 overflow-hidden rounded-full bg-slate-100">
                  <div className="h-full rounded-full bg-red-400 transition-all" style={{ width: `${cp.bounce_rate}%` }} />
                </div>
                <p className="mt-1 text-xs text-slate-400">{cp.total_bounced} of {cp.total_sends} emails bounced</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
