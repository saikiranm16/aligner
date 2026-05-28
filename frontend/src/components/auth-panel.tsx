import { FormEvent, useState } from "react";
import { AuthResponse, UserResponse } from "../types";

interface AuthPanelProps {
  user: UserResponse | null;
  onLogin: (email: string, password: string) => Promise<AuthResponse>;
  onRegister: (email: string, password: string) => Promise<AuthResponse>;
  onLogout: () => void;
}

export function AuthPanel({ user, onLogin, onRegister, onLogout }: AuthPanelProps) {
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    setLoading(true);
    setMessage(null);
    try {
      const response = mode === "login" ? await onLogin(email, password) : await onRegister(email, password);
      setMessage(`${mode === "login" ? "Signed in" : "Account created"} for ${response.user.email}`);
      setEmail("");
      setPassword("");
    } catch (error) {
      setMessage(error instanceof Error ? error.message : "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <section className="panel p-6">
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-xl font-semibold">Account Access</h2>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-300">
            Optional sign-in unlocks a personalized dashboard and protected API access.
          </p>
        </div>
        {user ? (
          <button
            type="button"
            onClick={onLogout}
            className="rounded-full border border-slate-300 px-4 py-2 text-sm font-semibold transition hover:border-slate-900 dark:border-white/15 dark:hover:border-white/40"
          >
            Log Out
          </button>
        ) : null}
      </div>

      {user ? (
        <div className="mt-5 rounded-2xl bg-emerald-50 px-4 py-4 text-sm text-emerald-800 dark:bg-emerald-500/10 dark:text-emerald-200">
          Signed in as <span className="font-semibold">{user.email}</span>
        </div>
      ) : (
        <form onSubmit={submit} className="mt-5 space-y-4">
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setMode("login")}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                mode === "login"
                  ? "bg-slate-950 text-white dark:bg-white dark:text-slate-950"
                  : "border border-slate-300 dark:border-white/15"
              }`}
            >
              Login
            </button>
            <button
              type="button"
              onClick={() => setMode("register")}
              className={`rounded-full px-4 py-2 text-sm font-semibold transition ${
                mode === "register"
                  ? "bg-slate-950 text-white dark:bg-white dark:text-slate-950"
                  : "border border-slate-300 dark:border-white/15"
              }`}
            >
              Register
            </button>
          </div>

          <div className="grid gap-3">
            <input
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Email address"
              className="rounded-2xl border border-slate-300/80 bg-white/70 px-4 py-3 text-sm outline-none transition focus:border-slate-900 dark:border-white/15 dark:bg-white/5 dark:focus:border-white/40"
            />
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Password"
              className="rounded-2xl border border-slate-300/80 bg-white/70 px-4 py-3 text-sm outline-none transition focus:border-slate-900 dark:border-white/15 dark:bg-white/5 dark:focus:border-white/40"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="rounded-full bg-gradient-to-r from-accent to-glow px-5 py-3 text-sm font-semibold text-white transition hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Please wait..." : mode === "login" ? "Sign In" : "Create Account"}
          </button>
        </form>
      )}

      {message ? (
        <p className="mt-4 text-sm text-slate-600 dark:text-slate-300">{message}</p>
      ) : null}
    </section>
  );
}
