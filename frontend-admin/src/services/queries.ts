
import { apiGet, apiPost, apiDelete, devLogin, googleLogin } from './api';
export { googleLogin };

// ---- Enrichment ----
export type EnrichedBusiness = {
  name: string; address: string; phone: string; website: string;
  rating?: number; reviews_count?: number; google_maps_url: string;
  status: string; types: string[]; top_review: string; opening_hours: string[];
  place_id: string; facebook_url: string; instagram_url: string;
  social_confidence: string; completeness_score: number;
  lead_opportunity_score: number;
  cache_status?: 'new' | 'known' | 'imported';
};
export type EnrichSearchResult = {
  city: string; category: string; total: number; has_real_api: boolean;
  new_this_search: number; already_known: number;
  filters: { no_website_only: boolean; min_reviews: number; min_rating: number };
  results: EnrichedBusiness[];
};
export type EnrichStatus = { google_places: boolean; facebook_graph: boolean; openai_llm: boolean; mode: string; cache_total: number; cache_imported: number };
export type EnrichCategory = { label: string; queries: string[] };

export const getEnrichStatus = () => apiGet<EnrichStatus>('/admin/enrich/status');
export const getEnrichCategories = () => apiGet<EnrichCategory[]>('/admin/enrich/categories');
export const searchEnrich = (
  city: string, category: string, limit: number, social: boolean,
  no_website_only: boolean, min_reviews: number, min_rating: number,
) =>
  apiGet<EnrichSearchResult>(
    `/admin/enrich/search?city=${encodeURIComponent(city)}&category=${encodeURIComponent(category)}&limit=${limit}&social=${social}&no_website_only=${no_website_only}&min_reviews=${min_reviews}&min_rating=${min_rating}`
  );
export const importEnrichedToLeads = (businesses: EnrichedBusiness[], city: string) =>
  apiPost<{ imported: number; skipped: number; errors: string[] }>('/admin/enrich/import-to-leads', { businesses, city });

export async function createBusiness(payload: Record<string, unknown>) {
  return apiPost<Business>('/admin/businesses', payload);
}

export async function createLead(payload: Record<string, unknown>) {
  return apiPost<Lead>('/admin/leads', payload);
}

export async function importLeadsCSV(csvText: string): Promise<{ imported: number; errors: string[] }> {
  const BASE_URL = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1') as string;
  const token = localStorage.getItem('admin_access_token') ?? '';
  const blob = new Blob([csvText], { type: 'text/csv' });
  const form = new FormData();
  form.append('file', blob, 'leads.csv');
  const res = await fetch(`${BASE_URL}/admin/leads/import-csv`, {
    method: 'POST',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
    body: form,
  });
  if (!res.ok) throw new Error('Import failed');
  return res.json();
}

export type Snapshot = Record<string, number>;
export type Digest = { executive_summary: string; recommended_actions: string[]; approval_queue_count?: number; approvals_pending?: number; payments_pending?: number; expiring_drafts?: number; outreach_ready_count?: number; qualified_leads?: number; pressure_notes?: string[] };
export type Business = { id: number; name: string; city?: string; category?: string; status: string; phone?: string | null; address?: string | null; campaign_id?: number | null; targeting_profile_id?: number | null };
export type Lead = { id: number; imported_name: string; city?: string; category?: string; phone?: string | null; score: number; status: string; website_url?: string | null; campaign_id?: number | null; targeting_profile_id?: number | null };
export type Approval = { id: number; title: string; status: string; approval_type: string; summary?: string | null };
export type ApprovalDetail = Approval & { rationale?: string | null; evidence_json?: Record<string, unknown> | null; before_json?: Record<string, unknown> | null; after_json?: Record<string, unknown> | null; confidence_score?: number | null; payload_json?: Record<string, unknown> | null };
export type Profile = { id: number; name: string; city?: string; radius_km?: number };
export type Campaign = { id: number; name: string; status: string };
export type Health = { overall_status?: string; drivers?: string[]; database_ok?: boolean; status?: string };
export type QueueSummary = { queue_type: string; count: number; label: string };
export type QueueItem = { id: number; title: string; subtitle?: string | null; priority: string; queue_type: string; linked_entity_type: string; linked_entity_id: number; available_actions?: string[] };
export type CampaignResults = { campaign_id: number; lead_count: number; business_count: number };

