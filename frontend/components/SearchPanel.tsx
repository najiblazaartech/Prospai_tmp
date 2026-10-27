"use client";
import { useState } from "react";
import { searchLeads, listCampaigns, addLeadToCampaign, createCampaign } from "@/lib/api";

const scoreColor = (s: number) =>
  s >= 90 ? "text-green-600" : s >= 75 ? "text-sky-600" : s >= 60 ? "text-amber-600" : "text-slate-400";

export default function SearchPanel() {
  const [prompt, setPrompt] = useState("CEOs de scale-ups SaaS en France actifs sur LinkedIn");
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [campaignId, setCampaignId] = useState<number | null>(null);
  const [flash, setFlash] = useState("");
  const [error, setError] = useState("");
  const [searched, setSearched] = useState(false);

  const run = async () => {
    setLoading(true);
    setFlash("");
    setError("");
    setSearched(true);
    try {
      const res = await searchLeads(prompt, 8);
      setLeads(res);
      setCampaigns(await listCampaigns());
      if (!res.length) setFlash("Aucun résultat web exploitable. Aucun prospect fictif n’a été ajouté.");
    } catch (err: any) {
      setError("La recherche en direct a échoué : " + String(err?.message || err));
    } finally {
      setLoading(false);
    }
  };

  const createDefaultCampaign = async () => {
    const c = await createCampaign("Campagne - " + new Date().toLocaleDateString("fr-FR"), prompt);
    setCampaigns(await listCampaigns());
    setCampaignId(c.id);
    setFlash("Campagne creee avec sequence multicanale par defaut (J0 invitation, J+3 message, J+5 email, J+10 breakup).");
  };

  const addToCampaign = async (leadId: number) => {
    let cid = campaignId ?? campaigns[0]?.id;
    if (!cid) {
      const c = await createCampaign("Ma premiere campagne", prompt);
      cid = c.id;
      setCampaigns(await listCampaigns());
      setCampaignId(cid);
    }
    await addLeadToCampaign(cid, leadId);
    setFlash("Lead ajoute : actions en file. En mode revue manuelle, la premiere action attend votre validation (onglet A valider).");
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-sm font-semibold mb-2">Decris ta cible en langage naturel</div>
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={2}
          className="w-full rounded-xl border border-slate-200 p-3 text-sm" />
        <div className="flex items-center gap-3 mt-3">
          <button onClick={run} disabled={loading}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
            {loading ? "Recherche IA en cours..." : "Lancer la recherche IA"}
          </button>
          <button onClick={createDefaultCampaign} className="text-xs font-semibold text-indigo-600 hover:underline">
            + Nouvelle campagne avec sequence par defaut
          </button>
          {campaigns.length > 0 && (
            <select value={campaignId ?? campaigns[0].id} onChange={(e) => setCampaignId(+e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2 py-1">
              {campaigns.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          )}
        </div>
        {flash && <div className="mt-3 rounded-xl bg-indigo-50 p-3 text-xs text-indigo-700">{flash}</div>}
      </div>

      {error && <div role="alert" className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</div>}
      {leads.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 font-semibold text-sm">
            Résultats issus du web ({leads.length})
          </div>
          {leads.map((l: any) => (
            <div key={l.id} className="flex items-center gap-4 px-5 py-3 border-b border-slate-50 hover:bg-slate-50">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-semibold">{l.full_name} <span className="font-normal text-slate-500">- {l.role}, {l.company} ({l.company_size} pers.)</span></div>
                <div className="text-xs text-slate-500">{(l.score_reasons || []).join(" · ")}</div>
                {l.enrichment?.url && <a className="text-xs text-indigo-600 underline" href={l.enrichment.url} target="_blank" rel="noreferrer">Source web : {l.enrichment.website || l.enrichment.url}</a>}
                {l.enrichment?.snippet && <div className="text-xs text-slate-500 mt-1">{l.enrichment.snippet}</div>}
              </div>
              <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${l.email_status === "valide" ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"}`}>
                email {l.email_status}
              </span>
              <div className={`text-sm font-bold ${scoreColor(l.score)}`}>{l.score}</div>
              <button onClick={() => addToCampaign(l.id)}
                className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700">
                + Campagne
              </button>
            </div>
          ))}
        </div>
      )}
      {searched && !loading && leads.length === 0 && !error && <div className="rounded-2xl border border-slate-200 bg-white p-5 text-sm text-slate-600">Aucun prospect affiché. ProspAI ne remplit pas la liste avec des fiches inventées.</div>}
    </div>
  );
}
