import { FormEvent, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { login, storeSession, hasSession } from "@/api/auth";
import { Icon } from "@/components/ui/Icon";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("demo@labreport.local");
  const [password, setPassword] = useState("demo1234");
  const [showPw, setShowPw] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  if (hasSession()) return <Navigate to="/dashboard" replace />;

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const resp = await login(email, password);
      storeSession(resp);
      navigate("/dashboard", { replace: true });
    } catch {
      setError("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="w-full h-screen flex bg-surface">
      {/* Left brand panel */}
      <section className="hidden lg:flex flex-col justify-center items-start w-1/2 bg-surface-container-low relative overflow-hidden p-16">
        <div className="relative z-10 max-w-lg">
          <h1 className="text-on-primary-fixed font-black text-4xl tracking-tighter uppercase mb-6">
            K S Ganga Medical Clinic
          </h1>
          <p className="text-on-surface-variant text-xl font-medium leading-relaxed mb-12">
            Professional lab reports in seconds. Elevating diagnostic clarity through precise information architecture.
          </p>
          <div className="flex items-center gap-2 text-on-surface-variant text-sm">
            <Icon name="shield_person" size={18} />
            <span>Secure multi-tenant lab workspace</span>
          </div>
        </div>
        <div
          aria-hidden
          className="absolute -right-24 -bottom-24 w-[540px] h-[540px] rounded-full opacity-60 mix-blend-multiply"
          style={{
            background:
              "radial-gradient(circle at 30% 30%, rgba(109,245,225,0.5), transparent 60%), radial-gradient(circle at 70% 70%, rgba(11,42,91,0.25), transparent 60%)",
          }}
        />
      </section>

      {/* Right login card */}
      <section className="w-full lg:w-1/2 flex flex-col justify-center items-center p-8 sm:p-12 md:p-24 bg-surface">
        <div className="w-full max-w-md bg-surface-container-lowest p-10 rounded-xl shadow-[0px_4px_32px_rgba(0,22,58,0.04)] ring-1 ring-outline-variant/15 flex flex-col gap-8">
          <div className="lg:hidden w-full text-center mb-2">
            <h1 className="text-on-primary-fixed font-black text-2xl tracking-tighter uppercase">
              K S Ganga Clinic
            </h1>
          </div>

          <div className="flex flex-col gap-2">
            <h2 className="text-on-primary-fixed font-bold text-3xl tracking-tight">Access Dossier</h2>
            <p className="text-on-surface-variant text-sm">
              Enter your credentials to access the clinical ledger.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="flex flex-col gap-6">
            <div className="flex flex-col gap-1.5">
              <label className="text-on-surface-variant text-sm font-semibold" htmlFor="email">
                Email Address
              </label>
              <div className="relative group">
                <Icon
                  name="mail"
                  size={18}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant opacity-70"
                />
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface text-sm rounded-lg pl-10 pr-4 py-3 focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary focus:outline-none transition-all placeholder:text-on-surface-variant/50"
                  placeholder="clinician@ksganga.com"
                />
              </div>
            </div>

            <div className="flex flex-col gap-1.5">
              <div className="flex justify-between items-center">
                <label className="text-on-surface-variant text-sm font-semibold" htmlFor="password">
                  Password
                </label>
                <a className="text-secondary text-xs font-semibold hover:underline" href="#">
                  Forgot password?
                </a>
              </div>
              <div className="relative group">
                <Icon
                  name="lock"
                  size={18}
                  className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant opacity-70"
                />
                <input
                  id="password"
                  type={showPw ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface text-sm rounded-lg pl-10 pr-10 py-3 focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary focus:outline-none transition-all placeholder:text-on-surface-variant/50"
                  placeholder="••••••••"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant opacity-70 hover:opacity-100 focus:outline-none"
                >
                  <Icon name={showPw ? "visibility" : "visibility_off"} size={18} />
                </button>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 text-sm text-on-error-container bg-error-container rounded-lg px-3 py-2">
                <Icon name="error" size={16} />
                <span>{error}</span>
              </div>
            )}

            <div className="pt-1 flex flex-col gap-3">
              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-b from-primary-container to-primary text-on-primary font-semibold text-sm rounded-lg py-3 px-4 shadow-sm hover:opacity-95 active:scale-[0.98] transition-all flex justify-center items-center gap-2 disabled:opacity-60"
              >
                <span>{loading ? "Signing in…" : "Login"}</span>
                {!loading && <Icon name="arrow_forward" size={16} />}
              </button>
              <button
                type="button"
                className="w-full bg-surface-container-high text-primary-container font-semibold text-sm rounded-lg py-3 px-4 hover:bg-surface-container-highest transition-colors flex justify-center items-center gap-2"
              >
                <Icon name="dialpad" size={16} />
                <span>Login with OTP</span>
              </button>
            </div>
          </form>

          <div className="pt-4 border-t border-outline-variant/10 flex flex-col items-center gap-2 text-center">
            <p className="text-on-surface-variant text-xs">
              Authorized personnel only. Activities are monitored.
            </p>
            <p className="text-on-surface-variant text-[11px]">
              Demo: <code className="font-mono">demo@labreport.local</code> /{" "}
              <code className="font-mono">demo1234</code>
            </p>
          </div>
        </div>
      </section>
    </main>
  );
}
