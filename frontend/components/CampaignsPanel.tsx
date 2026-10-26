"use client";
import { useEffect, useState } from "react";
import { listCampaigns } from "@/lib/api";

export default function CampaignsPanel() {
  const [campaigns, setCampaigns] = useState<any[]>([]);

  useEffect(() => {
    listCampaigns().then(setCampaigns).catch(() => {});
  }, []);

  return (
    <div className="space-y-4">
      <div className="font-semibold text-sm">Mes campagnes</div>
      {campaigns.map((c: any) => (
        <div key={c.id} className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between mb-3">
            <div className="text-sm font-semibold">{c.name}</div>
            <span className={`text-[10px] px-2 py-0.5 rounded-full font-semibold ${c.status === "active" ? "bg-green-100 text-green-700" : "bg-slate-100 text-slate-500"}`}>
              {c.status === "active" ? "Active" : c.status}
            </span>
          </div>
          <div className="grid grid-cols-5 gap-2 text-center">
            {[["Leads", c.leads], ["Envoyes", c.sent], ["Reponses", c.replies], ["Taux rep.", c.reply_rate + "%"], ["Statut", c.status]].map(([k, v]) => (
              <div key={k as string} className="rounded-xl bg-slate-50 py-2">
                <div className="text-[10px] text-slate-500">{k}</div>
                <div className="text-sm font-bold">{v}</div>
              </div>
            ))}
          </div>
        </div>
      ))}
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-3 text-xs text-amber-800">
        Quotas anti-ban : max 80 actions LinkedIn/jour, jitter aleatoire, fenetres d'envoi.
        Le worker envoie uniquement les actions approuvees (mode EU).
      </div>
    </div>
  );
}