export async function ensureDevLogin() {
  try {
    await devLogin(import.meta.env.VITE_ADMIN_EMAIL || 'admin@example.com', 'Admin User', import.meta.env.VITE_ADMIN_DEV_TOKEN || 'dev-admin-token');
    return '';
  } catch (e) {
    return 'Could not perform dev login, falling back to headers if available.';
  }
}

export const getSnapshot = () => apiGet<Snapshot>('/admin/analytics/snapshot');
export const getDigest = () => apiGet<Digest>('/admin/ceo/daily-digest');
export const getHealth = () => apiGet<Health>('/admin/ceo/health');
export const getBusinesses = (skip = 0, limit = 100) => apiGet<Business[]>(`/admin/businesses?skip=${skip}&limit=${limit}`);
export const getLeads = (skip = 0, limit = 100) => apiGet<Lead[]>(`/admin/leads?skip=${skip}&limit=${limit}`);
export const getApprovals = () => apiGet<Approval[]>('/admin/approvals');
export const getApprovalDetail = (id: number) => apiGet<ApprovalDetail>(`/admin/approvals/${id}`);
export const approve = (id: number) => apiPost(`/admin/approvals/${id}/approve`, {});
export const reject = (id: number) => apiPost(`/admin/approvals/${id}/reject`, {});
export type ApplyResult = { id: number; status: string; applied: boolean; execution?: { status: string; message: string } };
export const applyApproval = (id: number) => apiPost<ApplyResult>(`/admin/approvals/${id}/apply`, {});
export const getProfiles = () => apiGet<Profile[]>('/admin/targeting/profiles');
export const getCampaigns = () => apiGet<Campaign[]>('/admin/targeting/campaigns');
export const getCampaignResults = (id: number) => apiGet<CampaignResults>(`/admin/targeting/campaigns/${id}/results`);
export const assignLeadToCampaign = (campaignId: number, leadId: number, targeting_profile_id?: number | null) => apiPost(`/admin/targeting/campaigns/${campaignId}/assign-lead/${leadId}`, { campaign_id: campaignId, targeting_profile_id });
export const assignBusinessToCampaign = (campaignId: number, businessId: number, targeting_profile_id?: number | null) => apiPost(`/admin/targeting/campaigns/${campaignId}/assign-business/${businessId}`, { campaign_id: campaignId, targeting_profile_id });
export const searchLeads = (city?: string, category?: string) => {
  const q = new URLSearchParams();
  if (city) q.set('city', city);
  if (category) q.set('category', category);
  q.set('min_score', '0');
  return apiGet<Lead[]>(`/admin/targeting/search?${q.toString()}`);
};
export const getQueueSummary = () => apiGet<QueueSummary[]>('/admin/queues/summary');
export const getQueueItems = (queueType: string) => apiGet<QueueItem[]>(`/admin/queues/${queueType}`);
export const runQueueAction = (queueType: string, id: number, action: string, extra?: Record<string, unknown>) => apiPost(`/admin/queues/${queueType}/${id}/action`, { action, ...(extra || {}) });
export const qualifyLead = (leadId: number) => apiPost(`/admin/leads/${leadId}/qualify`, {});
export const convertLeadToBusiness = (leadId: number) => apiPost(`/admin/leads/${leadId}/convert-to-business`, {});
export const moveBusinessToDraft = (businessId: number) => apiPost(`/admin/businesses/${businessId}/move-to-draft`, {});
export const markBusinessOutreachReady = (businessId: number) => apiPost(`/admin/businesses/${businessId}/outreach-ready`, {});
export const buildBusinessWhatsApp = (businessId: number, draftSiteId?: number | null, messageTemplateKey = 'initial_outreach_v1') => apiPost('/admin/communications/whatsapp-for-business', { business_id: businessId, draft_site_id: draftSiteId ?? null, message_template_key: messageTemplateKey });
export const markOutreachSent = (outreachId: number) => apiPost(`/admin/communications/outreach/${outreachId}/mark-sent`, { status: 'sent' });
export const rescheduleFollowup = (outreachId: number, note?: string) => apiPost(`/admin/communications/outreach/${outreachId}/reschedule-followup`, { note: note || null });
export const confirmPayment = (paymentId: number) => apiPost(`/admin/payments/${paymentId}/confirm`, {});
export const movePaymentToActivation = (paymentId: number) => apiPost(`/admin/payments/${paymentId}/move-to-activation`, {});
export const createCeoTask = (source: string, title: string, note?: string) => apiPost('/admin/ceo/task-from-recommendation', { source, title, note });
export const addCeoDecisionNote = (note: string) => apiPost('/admin/ceo/decision-note', { note });

