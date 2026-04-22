import { useEffect, useState, FormEvent } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { getLab, updateLab, type Lab } from "@/api/lab";
import { Icon } from "@/components/ui/Icon";

type Section = "profile" | "branches" | "signatures" | "subscription";

export default function SettingsPage() {
  const qc = useQueryClient();
  const { data: lab } = useQuery({ queryKey: ["lab"], queryFn: getLab });
  const [form, setForm] = useState<Partial<Lab>>({});
  const [msg, setMsg] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [section, setSection] = useState<Section>("profile");

  useEffect(() => {
    if (lab) setForm(lab);
  }, [lab]);

  async function save(e: FormEvent) {
    e.preventDefault();
    setMsg(null);
    setSaving(true);
    try {
      await updateLab(form);
      await qc.invalidateQueries({ queryKey: ["lab"] });
      setMsg("Saved successfully.");
      setTimeout(() => setMsg(null), 3000);
    } catch {
      setMsg("Save failed.");
    } finally {
      setSaving(false);
    }
  }

  const set = (k: keyof Lab) => (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
    setForm({ ...form, [k]: e.target.value });

  if (!lab) {
    return <p className="text-on-surface-variant text-sm">Loading settings…</p>;
  }

  return (
    <main className="flex flex-col lg:flex-row gap-10 max-w-7xl mx-auto">
      <aside className="lg:w-64 shrink-0 flex flex-col gap-2">
        <h1 className="text-xl font-bold text-on-primary-fixed mb-4 tracking-tight">
          Configuration
        </h1>
        <nav className="flex flex-col gap-1">
          <SidebarTab
            icon="domain"
            label="Lab Profile"
            active={section === "profile"}
            onClick={() => setSection("profile")}
          />
          <SidebarTab
            icon="share"
            label="Branches"
            active={section === "branches"}
            onClick={() => setSection("branches")}
          />
          <SidebarTab
            icon="draw"
            label="Signatures"
            active={section === "signatures"}
            onClick={() => setSection("signatures")}
          />
          <SidebarTab
            icon="workspace_premium"
            label="Subscription Plan"
            active={section === "subscription"}
            onClick={() => setSection("subscription")}
          />
        </nav>
      </aside>

      <div className="flex-1 min-w-0 bg-surface-container-lowest rounded-xl p-8 md:p-10 shadow-ambient ring-1 ring-outline-variant/10">
        {section === "profile" && (
          <form onSubmit={save} className="flex flex-col gap-6">
            <header className="mb-4 flex justify-between items-end">
              <div>
                <h2 className="text-3xl font-bold text-on-primary-fixed tracking-tight mb-2">
                  Lab Identity Profile
                </h2>
                <p className="text-on-surface-variant text-sm">
                  Manage the official credentials and visual identity appearing on patient
                  reports.
                </p>
              </div>
              <button
                disabled={saving}
                className="bg-gradient-to-b from-primary-container to-primary text-on-primary px-6 py-2.5 rounded-md font-medium text-sm hover:opacity-95 transition-opacity shadow-sm disabled:opacity-60"
              >
                {saving ? "Saving…" : "Save Dossier"}
              </button>
            </header>

            {msg && (
              <div
                className={
                  msg.startsWith("Save fail")
                    ? "bg-error-container text-on-error-container rounded-lg px-4 py-2.5 text-sm flex items-center gap-2"
                    : "bg-secondary-container text-on-secondary-container rounded-lg px-4 py-2.5 text-sm flex items-center gap-2"
                }
              >
                <Icon name={msg.startsWith("Save fail") ? "error" : "check_circle"} size={16} />
                {msg}
              </div>
            )}

            <SettingsSection
              label="Entity Details"
              hint="Registered name and operational headquarters."
            >
              <SettingsField label="Registered Laboratory Name" required>
                <input
                  className="stitch-field"
                  value={form.name ?? ""}
                  onChange={set("name")}
                  required
                />
              </SettingsField>
              <SettingsField label="Official Address">
                <textarea
                  className="stitch-field resize-none"
                  rows={3}
                  value={form.address ?? ""}
                  onChange={set("address")}
                />
              </SettingsField>
              <div className="grid grid-cols-3 gap-4">
                <SettingsField label="City">
                  <input className="stitch-field" value={form.city ?? ""} onChange={set("city")} />
                </SettingsField>
                <SettingsField label="State">
                  <input className="stitch-field" value={form.state ?? ""} onChange={set("state")} />
                </SettingsField>
                <SettingsField label="Pincode">
                  <input
                    className="stitch-field"
                    value={form.pincode ?? ""}
                    onChange={set("pincode")}
                  />
                </SettingsField>
              </div>
            </SettingsSection>

            <Divider />

            <SettingsSection label="Contact" hint="Phone and digital reach printed on reports.">
              <div className="grid grid-cols-2 gap-4">
                <SettingsField label="Phone">
                  <input
                    className="stitch-field"
                    value={form.phone ?? ""}
                    onChange={set("phone")}
                  />
                </SettingsField>
                <SettingsField label="Email">
                  <input
                    type="email"
                    className="stitch-field"
                    value={form.email ?? ""}
                    onChange={set("email")}
                  />
                </SettingsField>
                <SettingsField label="Website">
                  <input
                    className="stitch-field"
                    value={form.website ?? ""}
                    onChange={set("website")}
                  />
                </SettingsField>
              </div>
            </SettingsSection>

            <Divider />

            <SettingsSection
              label="Accreditations"
              hint="Quality control certification numbers shown on footer."
            >
              <div className="grid grid-cols-2 gap-4">
                <SettingsField label="GST / Tax Registration">
                  <input
                    className="stitch-field font-mono text-sm"
                    value={form.tax_registration ?? ""}
                    onChange={set("tax_registration")}
                  />
                </SettingsField>
                <SettingsField label="Accreditation Info (ISO / NABL)">
                  <input
                    className="stitch-field font-mono text-sm"
                    value={form.accreditation_info ?? ""}
                    onChange={set("accreditation_info")}
                  />
                </SettingsField>
              </div>
            </SettingsSection>

            <Divider />

            <SettingsSection
              label="Visual Identity"
              hint="Primary color accents on generated reports."
            >
              <div className="grid grid-cols-2 gap-4">
                <SettingsField label="Primary Color (hex)">
                  <input
                    className="stitch-field font-mono"
                    placeholder="#0B2A5B"
                    value={form.primary_color ?? ""}
                    onChange={set("primary_color")}
                  />
                </SettingsField>
                <SettingsField label="Secondary Color (hex)">
                  <input
                    className="stitch-field font-mono"
                    placeholder="#006B5F"
                    value={form.secondary_color ?? ""}
                    onChange={set("secondary_color")}
                  />
                </SettingsField>
              </div>
            </SettingsSection>
          </form>
        )}

        {section !== "profile" && <PlaceholderSection section={section} />}
      </div>

      <style>{`
        .stitch-field {
          width: 100%;
          background: #e0e3e5;
          border: 0;
          padding: 0.625rem 0.875rem;
          border-radius: 0.375rem;
          color: #191c1e;
          font-size: 0.875rem;
          outline: none;
          transition: all 0.2s;
        }
        .stitch-field:focus {
          background: #ffffff;
          box-shadow: 0 0 0 1px #006b5f;
        }
      `}</style>
    </main>
  );
}

function SidebarTab({
  icon,
  label,
  active,
  onClick,
}: {
  icon: string;
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? "flex items-center gap-3 px-4 py-3 rounded-xl bg-surface-container-high text-primary-container font-semibold transition-colors text-left"
          : "flex items-center gap-3 px-4 py-3 rounded-xl text-on-surface-variant hover:bg-surface-container-low hover:text-primary-container font-medium transition-colors text-left"
      }
    >
      <Icon name={icon} size={20} filled={active} className={active ? "text-secondary" : ""} />
      {label}
    </button>
  );
}

