import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ProspAI - Decouverte IA + sequences multicanal",
  description: "Decris ta cible, ProspAI la trouve, la score, la verifie et lance tes campagnes LinkedIn + email.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="fr">
      <body className="bg-slate-50 text-slate-900">{children}</body>
    </html>
  );
}
