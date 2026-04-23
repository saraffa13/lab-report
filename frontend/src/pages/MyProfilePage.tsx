import { FormEvent, useState } from "react";
import {
  cachedUser,
  changeMyPassword,
  storeSession,
  updateMyProfile,
  type User,
} from "@/api/auth";
import { Icon } from "@/components/ui/Icon";

export default function MyProfilePage() {
  const current = cachedUser();
  const [full_name, setFullName] = useState(current?.full_name ?? "");
  const [email, setEmail] = useState(current?.email ?? "");
  const [profileBusy, setProfileBusy] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [pwBusy, setPwBusy] = useState(false);
  const [pwMsg, setPwMsg] = useState<{ kind: "ok" | "err"; text: string } | null>(null);

  async function saveProfile(e: FormEvent) {
    e.preventDefault();
    setProfileMsg(null);
    setProfileBusy(true);
    try {
      const updated: User = await updateMyProfile({ full_name, email });
      // Refresh the cached session so the header picks up the new name/email.
      const tokens = {
        access: localStorage.getItem("labreport.access_token") ?? "",
        refresh: localStorage.getItem("labreport.refresh_token") ?? "",
      };
      storeSession({ ...tokens, user: updated });
      setProfileMsg({ kind: "ok", text: "Profile updated." });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setProfileMsg({ kind: "err", text: e.response?.data?.detail ?? "Failed to update profile." });
    } finally {
      setProfileBusy(false);
    }
  }

  async function savePassword(e: FormEvent) {
    e.preventDefault();
    setPwMsg(null);
    if (newPassword.length < 6) {
      setPwMsg({ kind: "err", text: "New password must be at least 6 characters." });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPwMsg({ kind: "err", text: "New passwords do not match." });
      return;
    }
    setPwBusy(true);
    try {
      await changeMyPassword({ current_password: currentPassword, new_password: newPassword });
      setPwMsg({ kind: "ok", text: "Password updated." });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
    } catch (err: unknown) {
      setPwMsg({ kind: "err", text: extractError(err, "Failed to change password.") });
    } finally {
      setPwBusy(false);
    }
  }

  function extractError(err: unknown, fallback: string): string {
    const e = err as { response?: { data?: unknown } };
    const data = e.response?.data;
    if (typeof data === "string") return data;
    if (data && typeof data === "object") {
      const rec = data as Record<string, unknown>;
      if (typeof rec.detail === "string") return rec.detail;
      const parts: string[] = [];
      for (const [k, v] of Object.entries(rec)) {
        if (Array.isArray(v)) parts.push(`${k}: ${v.join(" ")}`);
        else if (typeof v === "string") parts.push(`${k}: ${v}`);
      }
      if (parts.length) return parts.join(" · ");
    }
    return fallback;
  }

  return (
    <div className="flex flex-col gap-6 max-w-2xl mx-auto">
      <header>
        <h1 className="text-3xl font-extrabold text-on-primary-fixed tracking-tight">
          My Profile
        </h1>
        <p className="text-sm text-on-surface-variant mt-1">
          Update your name, email, or password.
        </p>
      </header>

      <form
        onSubmit={saveProfile}
        className="bg-surface-container-lowest rounded-xl p-6 ring-1 ring-outline-variant/15 shadow-dossier flex flex-col gap-4"
      >
        <h2 className="text-xs font-bold text-on-primary-fixed uppercase tracking-wider flex items-center gap-2">
          <Icon name="person" size={16} className="text-primary-container" />
          Profile
        </h2>
        <Field label="Full name">
          <input
            value={full_name}
            onChange={(e) => setFullName(e.target.value)}
            className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none text-sm"
          />
        </Field>
        <Field label="Email">
          <input
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none text-sm"
          />
        </Field>
        <Field label="Phone (login ID — contact the lab to change)">
          <input
            value={current?.phone ?? ""}
            disabled
            className="w-full bg-surface-container border border-outline-variant/15 text-on-surface-variant p-2.5 rounded-md text-sm"
          />
        </Field>
        {profileMsg && <Message msg={profileMsg} />}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={profileBusy}
            className="bg-gradient-to-b from-primary-container to-primary text-on-primary px-5 py-2 rounded-md font-medium text-sm hover:opacity-95 transition-opacity disabled:opacity-60"
          >
            {profileBusy ? "Saving…" : "Save Profile"}
          </button>
        </div>
      </form>

      <form
        onSubmit={savePassword}
        className="bg-surface-container-lowest rounded-xl p-6 ring-1 ring-outline-variant/15 shadow-dossier flex flex-col gap-4"
      >
        <h2 className="text-xs font-bold text-on-primary-fixed uppercase tracking-wider flex items-center gap-2">
          <Icon name="lock" size={16} className="text-primary-container" />
          Change Password
        </h2>
        <Field label="Current password">
          <input
            type="password"
            value={currentPassword}
            onChange={(e) => setCurrentPassword(e.target.value)}
            required
            className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none text-sm"
          />
        </Field>
        <Field label="New password">
          <input
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={6}
            className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none text-sm"
          />
        </Field>
        <Field label="Confirm new password">
          <input
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none text-sm"
          />
        </Field>
        {pwMsg && <Message msg={pwMsg} />}
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={pwBusy}
            className="bg-gradient-to-b from-primary-container to-primary text-on-primary px-5 py-2 rounded-md font-medium text-sm hover:opacity-95 transition-opacity disabled:opacity-60"
          >
            {pwBusy ? "Saving…" : "Update Password"}
          </button>
        </div>
      </form>
    </div>
  );
}

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="flex flex-col gap-1.5">
      <span className="text-xs text-on-surface-variant uppercase tracking-wider font-medium">
        {label}
      </span>
      {children}
    </label>
  );
}

function Message({ msg }: { msg: { kind: "ok" | "err"; text: string } }) {
  return (
    <div
      className={
        msg.kind === "ok"
          ? "rounded-md bg-secondary-container text-on-secondary-container px-3 py-2 text-sm"
          : "rounded-md bg-error-container text-on-error-container px-3 py-2 text-sm"
      }
    >
      {msg.text}
    </div>
  );
}