// ── Grok CEO ──────────────────────────────────────────────────────────────────
export type GrokExecutionPayload = {
  action_type: string;
  target_component: string;
  new_value: string;
};
export type GrokCEOResponse = {
  understanding_and_analysis: string;
  strategic_insight: string;
  proposed_action_plan: string;
  system_execution_payload: GrokExecutionPayload;
  message_to_ariel: string;
};
export type GrokExecuteResult = { status: string; message: string };

export const askGrok = (message?: string) =>
  apiPost<GrokCEOResponse>('/admin/ceo/grok-think', { message: message ?? null });

export const executeGrokAction = (payload: GrokExecutionPayload) =>
  apiPost<GrokExecuteResult>('/admin/ceo/grok-execute', payload);

export type Feedback = { id: number; target_type: string; target_id?: number | null; quick_rating: string; open_feedback?: string | null; feedback_status: string; analysis_category?: string | null; suggested_scope?: string | null; ceo_response?: string | null; action_hint?: string | null; preference_candidate: boolean; };
export const getFeedback = () => apiGet<Feedback[]>('/admin/feedback');
export const createFeedback = (payload: Record<string, unknown>) => apiPost('/admin/feedback', payload);
export const analyzeFeedback = (id: number) => apiPost(`/admin/feedback/${id}/analyze`, {});

export type SecuritySummary = { login_failures: number; blocked_logins: number; active_challenges: number; rate_limited_events: number; delivery_attempts: number; onboarding_sessions: number; demo_requests: number; overall_status: string };
export type SecurityTimelineItem = { type: string; at?: string | null; phone?: string | null; label: string; detail?: string | null };
export type SuspicionItem = { customer_phone: string; suspicion_score: number; suspicion_tier: string; login_failures: number; blocked_logins: number; rate_limit_hits: number; delivery_failures: number };
export const getSecuritySummary = () => apiGet<SecuritySummary>('/admin/security/summary');
export const getSecurityTimeline = (customerPhone?: string) => { const q = new URLSearchParams(); if (customerPhone) q.set('customer_phone', customerPhone); return apiGet<{ items: SecurityTimelineItem[] }>(`/admin/security/timeline?${q.toString()}`); };
export const getSuspicion = (customerPhone?: string) => { const q = new URLSearchParams(); if (customerPhone) q.set('customer_phone', customerPhone); return apiGet<{ items: SuspicionItem[], total: number }>(`/admin/security/suspicion?${q.toString()}`); };

export type SecurityAlert = { id: number; alert_type: string; severity: string; customer_phone?: string | null; summary: string; detail?: string | null; status: string; escalation_level: string; created_at?: string | null };
export const getSecurityAlerts = (status?: string) => { const q = new URLSearchParams(); if (status) q.set('status', status); return apiGet<SecurityAlert[]>(`/admin/security/alerts?${q.toString()}`); };
export const getLockoutPolicy = () => apiGet<Record<string, unknown>>('/admin/security/lockout-policy');
export const refreshSecurityAlerts = () => apiPost('/admin/security/refresh-alerts', {});

export const getCustomerPermissions = (customerId: number) => apiGet<Record<string, unknown>>(`/admin/customers/${customerId}/permissions`);

export type Customer = { id: number; business_id?: number | null; phone?: string | null; email?: string | null; contact_name?: string | null; active_site_id?: number | null; draft_site_id?: number | null; must_change_password: boolean; is_active: boolean; package_name?: string | null };
export const getCustomers = (skip = 0, limit = 100) => apiGet<Customer[]>(`/admin/customers?skip=${skip}&limit=${limit}`);

