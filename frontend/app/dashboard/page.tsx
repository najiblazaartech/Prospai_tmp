"use client";
import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/api";
import SearchPanel from "@/components/SearchPanel";
import CampaignsPanel from "@/components/CampaignsPanel";
import CrmPanel from "@/components/CrmPanel";
import ReviewPanel from "@/components/ReviewPanel";

const TABS = [
  ["search", "Recherche IA"],
  ["campaigns", "Campagnes"],
  ["review", "A valider"],
  ["crm", "CRM"],
] as const;

export default function Dashboard() {
  const router = useRouter();
  const [tab, setTab] = useState<string>("search");
  const [ready, setReady] = useState(false);

  useEffect(() => {
    if (!getToken()) router.push("/login");
    else setReady(true);
  }, [router]);

  if (!ready) return null;

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between border-b border-slate-200 pb-4 mb-6">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-sky-400 flex items-center justify-center text-white font-bold">P</div>
          <div>
            <div className="font-bold leading-tight">ProspAI</div>
            <div className="text-[11px] text-slate-500 leading-tight">Decouverte IA + sequences multicanal</div>
          </div>
        </div>
        <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
          {TABS.map(([id, label]) => (
            <button key={id} onClick={() => setTab(id)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium ${tab === id ? "bg-white shadow text-indigo-600" : "text-slate-600"}`}>
              {label}
            </button>
          ))}
        </div>
        <button onClick={() => { localStorage.removeItem("prospai_token"); router.push("/"); }}
          className="text-xs text-slate-500 hover:text-slate-800">Deconnexion</button>
      </div>
      {tab === "search" && <SearchPanel />}
      {tab === "campaigns" && <CampaignsPanel />}
      {tab === "review" && <ReviewPanel />}
      {tab === "crm" && <CrmPanel />}
    </div>
  );
}
