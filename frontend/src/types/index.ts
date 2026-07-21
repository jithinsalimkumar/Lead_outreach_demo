/**
 * TypeScript types matching the backend API schemas.
 *
 * These types mirror the Pydantic models in the backend so that
 * the frontend has type safety when working with API responses.
 */

// ==========================================
// Auth
// ==========================================
export interface LoginRequest {
  email: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
}

// ==========================================
// User
// ==========================================
export interface User {
  id: string;
  email: string;
  role: "admin" | "member";
  is_active: boolean;
  created_at: string;
}

// ==========================================
// Company
// ==========================================
export interface Company {
  id: string;
  name: string;
  domain: string;
  country: "US" | "UK" | "CA";
  employee_size_estimate: number | null;
  size_bucket: "small" | "large";
  source_job_url: string | null;
  created_at: string;
}

export interface CompanyDetail extends Company {
  job_postings: JobPosting[];
  lead_count: number;
}

// ==========================================
// Job Posting
// ==========================================
export interface JobPosting {
  id: string;
  title: string;
  tier_signal: "email_marketer" | "digital_marketer" | "general_marketer" | "email_agency";
  portal: "indeed" | "linkedin";
  url: string;
  location: string | null;
  scraped_at: string;
}

// ==========================================
// Lead
// ==========================================
export interface ScrapedJob {
  id: string;
  company_name: string;
  company_domain: string;
  country: string;
  job_title: string;
  tier_signal: string;
  job_url: string;
  portal: string;
  location: string | null;
  scraped_at: string;
}

export type LeadStatus =
  | "new"
  | "filtered"
  | "scraping_contacts"
  | "contacts_found"
  | "enriching"
  | "enriched"
  | "queued_for_outreach"
  | "sent"
  | "replied"
  | "bounced"
  | "unsubscribed";

export interface Lead {
  id: string;
  company_id: string;
  full_name: string;
  job_title: string | null;
  linkedin_url: string | null;
  is_excluded: boolean;
  status: LeadStatus;
  created_at: string;
  company_name: string | null;
  company_country: string | null;
  company_size_bucket: string | null;
  best_score: number | null;
}

export interface LeadDetail {
  id: string;
  full_name: string;
  job_title: string | null;
  linkedin_url: string | null;
  is_excluded: boolean;
  status: LeadStatus;
  created_at: string;
  company: Company | null;
  job_postings: JobPosting[];
  enrichment_data: EnrichmentData[];
  campaign_sends: CampaignSendDetail[];
}

// ==========================================
// Enrichment
// ==========================================
export interface EnrichmentData {
  id: string;
  lead_id: string;
  email: string | null;
  phone: string | null;
  verification_status: "verified" | "unverified" | "invalid";
  provider: "prospeo" | "vibe_prospecting";
  score: number | null;
  raw_response: unknown;
  created_at: string;
}

// ==========================================
// Campaign
// ==========================================
export interface Campaign {
  id: string;
  name: string;
  template_id: string | null;
  sending_account: string | null;
  daily_limit: number;
  country_scope: string[] | null;
  created_by: string | null;
  created_at: string;
  total_sends: number;
  total_opened: number;
  total_clicked: number;
  total_replied: number;
  total_bounced: number;
}

export interface CampaignDetail extends Campaign {
  leads: CampaignLead[];
}

export interface CampaignLead {
  lead_id: string;
  full_name: string;
  job_title: string | null;
  company_name: string | null;
  email: string | null;
  sends: CampaignSendSimple[];
}

export interface CampaignSendSimple {
  id: string;
  sequence_step: number;
  sent_at: string | null;
  opened: boolean;
  clicked: boolean;
  replied: boolean;
  bounced: boolean;
}

export interface CampaignSendDetail {
  id: string;
  campaign_id: string;
  campaign_name: string | null;
  sequence_step: number;
  sent_at: string | null;
  opened: boolean;
  clicked: boolean;
  replied: boolean;
  bounced: boolean;
}

// ==========================================
// Suppression
// ==========================================
export interface SuppressionEntry {
  id: string;
  email_or_domain: string;
  reason: "bounced" | "complained" | "unsubscribed" | "manual";
  country: string | null;
  created_at: string;
}

// ==========================================
// Dashboard
// ==========================================
export interface LeadsByStatus {
  new: number;
  filtered: number;
  scraping_contacts: number;
  contacts_found: number;
  enriching: number;
  enriched: number;
  queued_for_outreach: number;
  sent: number;
  replied: number;
  bounced: number;
  unsubscribed: number;
}

export interface CampaignPerformanceSummary {
  total_sends: number;
  total_opened: number;
  total_clicked: number;
  total_replied: number;
  total_bounced: number;
  open_rate: number;
  click_rate: number;
  reply_rate: number;
  bounce_rate: number;
}

export interface DashboardStats {
  leads_by_status: LeadsByStatus;
  leads_discovered_this_week: number;
  total_leads: number;
  total_companies: number;
  campaign_performance: CampaignPerformanceSummary;
}

// ==========================================
// Settings
// ==========================================
export interface Setting {
  id: string;
  key: string;
  masked_value: string;
  updated_by: string | null;
  updated_at: string | null;
}

// ==========================================
// Pagination
// ==========================================
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}
