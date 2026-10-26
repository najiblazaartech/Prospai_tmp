const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export function setToken(t: string) {
  if (typeof window !== "undefined") localStorage.setItem("prospai_token", t);
}
export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem("prospai_token");
}

export async function api(path: string, opts: RequestInit = {}): Promise<any> {
  const token = getToken();
  const res = await fetch(`${API}${path}`, {
    ...opts,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(opts.headers || {}),
    },
  });
  if (!res.ok) throw new Error(`${res.status}: ${await res.text()}`);
  return res.json();
}

export const login = (email: string, password: string) =>
  api("/auth/login", { method: "POST", body: JSON.stringify({ email, password }) });
export const register = (email: string, password: string, full_name: string) =>
  api("/auth/register", { method: "POST", body: JSON.stringify({ email, password, full_name }) });
export const searchLeads = (prompt: string, limit = 10) =>
  api("/search", { method: "POST", body: JSON.stringify({ prompt, limit }) });
export const listCampaigns = () => api("/campaigns");
export const createCampaign = (name: string, prompt: string) =>
  api("/campaigns", { method: "POST", body: JSON.stringify({ name, prompt }) });
export const addLeadToCampaign = (campaignId: number, leadId: number) =>
  api(`/campaigns/${campaignId}/add-lead/${leadId}`, { method: "POST" });
export const pendingReview = () => api("/campaigns/actions/pending-review");
export const approveAction = (id: number) =>
  api(`/campaigns/actions/${id}/approve`, { method: "POST" });
export const crmLeads = () => api("/crm/leads");
export const setLeadStatus = (leadId: number, status: string) =>
  api(`/crm/leads/${leadId}/status?status=${status}`, { method: "PATCH" });
export const pipeline = () => api("/crm/pipeline");
export const analytics = () => api("/crm/analytics");