export type DraftSite = { id: number; business_id: number; site_title: string; status: string; preview_url?: string | null; primary_color?: string | null; is_demo?: boolean; noindex?: boolean; hero_title?: string | null; about_text?: string | null };
export const getDraftSites = (skip = 0, limit = 100) => apiGet<DraftSite[]>(`/admin/draft-sites?skip=${skip}&limit=${limit}`);
export const generateDraftPreview = (draftId: number) => apiPost<DraftSite>(`/admin/draft-sites/${draftId}/generate-preview`, {});
export const createAndPreview = (businessId: number) => apiPost<DraftSite>(`/admin/draft-sites/create-and-preview/${businessId}`, {});

export type Payment = { id: number; business_id?: number | null; amount: number; internal_status: string };
export const getPayments = (skip = 0, limit = 100) => apiGet<Payment[]>(`/admin/payments?skip=${skip}&limit=${limit}`);

// ---- Demo Sites ----
export type DemoRecord = {
  id: number; slug: string; place_id?: string | null;
  business_name: string; tagline?: string | null;
  phone?: string | null; address?: string | null; city?: string | null;
  rating?: number | null; reviews_count?: number | null;
  google_maps_url?: string | null; top_review?: string | null;
  business_types?: string | null; category?: string | null;
  status: string; view_count: number;
  first_viewed_at?: string | null; whatsapp_sent_at?: string | null;
  created_at?: string | null;
};
export type PublicDemoData = Omit<DemoRecord, 'id' | 'status' | 'view_count' | 'first_viewed_at' | 'whatsapp_sent_at' | 'created_at'>;

export const getDemos = () => apiGet<DemoRecord[]>('/admin/demos');
export const createDemosFromEnriched = (businesses: EnrichedBusiness[]) =>
  apiPost<{ created: number; demos: DemoRecord[] }>('/admin/demos/create-from-enriched', { businesses });
export const markDemoSent = (id: number) => apiPost<DemoRecord>(`/admin/demos/${id}/mark-sent`, {});
export const markDemoConverted = (id: number) => apiPost<DemoRecord>(`/admin/demos/${id}/mark-converted`, {});
export const deleteDemo = (id: number) => apiDelete<{ ok: boolean }>(`/admin/demos/${id}`);

const PUBLIC_BASE = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1') as string;
export async function getPublicDemo(slug: string): Promise<PublicDemoData> {
  const res = await fetch(`${PUBLIC_BASE}/public/demo/${slug}`);
  if (!res.ok) throw new Error('Demo not found');
  return res.json();
}
export async function trackDemoView(slug: string): Promise<void> {
  await fetch(`${PUBLIC_BASE}/public/demo/${slug}/view`, { method: 'POST' });
}

// ---- Notifications ----
export type Notification = { id: number; event: string; entity_type: string; entity_id?: number | null; summary: string; created_at?: string | null };
export const getNotifications = (limit = 30) => apiGet<Notification[]>(`/admin/notifications?limit=${limit}`);

// ---- A/B Test Results ----
export type AbVariantResult = { variant: string; campaign_id: string; total: number; sent: number; delivered: number; read: number; replied: number; reply_rate: number; read_rate: number };
export const getAbResults = (campaignId?: string) => apiGet<AbVariantResult[]>(`/admin/analytics/ab-results${campaignId ? `?campaign_id=${encodeURIComponent(campaignId)}` : ''}`);

// ---- Auto-qualify ----
export const autoQualifyLeads = () => apiPost<{ qualified: number; leads: { id: number; name: string }[] }>('/admin/leads/auto-qualify', {});

// ---- Celery background tasks ----
export type TaskTriggered = { task_id: string; message: string };
export type TaskStatus = { task_id: string; state: string; step?: string | null; result?: Record<string, unknown> | null; error?: string | null };
export const triggerGenerateSite = (businessId: number) => apiPost<TaskTriggered>(`/admin/tasks/generate-site/${businessId}`, {});
export const triggerBatchGenerate = (businessIds: number[]) => apiPost<TaskTriggered>('/admin/tasks/batch-generate', { business_ids: businessIds });
export const getTaskStatus = (taskId: string) => apiGet<TaskStatus>(`/admin/tasks/${taskId}/status`);
