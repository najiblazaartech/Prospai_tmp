"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { login, register, setToken } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [name, setName] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      const res = mode === "login" ? await login(email, password) : await register(email, password, name);
      setToken(res.access_token);
      router.push("/dashboard");
    } catch (err: any) {
      setError(mode === "login" ? "Email ou mot de passe incorrect." : String(err.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-md">
        <div className="flex items-center gap-2 justify-center mb-6">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-sky-400 flex items-center justify-center text-white font-bold">P</div>
          <span className="font-bold text-lg">ProspAI</span>
        </div>
        <form onSubmit={submit} className="rounded-2xl bg-white border border-slate-200 p-6 space-y-4">
          <div className="flex bg-slate-100 rounded-xl p-1">
            {(["login", "register"] as const).map((m) => (
              <button key={m} type="button" onClick={() => { setMode(m); setError(""); }}
                className={`flex-1 rounded-lg py-1.5 text-sm font-medium ${mode === m ? "bg-white shadow text-indigo-600" : "text-slate-600"}`}>
                {m === "login" ? "Connexion" : "Inscription"}
              </button>
            ))}
          </div>
          {mode === "register" && (
            <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Nom complet" required
              className="w-full rounded-xl border border-slate-200 p-3 text-sm" />
          )}
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email" required
            className="w-full rounded-xl border border-slate-200 p-3 text-sm" />
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Mot de passe" required minLength={8}
            className="w-full rounded-xl border border-slate-200 p-3 text-sm" />
          {error && <div role="alert" className="text-xs text-red-600">{error}</div>}
          <button disabled={loading}
            className="w-full rounded-xl bg-indigo-600 p-3 text-sm font-semibold text-white hover:bg-indigo-700 disabled:opacity-50">
            {loading ? "..." : mode === "login" ? "Se connecter" : "Créer mon compte"}
          </button>
        </form>
      </div>
    </main>
  );
}
