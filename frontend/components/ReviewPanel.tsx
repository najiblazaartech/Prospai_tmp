"use client";
import { useEffect, useState } from "react";
import { pendingReview, approveAction } from "@/lib/api";

export default function ReviewPanel() {
  const [actions, setActions] = useState<any[]>([]);

  const load = () => pendingReview().then(setActions).catch(() => {});
  useEffect(() => { load(); }, []);

  const approve = async (id: number) => {
    await approveAction(id);
    await load();
  };

  return (
    <div className="space-y-4">
      <div className="font-semibold text-sm">Actions en attente de validation (mode RGPD)</div>
      {actions.length === 0 && (
        <div className="rounded-xl bg-slate-100 p-4 text-xs text-slate-500">
          Aucune action a valider. Ajoutez des leads a une campagne depuis l'onglet Recherche IA.
        </div>
      )}
      {actions.map((a: any) => (
        <div key={a.id} className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <div className="text-sm font-semibold">{a.lead} - {a.channel}</div>
            <button onClick={() => approve(a.id)}
              className="rounded-lg bg-green-600 px-3 py-1.5 text-xs font-semibold text-white hover:bg-green-700">
              Approuver l'envoi
            </button>
          </div>
          <div className="text-xs text-slate-600 bg-slate-50 rounded-xl p-3">{a.content}</div>
        </div>
      ))}
    </div>
  );
}
