"use client";
import { useEffect, useState } from "react";
import { crmLeads, setLeadStatus } from "@/lib/api";

const STATUSES = ["new", "contacted", "replied", "meeting", "won", "lost"];

export default function CrmPanel() {
  const [leads, setLeads] = useState<any[]>([]);

  const load = () => crmLeads().then(setLeads).catch(() => {});
  useEffect(() => { load(); }, []);

  const move = async (id: number, status: string) => {
    await setLeadStatus(id, status);
    await load();
  };

  const byStatus = STATUSES.map((s) => ({ status: s, leads: leads.filter((l) => l.crm_status === s) }));

  return (
    <div className="space-y-4">
      <div className="font-semibold text-sm">Pipeline CRM</div>
      <div className="grid grid-cols-6 gap-3">
        {byStatus.map(({ status, leads: ls }) => (
          <div key={status} className="rounded-2xl bg-slate-100 p-2 min-h-40">
            <div className="text-[11px] font-bold text-slate-600 uppercase px-1 pb-2">{status} ({ls.length})</div>
            {ls.map((l) => (
              <div key={l.id} className="rounded-xl bg-white p-2 mb-2 shadow-sm">
                <div className="text-[11px] font-semibold">{l.name}</div>
                <div className="text-[10px] text-slate-500">{l.company}</div>
                <div className="flex gap-1 mt-1">
                  {STATUSES.filter((s) => s !== l.crm_status).slice(0, 2).map((s) => (
                    <button key={s} onClick={() => move(l.id, s)}
                      className="text-[9px] bg-slate-200 rounded px-1.5 py-0.5 hover:bg-slate-300">{s}</button>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ))}
      </div>
    </div>
  );
}
