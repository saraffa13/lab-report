import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { createPatient } from "@/api/patients";
import { Icon } from "@/components/ui/Icon";

export default function PatientCreatePage() {
  const nav = useNavigate();
  const [form, setForm] = useState({
    name: "",
    sex: "M" as "M" | "F" | "O",
    age: "",
    blood_group: "",
    phone: "",
    alternate_phone: "",
    email: "",
    address: "",
    city: "",
    state: "",
    pincode: "",
  });
  const [err, setErr] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setSubmitting(true);
    try {
      const p = await createPatient({
        name: form.name,
        sex: form.sex,
        age: form.age ? Number(form.age) : null,
        age_unit: "years",
        blood_group: form.blood_group,
        phone: form.phone,
        alternate_phone: form.alternate_phone,
        email: form.email,
        address: form.address,
        city: form.city,
        state: form.state,
        pincode: form.pincode,
      });
      nav(`/patients/${p.id}`, { replace: true });
    } catch (e: unknown) {
      const ex = e as { response?: { data?: Record<string, string[]> } };
      setErr(
        ex.response?.data
          ? Object.entries(ex.response.data)
              .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
              .join(" · ")
          : "Failed to create patient.",
      );
    } finally {
      setSubmitting(false);
    }
  }

  const set =
    (k: keyof typeof form) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) =>
      setForm({ ...form, [k]: e.target.value });

  return (
    <form onSubmit={handleSubmit} className="mx-auto max-w-4xl flex flex-col gap-6">
      <div className="flex items-center gap-2 text-on-surface-variant text-sm">
        <Link to="/patients" className="hover:text-primary-container transition-colors">
          Patients
        </Link>
        <Icon name="chevron_right" size={16} />
        <span className="text-on-surface font-medium">New Patient</span>
      </div>

      <div>
        <h1 className="text-3xl font-bold text-on-primary-fixed tracking-tight">
          Register New Patient
        </h1>
        <p className="text-on-surface-variant text-sm mt-1">
          Create a new patient record. A unique patient code will be auto-generated.
        </p>
      </div>

      <div className="bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 p-8 flex flex-col gap-8">
        <Section
          label="Demographics"
          hint="Basic identity fields printed on the report letterhead."
        >
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <Field label="Full Name" required>
              <input
                required
                className="stitch-input"
                value={form.name}
                onChange={set("name")}
                placeholder="e.g. Name  "
              />
            </Field>
            <Field label="Biological Sex" required>
              <div className="relative">
                <select className="stitch-input appearance-none pr-9" value={form.sex} onChange={set("sex")}>
                  <option value="M">Male</option>
                  <option value="F">Female</option>
                  <option value="O">Other</option>
                </select>
                <Icon
                  name="expand_more"
                  size={18}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
                />
              </div>
            </Field>
            <Field label="Age (Years)">
              <input
                type="number"
                min={0}
                max={150}
                className="stitch-input"
                value={form.age}
                onChange={set("age")}
                placeholder="45"
              />
            </Field>
            <Field label="Blood Group">
              <div className="relative">
                <select
                  className="stitch-input appearance-none pr-9"
                  value={form.blood_group}
                  onChange={set("blood_group")}
                >
                  <option value="">—</option>
                  {["O+", "O-", "A+", "A-", "B+", "B-", "AB+", "AB-"].map((b) => (
                    <option key={b} value={b}>
                      {b}
                    </option>
                  ))}
                </select>
                <Icon
                  name="expand_more"
                  size={18}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
                />
              </div>
            </Field>
          </div>
        </Section>

        <Separator />

        <Section label="Contact" hint="Primary reach for report delivery and reminders.">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
            <Field label="Phone">
              <input
                className="stitch-input"
                value={form.phone}
                onChange={set("phone")}
                placeholder="+91 "
              />
            </Field>
            <Field label="Alternate Phone">
              <input
                className="stitch-input"
                value={form.alternate_phone}
                onChange={set("alternate_phone")}
              />
            </Field>
            <Field label="Email">
              <input
                type="email"
                className="stitch-input"
                value={form.email}
                onChange={set("email")}
              />
            </Field>
          </div>
        </Section>

        <Separator />

        <Section label="Address" hint="Optional — printed if present on billing correspondence.">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <Field label="Street / Line 1">
              <input className="stitch-input" value={form.address} onChange={set("address")} />
            </Field>
            <Field label="City">
              <input className="stitch-input" value={form.city} onChange={set("city")} />
            </Field>
            <Field label="State">
              <input className="stitch-input" value={form.state} onChange={set("state")} />
            </Field>
            <Field label="Pincode">
              <input className="stitch-input" value={form.pincode} onChange={set("pincode")} />
            </Field>
          </div>
        </Section>
      </div>

      {err && (
        <div className="rounded-lg bg-error-container text-on-error-container px-4 py-3 text-sm flex items-center gap-2">
          <Icon name="error" size={16} />
          {err}
        </div>
      )}

      <div className="flex gap-3 justify-end">
        <button
          type="button"
          onClick={() => nav(-1)}
          className="px-5 py-2.5 rounded-lg text-sm font-medium text-on-surface-variant hover:bg-surface-container-low transition-colors"
        >
          Cancel
        </button>
        <button
          disabled={submitting}
          className="bg-gradient-to-b from-primary-container to-primary text-on-primary px-6 py-2.5 rounded-lg font-semibold text-sm shadow-md hover:opacity-95 transition-opacity flex items-center gap-2 disabled:opacity-60"
        >
          {submitting ? "Creating…" : "Create Patient"}
          {!submitting && <Icon name="arrow_forward" size={16} />}
        </button>
      </div>

      <style>{`
        .stitch-input {
          width: 100%;
          background: #e0e3e5;
          border: 1px solid rgba(196, 198, 208, 0.15);
          color: #191c1e;
          padding: 0.625rem 0.875rem;
          border-radius: 0.375rem;
          font-size: 0.875rem;
          outline: none;
          transition: all 0.2s;
        }
        .stitch-input:focus {
          background: #ffffff;
          border-color: #006b5f;
          box-shadow: 0 0 0 1px #006b5f;
        }
      `}</style>
    </form>
  );
}

function Section({
  label,
  hint,
  children,
}: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}) {
  return (
    <section className="flex gap-8 items-start">
      <div className="w-48 shrink-0">
        <label className="block text-sm font-semibold text-primary-container mb-1">{label}</label>
        {hint && <p className="text-xs text-on-surface-variant leading-relaxed">{hint}</p>}
      </div>
      <div className="flex-1 min-w-0">{children}</div>
    </section>
  );
}

function Separator() {
  return <hr className="border-0 bg-surface-container-low h-px w-full" />;
}

function Field({
  label,
  required,
  children,
}: {
  label: string;
  required?: boolean;
  children: React.ReactNode;
}) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium text-on-surface-variant">
        {label}
        {required && <span className="text-error"> *</span>}
      </span>
      {children}
    </label>
  );
}