function SettingsSection({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="flex flex-col md:flex-row gap-8 items-start">
      <div className="md:w-48 shrink-0">
        <label className="block text-sm font-semibold text-primary-container mb-1">
          {label}
        </label>
        {hint && <p className="text-xs text-on-surface-variant leading-relaxed">{hint}</p>}
      </div>
      <div className="flex-1 min-w-0 flex flex-col gap-4">{children}</div>
    </section>
  );
}

function SettingsField({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div>
      <label className="block text-sm font-medium text-on-surface-variant mb-1.5">
        {label}
        {required && <span className="text-error"> *</span>}
      </label>
      {children}
    </div>
  );
}

function Divider() {
  return <hr className="border-0 bg-surface-container-low h-px w-full" />;
}

function PlaceholderSection({ section }: { section: "branches" | "signatures" | "subscription" }) {
  const copy = {
    branches: {
      title: "Branch Locations",
      desc: "Configure additional lab branches for multi-location operations.",
      icon: "share",
    },
    signatures: {
      title: "Signatory Management",
      desc: "Upload and manage pathologist signatures that appear on finalized reports.",
      icon: "draw",
    },
    subscription: {
      title: "Subscription Plan",
      desc: "Review your plan tier, usage, and renewal details.",
      icon: "workspace_premium",
    },
  }[section];

  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <Icon name={copy.icon} size={48} className="text-outline-variant mb-4" />
      <h3 className="text-xl font-bold text-on-primary-fixed mb-2">{copy.title}</h3>
      <p className="text-on-surface-variant text-sm max-w-sm">{copy.desc}</p>
      <p className="text-outline text-xs mt-4 italic">Coming soon</p>
    </div>
  );
}
