"use client";
import { useState } from "react";
import { searchLeads, listCampaigns, addLeadToCampaign, createCampaign } from "@/lib/api";

const scoreColor = (s: number) =>
  s >= 90 ? "text-green-600" : s >= 75 ? "text-sky-600" : s >= 60 ? "text-amber-600" : "text-slate-400";

const sourceLabel = (source: string) => {
  if (source === "web") return "Recherche web en direct";
  if (source === "apollo") return "Apollo";
  if (source === "curated-web") return "Jeu local de test — pas une recherche en direct";
  if (source === "mock") return "Démonstration — données fictives";
  return source || "Source non précisée";
};

export default function SearchPanel() {
  const [prompt, setPrompt] = useState("Cabinets de transmission d'entreprise et courtiers en fonds de commerce en France");
  const [leads, setLeads] = useState<any[]>([]);
  const [hasSearched, setHasSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [campaignId, setCampaignId] = useState<number | null>(null);
  const [flash, setFlash] = useState("");
  const [error, setError] = useState("");

  const run = async () => {
    setLoading(true);
    setFlash("");
    setError("");
    setHasSearched(false);
    try {
      const res = await searchLeads(prompt, 8);
      setLeads(res);
      setHasSearched(true);
      setCampaigns(await listCampaigns());
    } catch (err: any) {
      setLeads([]);
      setError(err?.message || "La recherche a échoué. Vérifiez que l’API est accessible.");
    } finally {
      setLoading(false);
    }
  };

  const createDefaultCampaign = async () => {
    const c = await createCampaign("Campagne - " + new Date().toLocaleDateString("fr-FR"), prompt);
    setCampaigns(await listCampaigns());
    setCampaignId(c.id);
    setFlash("Campagne créée. Les envois restent soumis à validation manuelle.");
  };

  const addToCampaign = async (leadId: number) => {
    let cid = campaignId ?? campaigns[0]?.id;
    if (!cid) {
      const c = await createCampaign("Ma première campagne", prompt);
      cid = c.id;
      setCampaigns(await listCampaigns());
      setCampaignId(cid);
    }
    await addLeadToCampaign(cid, leadId);
    setFlash("Prospect ajouté. La première action attend votre validation dans l’onglet « À valider ».");
  };

  return (
    <div className="space-y-6">
      <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
        <div className="text-sm font-semibold mb-2">Décris ta cible en langage naturel</div>
        <textarea value={prompt} onChange={(e) => setPrompt(e.target.value)} rows={2}
          className="w-full rounded-xl border border-slate-200 p-3 text-sm" />
        <div className="flex items-center gap-3 mt-3 flex-wrap">
          <button onClick={run} disabled={loading || !prompt.trim()}
            className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
            {loading ? "Recherche web en cours…" : "Lancer la recherche"}
          </button>
          <span className="text-xs text-slate-500">Recherche en direct · pas de faux résultats de secours</span>
          <button onClick={createDefaultCampaign} className="text-xs font-semibold text-indigo-600 hover:underline">
            + Nouvelle campagne
          </button>
          {campaigns.length > 0 && (
            <select value={campaignId ?? campaigns[0].id} onChange={(e) => setCampaignId(+e.target.value)}
              className="text-xs border border-slate-200 rounded-lg px-2 py-1">
              {campaigns.map((c: any) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          )}
        </div>
        {flash && <div className="mt-3 rounded-xl bg-indigo-50 p-3 text-xs text-indigo-700">{flash}</div>}
        {error && <div role="alert" className="mt-3 rounded-xl bg-red-50 p-3 text-xs text-red-700">{error}</div>}
      </div>

      {leads.length > 0 && (
        <div className="rounded-2xl border border-slate-200 bg-white shadow-sm overflow-hidden">
          <div className="px-5 py-3 border-b border-slate-100 font-semibold text-sm flex items-center justify-between gap-3">
            <span>Résultats de recherche ({leads.length})</span>
            <span className="text-xs font-normal text-slate-500">Vérifie la source avant de contacter</span>
          </div>
          {leads.map((l: any) => {
            const evidence = l.enrichment || {};
            const sourceUrl = evidence.url || evidence.research_source ||
              (evidence.website ? (evidence.website.startsWith("http") ? evidence.website : "https://" + evidence.website) : "");
            const isRealWeb = l.source === "web" || l.source === "apollo";
            return (
              <div key={l.id} className="px-5 py-4 border-b border-slate-100 last:border-0 hover:bg-slate-50">
                <div className="flex items-start gap-4">
                  <div className="flex-1 min-w-0">
                    <div className="text-sm font-semibold">{l.company || l.full_name}</div>
                    <div className="text-xs text-slate-600 mt-1">{l.role || "Activité / poste non identifié"}{l.country ? " · " + l.country : ""}</div>
                    {evidence.snippet && <p className="text-xs text-slate-600 mt-2">{evidence.snippet}</p>}
                    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 mt-2 text-xs">
                      {sourceUrl && <a href={sourceUrl} target="_blank" rel="noreferrer" className="text-indigo-600 underline break-all">Ouvrir la source</a>}
                      {evidence.website && <span className="text-slate-500">Domaine : {evidence.website}</span>}
                      {evidence.search_query && <span className="text-slate-400">Requête : {evidence.search_query}</span>}
                    </div>
                    <div className="mt-2 text-[11px] text-slate-500">
                      Source : {sourceLabel(l.source)}
                      {!isRealWeb && <span className="ml-2 font-semibold text-amber-700">À ne pas traiter comme prospect réel</span>}
                    </div>
                    <div className="text-xs text-slate-500 mt-1">{(l.score_reasons || []).join(" · ")}</div>
                  </div>
                  <div className="flex flex-col items-end gap-2 shrink-0">
                    {l.email ? (
                      <span className={`text-[10px] px-2 py-0.5 rounded-full ${l.email_status === "valide" ? "bg-green-100 text-green-700" : "bg-amber-100 text-amber-700"}`}>email {l.email_status}</span>
                    ) : <span className="text-[10px] px-2 py-0.5 rounded-full bg-slate-100 text-slate-600">Aucun email fourni</span>}
                    <div className={`text-sm font-bold ${scoreColor(l.score)}`}>Score {l.score}</div>
                    <button onClick={() => addToCampaign(l.id)}
                      className="rounded-lg bg-slate-900 px-3 py-1.5 text-xs font-semibold text-white hover:bg-slate-700">
                      + Campagne
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {hasSearched && leads.length === 0 && !error && (
        <div className="rounded-2xl border border-amber-200 bg-amber-50 p-5 text-sm text-amber-900">
          Aucun résultat réel retourné pour cette recherche. Aucun prospect fictif n’a été ajouté. Essaie d’élargir ou de reformuler la cible.
        </div>
      )}
    </div>
  );
}
