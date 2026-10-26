import Link from "next/link";

export default function Home() {
  return (
    <main className="min-h-screen bg-gradient-to-b from-indigo-50 to-white">
      <nav className="max-w-6xl mx-auto flex items-center justify-between py-6 px-4">
        <div className="flex items-center gap-2">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-sky-400 flex items-center justify-center text-white font-bold">P</div>
          <span className="font-bold text-lg">ProspAI</span>
        </div>
        <Link href="/login" className="rounded-xl bg-indigo-600 px-4 py-2 text-sm font-semibold text-white hover:bg-indigo-700">
          Essayer
        </Link>
      </nav>

      <section className="max-w-6xl mx-auto px-4 py-20 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight mb-6">
          Decris qui tu veux atteindre.<br />
          <span className="text-indigo-600">ProspAI fait le reste.</span>
        </h1>
        <p className="text-lg text-slate-600 max-w-2xl mx-auto mb-8">
          Recherche IA multi-sources, scoring explicable, emails verifies et sequences
          LinkedIn/email automatiques - dans un seul produit.
        </p>
        <div className="flex justify-center gap-3">
          <Link href="/login" className="rounded-xl bg-indigo-600 px-6 py-3 font-semibold text-white hover:bg-indigo-700">
            Commencer gratuitement
          </Link>
        </div>
        <div className="grid grid-cols-4 gap-4 max-w-3xl mx-auto mt-16 text-left">
          {[
            ["\uD83D\uDD0D", "Decouverte IA", "100+ sources, prompt en langage naturel"],
            ["\uD83C\uDFAF", "Scoring explicable", "Chaque lead avec ses raisons"],
            ["\u2709\uFE0F", "Multicanal", "Sequences LinkedIn + email conditionnelles"],
            ["\uD83D\uDEE1\uFE0F", "RGPD by design", "Revue manuelle, quotas anti-ban"],
          ].map(([icon, title, desc]) => (
            <div key={title} className="rounded-2xl bg-white border border-slate-200 p-4">
              <div className="text-2xl">{icon}</div>
              <div className="font-semibold mt-2">{title}</div>
              <div className="text-xs text-slate-500 mt-1">{desc}</div>
            </div>
          ))}
        </div>
      </section>
    </main>
  );
}
