/**
 * Create Campaign page — form to set up a new outreach campaign.
 *
 * Lets the user:
 * - Name the campaign
 * - Set a sending account and daily limit
 * - Select target countries
 * - Choose leads to include (filtered to status = enriched)
 */

"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { apiRequest } from "@/lib/api";
import { Lead, PaginatedResponse } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowLeft, Check } from "lucide-react";

const COUNTRIES = ["US", "UK", "CA"];

export default function CreateCampaignPage() {
  const router = useRouter();
  const [name, setName] = useState("");
  const [sendingAccount, setSendingAccount] = useState("");
  const [dailyLimit, setDailyLimit] = useState("50");
  const [countryScope, setCountryScope] = useState<string[]>([]);
  const [enrichedLeads, setEnrichedLeads] = useState<Lead[]>([]);
  const [selectedLeadIds, setSelectedLeadIds] = useState<Set<string>>(new Set());
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState("");

  // Fetch enriched leads available for campaign
  useEffect(() => {
    async function fetchLeads() {
      try {
        const data = await apiRequest<PaginatedResponse<Lead>>(
          "/api/leads?status=enriched&page_size=100"
        );
        setEnrichedLeads(data.items);
      } catch (err) {
        console.error("Failed to fetch enriched leads:", err);
      }
    }
    fetchLeads();
  }, []);

  const toggleCountry = (c: string) => {
    setCountryScope((prev) =>
      prev.includes(c) ? prev.filter((x) => x !== c) : [...prev, c]
    );
  };

  const toggleLead = (id: string) => {
    setSelectedLeadIds((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAllLeads = () => {
    if (selectedLeadIds.size === enrichedLeads.length) {
      setSelectedLeadIds(new Set());
    } else {
      setSelectedLeadIds(new Set(enrichedLeads.map((l) => l.id)));
    }
  };

  const handleCreate = async () => {
    if (!name.trim()) {
      setError("Campaign name is required");
      return;
    }

    setCreating(true);
    setError("");

    try {
      // Step 1: Create the campaign
      const campaign = await apiRequest<{ id: string }>("/api/campaigns", {
        method: "POST",
        body: JSON.stringify({
          name: name.trim(),
          sending_account: sendingAccount.trim() || null,
          daily_limit: parseInt(dailyLimit) || 50,
          country_scope: countryScope.length > 0 ? countryScope : null,
        }),
      });

      // Step 2: Add selected leads
      if (selectedLeadIds.size > 0) {
        await apiRequest(`/api/campaigns/${campaign.id}/leads`, {
          method: "POST",
          body: JSON.stringify({
            lead_ids: Array.from(selectedLeadIds),
          }),
        });
      }

      router.push(`/campaigns/${campaign.id}`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create campaign");
    } finally {
      setCreating(false);
    }
  };

  return (
    <div>
      <Button variant="ghost" size="sm" onClick={() => router.push("/campaigns")} className="mb-4">
        <ArrowLeft className="mr-1 h-4 w-4" />
        Back to Campaigns
      </Button>

      <h1 className="mb-6 text-2xl font-bold text-slate-900">Create Campaign</h1>

      {error && (
        <div className="mb-4 rounded-lg border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-600">
          {error}
        </div>
      )}

      <div className="grid gap-6 lg:grid-cols-2">
        {/* Campaign Details */}
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Campaign Details</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Campaign Name *</label>
              <Input
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. US Email Marketers - Q1 2024"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Sending Account</label>
              <Input
                value={sendingAccount}
                onChange={(e) => setSendingAccount(e.target.value)}
                placeholder="e.g. outreach@team.com"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Daily Send Limit</label>
              <Input
                type="number"
                value={dailyLimit}
                onChange={(e) => setDailyLimit(e.target.value)}
                min="1"
                max="500"
              />
            </div>
            <div>
              <label className="mb-1.5 block text-sm font-medium text-slate-700">Target Countries</label>
              <div className="flex gap-2">
                {COUNTRIES.map((c) => (
                  <button
                    key={c}
                    type="button"
                    onClick={() => toggleCountry(c)}
                    className={`rounded-lg border px-3 py-1.5 text-sm font-medium transition-colors ${
                      countryScope.includes(c)
                        ? "border-slate-900 bg-slate-900 text-white"
                        : "border-slate-200 bg-white text-slate-600 hover:border-slate-300"
                    }`}
                  >
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Lead Selection */}
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-base">
                Select Leads ({selectedLeadIds.size} selected)
              </CardTitle>
              <Button variant="ghost" size="sm" onClick={toggleAllLeads}>
                {selectedLeadIds.size === enrichedLeads.length ? "Deselect All" : "Select All"}
              </Button>
            </div>
            <p className="text-xs text-slate-500">
              Showing leads with status &ldquo;enriched&rdquo; — {enrichedLeads.length} available
            </p>
          </CardHeader>
          <CardContent>
            {enrichedLeads.length === 0 ? (
              <p className="text-center text-sm text-slate-400 py-8">
                No enriched leads available for campaigns
              </p>
            ) : (
              <div className="max-h-80 overflow-y-auto space-y-1">
                {enrichedLeads.map((lead) => (
                  <button
                    key={lead.id}
                    type="button"
                    onClick={() => toggleLead(lead.id)}
                    className={`flex w-full items-center gap-3 rounded-lg border p-3 text-left text-sm transition-colors ${
                      selectedLeadIds.has(lead.id)
                        ? "border-emerald-200 bg-emerald-50"
                        : "border-slate-100 hover:bg-slate-50"
                    }`}
                  >
                    <div className={`flex h-5 w-5 items-center justify-center rounded border ${
                      selectedLeadIds.has(lead.id)
                        ? "border-emerald-500 bg-emerald-500 text-white"
                        : "border-slate-300"
                    }`}>
                      {selectedLeadIds.has(lead.id) && <Check className="h-3 w-3" />}
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="font-medium text-slate-900 truncate">{lead.full_name}</p>
                      <p className="text-xs text-slate-400 truncate">
                        {lead.company_name || "Unknown"} · {lead.company_country}
                      </p>
                    </div>
                    {lead.best_score && (
                      <Badge variant="secondary" className="text-xs">
                        Score: {lead.best_score}
                      </Badge>
                    )}
                  </button>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex items-center gap-3">
        <Button onClick={handleCreate} disabled={creating}>
          {creating ? "Creating..." : "Create Campaign"}
        </Button>
        <Button variant="outline" onClick={() => router.push("/campaigns")}>
          Cancel
        </Button>
      </div>
    </div>
  );
}
