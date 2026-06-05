import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import {
  getPackage,
  getTemplate,
  listPackages,
  listTemplates,
  type Test,
} from "@/api/catalog";
import { listPatients, type Patient } from "@/api/patients";
import {
  createReferringDoctor,
  createReport,
  downloadPdf,
  listReferringDoctors,
  listSampleCollectors,
  type ReferringDoctor,
} from "@/api/reports";
import { Icon } from "@/components/ui/Icon";

type PatientForm = {
  name: string;
  sex: "M" | "F" | "O";
  age: string;
  phone: string;
  city: string;
  blood_group: string;
};

const EMPTY_PATIENT: PatientForm = {
  name: "", sex: "M", age: "", phone: "", city: "", blood_group: "",
};

const BLOOD_GROUP_OPTIONS = [
  { value: "", label: "Unknown" },
  { value: "A+", label: "A+" },
  { value: "A-", label: "A-" },
  { value: "B+", label: "B+" },
  { value: "B-", label: "B-" },
  { value: "O+", label: "O+" },
  { value: "O-", label: "O-" },
  { value: "AB+", label: "AB+" },
  { value: "AB-", label: "AB-" },
];

const TEMPLATE_ICON: Record<string, string> = {
  CBC: "bloodtype",
  LFT: "science",
  KFT: "nephrology",
  TFT: "monitor_heart",
  URINE: "water_drop",
  LIPID: "water_drop",
  WIDAL: "biotech",
  DENGUE: "coronavirus",
  MALARIA: "bug_report",
};

function iconForCode(code: string) {
  return TEMPLATE_ICON[code.toUpperCase()] ?? "science";
}

function localNowIso(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
}

export default function CreateReportPage() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [patient, setPatient] = useState<PatientForm>(EMPTY_PATIENT);
  const [referredBy, setReferredBy] = useState("Self");
  const [clinicalHistory, setClinicalHistory] = useState("");
  const [templateId, setTemplateId] = useState<string>("");
  const [packageId, setPackageId] = useState<string>("");
  const [packageTests, setPackageTests] = useState<Test[]>([]);
  const [results, setResults] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [patientMode, setPatientMode] = useState<"new" | "existing">("new");
  const [collectedBy, setCollectedBy] = useState("");
  const [registeredOn, setRegisteredOn] = useState<string>(() => localNowIso());
  const [collectedOn, setCollectedOn] = useState<string>(() => localNowIso());
  const [reportedOn, setReportedOn] = useState<string>(() => localNowIso());

  const { data: templates } = useQuery({ queryKey: ["templates"], queryFn: listTemplates });
  const { data: packages } = useQuery({ queryKey: ["packages"], queryFn: listPackages });
  const { data: doctors } = useQuery({
    queryKey: ["referring-doctors"],
    queryFn: () => listReferringDoctors(),
  });
  const { data: collectors } = useQuery({
    queryKey: ["sample-collectors"],
    queryFn: listSampleCollectors,
    refetchOnMount: "always",
    staleTime: 0,
  });
  const { data: template } = useQuery({
    queryKey: ["template", templateId],
    queryFn: () => getTemplate(templateId),
    enabled: !!templateId,
  });

  const tests: Test[] = useMemo(() => {
    if (packageId) return packageTests;
    return template ? template.template_tests.map((tt) => tt.test) : [];
  }, [packageId, packageTests, template]);

  useEffect(() => {
    setResults({});
  }, [templateId, packageId]);

  // When a package is picked, fetch the full detail of each member template
  // and union their tests (de-duped, preserving order).
  useEffect(() => {
    if (!packageId) {
      setPackageTests([]);
      return;
    }
    let cancelled = false;
    (async () => {
      const pkg = await getPackage(packageId);
      const tplDetails = await Promise.all(
        pkg.package_templates
          .sort((a, b) => a.display_order - b.display_order)
          .map((pt) => getTemplate(pt.template)),
      );
      if (cancelled) return;
      const seen = new Set<string>();
      const merged: Test[] = [];
      for (const tpl of tplDetails) {
        for (const tt of tpl.template_tests) {
          if (seen.has(tt.test.id)) continue;
          seen.add(tt.test.id);
          merged.push(tt.test);
        }
      }
      setPackageTests(merged);
    })();
    return () => { cancelled = true; };
  }, [packageId]);

  const stepPatientDone = patient.name.trim().length > 0;
  const stepTemplateDone = !!(templateId || packageId);
  const stepResultsDone = tests.length > 0 && tests.every((t) => (results[t.id] ?? "").trim());

  function pickRange(t: Test): string {
    const sex = patient.sex;
    const forSex =
      t.reference_ranges.find((r) => r.sex === sex) ??
      t.reference_ranges.find((r) => r.sex === "A");
    return forSex?.display ?? "";
  }

  function flagFor(t: Test, value: string): "normal" | "high" | "low" | null {
    const num = parseFloat(value);
    if (!Number.isFinite(num)) return null;
    const range =
      t.reference_ranges.find((r) => r.sex === patient.sex) ??
      t.reference_ranges.find((r) => r.sex === "A");
    if (!range?.display) return null;
    const match = range.display.match(/(-?\d+\.?\d*)\s*[-–]\s*(-?\d+\.?\d*)/);
    if (!match) return null;
    const low = Number(match[1]);
    const high = Number(match[2]);
    if (num > high) return "high";
    if (num < low) return "low";
    return "normal";
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    if (!templateId && !packageId) return setError("Pick a template or a package.");
    const missing = tests.filter((t) => !results[t.id]?.trim());
    if (missing.length > 0)
      return setError(`Enter a value for: ${missing.map((t) => t.name).join(", ")}`);
    setSubmitting(true);
    try {
      const report = await createReport({
        patient: {
          name: patient.name,
          sex: patient.sex,
          age: patient.age ? Number(patient.age) : null,
          age_unit: "years",
          phone: patient.phone,
          city: patient.city,
          blood_group: patient.blood_group,
        },
        template_id: templateId || undefined,
        package_id: packageId || undefined,
        results: tests.map((t) => ({ test_id: t.id, value: results[t.id] })),
        referred_by_text: referredBy,
        clinical_history: clinicalHistory,
        billing_date: registeredOn ? new Date(registeredOn).toISOString() : null,
        sample_collected_by_name: collectedBy.trim(),
        sample_collected_at: collectedOn ? new Date(collectedOn).toISOString() : null,
        report_released_at: reportedOn ? new Date(reportedOn).toISOString() : null,
      });
      const typed = referredBy.trim();
      if (
        typed &&
        typed.toLowerCase() !== "self" &&
        !(doctors ?? []).some((d) => d.name.toLowerCase() === typed.toLowerCase())
      ) {
        try { await createReferringDoctor(typed); } catch { /* non-fatal */ }
      }
      qc.invalidateQueries({ queryKey: ["sample-collectors"] });
      await downloadPdf(report.id, report.suggested_filename);
      navigate("/reports", { replace: true });
    } catch (err: unknown) {
      const e = err as { response?: { data?: { detail?: string } } };
      setError(e.response?.data?.detail ?? "Failed to create report.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="pb-32">
      <div className="max-w-[1200px] mx-auto flex gap-12 items-start">
        {/* Side stepper */}
        <aside className="hidden lg:flex flex-col w-64 sticky top-24 shrink-0 gap-6">
          <div>
            <h2 className="text-2xl font-bold text-on-primary-fixed tracking-tight">
              Report Generator
            </h2>
            <p className="text-sm text-on-surface-variant mt-2">
              Complete all sections to finalize the diagnostic document.
            </p>
          </div>
          <nav className="flex flex-col gap-1 relative">
            <div className="absolute left-[11px] top-4 bottom-4 w-0.5 bg-surface-container-high -z-10" />
            <Step n={1} label="Patient Demographics" done={stepPatientDone} />
            <Step n={2} label="Diagnostic Panel" done={stepTemplateDone} />
            <Step n={3} label="Clinical Observations" done={stepResultsDone} />
          </nav>
        </aside>

        {/* Right content */}
        <div className="flex-1 bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 p-8 md:p-10 min-w-0">
          {/* Step 1 */}
          <section className="mb-14">
            <div className="flex justify-between items-end mb-6">
              <h3 className="text-2xl md:text-3xl font-bold text-on-primary-fixed">
                Patient Demographics
              </h3>
              <div className="bg-surface-container-low p-1 rounded-lg flex gap-1">
                <button
                  type="button"
                  onClick={() => setPatientMode("new")}
                  className={
                    patientMode === "new"
                      ? "bg-surface-container-lowest text-primary-container shadow-sm px-4 py-1.5 rounded-md text-sm font-medium"
                      : "text-on-surface-variant px-4 py-1.5 rounded-md text-sm font-medium"
                  }
                >
                  New Patient
                </button>
                <button
                  type="button"
                  onClick={() => setPatientMode("existing")}
                  className={
                    patientMode === "existing"
                      ? "bg-surface-container-lowest text-primary-container shadow-sm px-4 py-1.5 rounded-md text-sm font-medium"
                      : "text-on-surface-variant px-4 py-1.5 rounded-md text-sm font-medium"
                  }
                >
                  Existing
                </button>
              </div>
            </div>
            {patientMode === "existing" && (
              <div className="mb-5">
                <PatientSearch
                  onPick={(p) =>
                    setPatient({
                      name: p.name,
                      sex: (p.sex as "M" | "F" | "O") || "M",
                      age: p.age != null ? String(p.age) : "",
                      phone: p.phone || "",
                      city: p.city || "",
                      blood_group: p.blood_group || "",
                    })
                  }
                />
              </div>
            )}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-5">
              <TextField
                label="Full Name"
                required
                value={patient.name}
                onChange={(v) => setPatient({ ...patient, name: v })}
                placeholder="e.g. Name  "
              />
              <TextField
                label="Phone Number"
                type="tel"
                value={patient.phone}
                onChange={(v) => setPatient({ ...patient, phone: v })}
                placeholder="+91 "
              />
              <TextField
                label="Age (Years)"
                type="number"
                value={patient.age}
                onChange={(v) => setPatient({ ...patient, age: v })}
                placeholder="45"
              />
              <SelectField
                label="Biological Sex"
                value={patient.sex}
                onChange={(v) => setPatient({ ...patient, sex: v as "M" | "F" | "O" })}
                options={[
                  { value: "M", label: "Male" },
                  { value: "F", label: "Female" },
                  { value: "O", label: "Other" },
                ]}
              />
              <TextField
                label="City"
                value={patient.city}
                onChange={(v) => setPatient({ ...patient, city: v })}
                placeholder="Ranchi"
              />
              <SelectField
                label="Blood Group"
                value={patient.blood_group}
                onChange={(v) => setPatient({ ...patient, blood_group: v })}
                options={BLOOD_GROUP_OPTIONS}
              />
              <div className="flex flex-col gap-2">
                <label className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">
                  Clinical History (optional)
                </label>
                <textarea
                  rows={1}
                  value={clinicalHistory}
                  onChange={(e) => setClinicalHistory(e.target.value)}
                  className="bg-surface-container-highest border border-outline-variant/15 text-on-surface p-3 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all text-sm"
                />
              </div>
            </div>
          </section>

          {/* Sample tracking */}
          <section className="mb-14">
            <h3 className="text-2xl font-bold text-on-primary-fixed mb-5">Sample Tracking</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-x-6 gap-y-5">
              <div className="flex flex-col gap-2">
                <label className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">
                  Registered On
                </label>
                <input
                  type="datetime-local"
                  value={registeredOn}
                  onChange={(e) => setRegisteredOn(e.target.value)}
                  className="bg-surface-container-highest border border-outline-variant/15 text-on-surface p-3 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all text-sm"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">
                  Sample Collected By
                </label>
                <input
                  list="sample-collectors-list"
                  value={collectedBy}
                  onChange={(e) => setCollectedBy(e.target.value)}
                  placeholder="e.g. Damundar Mahto, CMLT"
                  className="bg-surface-container-highest border border-outline-variant/15 text-on-surface p-3 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all text-sm"
                  autoComplete="off"
                />
                <datalist id="sample-collectors-list">
                  {(collectors ?? []).map((n) => (
                    <option key={n} value={n} />
                  ))}
                </datalist>
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">
                  Collected On
                </label>
                <input
                  type="datetime-local"
                  value={collectedOn}
                  onChange={(e) => setCollectedOn(e.target.value)}
                  className="bg-surface-container-highest border border-outline-variant/15 text-on-surface p-3 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all text-sm"
                />
              </div>
              <div className="flex flex-col gap-2">
                <label className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">
                  Reported On
                </label>
                <input
                  type="datetime-local"
                  value={reportedOn}
                  onChange={(e) => setReportedOn(e.target.value)}
                  className="bg-surface-container-highest border border-outline-variant/15 text-on-surface p-3 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all text-sm"
                />
              </div>
            </div>
          </section>

          {/* Step 2 */}
          <section className="mb-14">
            <h3 className="text-2xl font-bold text-on-primary-fixed mb-5">Diagnostic Panel</h3>

            {/* Packages — auto-fill multiple templates at the offer price */}
            {packages && packages.length > 0 && (
              <div className="mb-6">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="text-sm font-semibold uppercase tracking-wider text-on-surface-variant">
                    Health Packages
                  </h4>
                  {packageId && (
                    <button
                      type="button"
                      onClick={() => setPackageId("")}
                      className="text-xs text-on-surface-variant hover:text-on-primary-fixed underline"
                    >
                      Clear package
                    </button>
                  )}
                </div>
                <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
                  {packages.map((p) => {
                    const active = packageId === p.id;
                    return (
                      <button
                        type="button"
                        key={p.id}
                        data-package-code={p.code}
                        onClick={() => {
                          setPackageId(p.id);
                          setTemplateId("");
                        }}
                        className={
                          active
                            ? "bg-secondary-container text-on-secondary-container p-4 rounded-lg text-left shadow-md"
                            : "bg-surface-container-low hover:bg-surface-container-highest transition-colors p-4 rounded-lg text-left"
                        }
                      >
                        <div className="flex justify-between items-start mb-1">
                          <Icon name="redeem" size={20} filled={active} />
                          {active && <Icon name="check_circle" size={18} className="text-secondary-fixed" />}
                        </div>
                        <h4 className="font-bold text-sm leading-tight">{p.name}</h4>
                        {p.name_alt && (
                          <p className="text-[11px] opacity-80 mt-0.5">{p.name_alt}</p>
                        )}
                        <div className="flex items-baseline gap-2 mt-2">
                          <span className="text-[11px] line-through text-on-surface-variant">
                            ₹{Number(p.list_price).toFixed(0)}
                          </span>
                          <span className="text-base font-bold text-error">
                            ₹{Number(p.offer_price).toFixed(0)}
                          </span>
                        </div>
                        <p className="text-[10px] mt-1 opacity-80">{p.template_count} templates</p>
                      </button>
                    );
                  })}
                </div>
                <div className="flex items-center my-5">
                  <div className="flex-1 h-px bg-outline-variant/30" />
                  <span className="px-3 text-xs uppercase tracking-wider text-on-surface-variant">
                    or pick a single template
                  </span>
                  <div className="flex-1 h-px bg-outline-variant/30" />
                </div>
              </div>
            )}

            {!templates ? (
              <div className="text-on-surface-variant text-sm">Loading templates…</div>
            ) : (
              <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-3">
                {templates.map((t) => {
                  const active = templateId === t.id;
                  return (
                    <button
                      type="button"
                      key={t.id}
                      data-template-code={t.code}
                      onClick={() => {
                        setTemplateId(t.id);
                        setPackageId("");
                      }}
                      className={
                        active
                          ? "bg-primary-container text-on-primary p-4 rounded-lg text-left shadow-md relative overflow-hidden"
                          : "bg-surface-container-low text-on-surface hover:bg-surface-container-highest transition-colors p-4 rounded-lg text-left cursor-pointer"
                      }
                    >
                      {active && (
                        <div className="absolute top-0 right-0 w-16 h-16 bg-white/10 rounded-bl-full" />
                      )}
                      <div
                        className={`flex justify-between items-start mb-3 ${
                          active ? "" : "text-primary-container"
                        }`}
                      >
                        <Icon name={iconForCode(t.code)} size={22} filled={active} />
                        {active && (
                          <Icon name="check_circle" size={20} className="text-secondary-fixed" />
                        )}
                      </div>
                      <h4 className="font-bold text-base leading-tight mb-0.5">{t.code}</h4>
                      <p
                        className={`text-xs ${
                          active ? "opacity-80" : "text-on-surface-variant"
                        } truncate`}
                      >
                        {t.name}
                      </p>
                    </button>
                  );
                })}
              </div>
            )}
          </section>

          {/* Step 3 */}
          {tests.length > 0 && (
            <section>
              <div className="flex justify-between items-end mb-5">
                <h3 className="text-2xl font-bold text-on-primary-fixed">Clinical Observations</h3>
              </div>
              <div className="w-full overflow-x-auto rounded-lg border border-outline-variant/15">
                <table className="w-full text-left border-collapse">
                  <thead className="bg-primary-container text-on-primary text-xs uppercase tracking-wider">
                    <tr>
                      <th className="p-3 px-4 font-semibold">Test Parameter</th>
                      <th className="p-3 px-4 font-semibold w-32">Observed Value</th>
                      <th className="p-3 px-4 font-semibold w-24">Unit</th>
                      <th className="p-3 px-4 font-semibold">Biological Ref. Range</th>
                      <th className="p-3 px-4 font-semibold w-24">Flag</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm text-on-surface">
                    {tests.map((t, i) => {
                      const val = results[t.id] ?? "";
                      const flag = flagFor(t, val);
                      return (
                        <tr
                          key={t.id}
                          className={i % 2 === 0 ? "bg-surface" : "bg-surface-container-low"}
                        >
                          <td className="p-3 px-4 font-medium">
                            {t.name}
                            {t.method && (
                              <div className="text-[11px] text-on-surface-variant">{t.method}</div>
                            )}
                          </td>
                          <td className="p-3 px-4">
                            <input
                              value={val}
                              onChange={(e) =>
                                setResults({ ...results, [t.id]: e.target.value })
                              }
                              className={
                                flag === "high" || flag === "low"
                                  ? "w-28 bg-error-container/20 border border-error/50 text-error px-2 py-1.5 rounded focus:border-error focus:ring-1 focus:ring-error outline-none font-mono text-right font-bold"
                                  : "w-28 bg-surface-container-highest border border-outline-variant/15 px-2 py-1.5 rounded focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none font-mono text-right"
                              }
                              placeholder="—"
                            />
                          </td>
                          <td className="p-3 px-4 text-on-surface-variant">{t.unit || "—"}</td>
                          <td className="p-3 px-4 text-on-surface-variant">{pickRange(t) || "—"}</td>
                          <td className="p-3 px-4">
                            {flag === "normal" && (
                              <span className="inline-flex bg-secondary-container text-on-secondary-container px-2 py-0.5 rounded text-xs border border-on-secondary-container/20">
                                Normal
                              </span>
                            )}
                            {flag === "high" && (
                              <span className="inline-flex items-center gap-1 bg-error-container text-on-error-container px-2 py-0.5 rounded text-xs font-bold border border-on-error-container/20">
                                <Icon name="arrow_upward" size={12} /> High
                              </span>
                            )}
                            {flag === "low" && (
                              <span className="inline-flex items-center gap-1 bg-tertiary-fixed text-on-tertiary-fixed px-2 py-0.5 rounded text-xs font-bold border border-on-tertiary-fixed/20">
                                <Icon name="arrow_downward" size={12} /> Low
                              </span>
                            )}
                            {flag == null && <span className="text-on-surface-variant">—</span>}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </section>
          )}

          {error && (
            <div className="mt-6 rounded-lg bg-error-container text-on-error-container px-4 py-3 text-sm flex items-center gap-2">
              <Icon name="error" size={16} />
              {error}
            </div>
          )}
        </div>
      </div>

      {/* Sticky bottom action bar */}
      <div className="fixed bottom-6 left-1/2 -translate-x-1/2 w-[94%] max-w-[820px] bg-surface-container-lowest/90 backdrop-blur-xl p-3 px-5 rounded-xl flex items-center justify-between shadow-[0_8px_32px_rgba(0,22,58,0.12)] z-40 border border-outline-variant/20">
        <div className="flex items-center gap-3 flex-1 min-w-0">
          <Icon name="stethoscope" size={20} className="text-primary-container opacity-60" />
          <div className="w-full max-w-[320px]">
            <label className="text-[10px] text-on-surface-variant uppercase tracking-wider font-bold block mb-1">
              Referred By
            </label>
            <DoctorAutocomplete
              value={referredBy}
              onChange={setReferredBy}
              doctors={doctors ?? []}
            />
          </div>
        </div>
        <div className="w-px h-8 bg-outline-variant/30 mx-3" />
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate("/reports")}
            className="px-4 py-2.5 text-sm font-medium text-on-surface-variant hover:bg-surface-container-low rounded-lg transition-colors"
          >
            Cancel
          </button>
          <button
            type="submit"
            disabled={submitting}
            className="bg-gradient-to-b from-primary-container to-primary text-on-primary px-5 py-2.5 rounded-lg font-bold text-sm shadow-md hover:opacity-95 transition-opacity flex items-center gap-2 whitespace-nowrap disabled:opacity-60"
          >
            {submitting ? "Generating…" : "Finalize & Generate PDF"}
            {!submitting && <Icon name="picture_as_pdf" size={16} />}
          </button>
        </div>
      </div>
    </form>
  );
}

function Step({ n, label, done }: { n: number; label: string; done: boolean }) {
  return (
    <div className="flex items-center gap-4 p-2">
      <div
        className={
          done
            ? "w-6 h-6 rounded-full bg-secondary text-on-secondary flex items-center justify-center text-xs font-bold shadow-sm"
            : "w-6 h-6 rounded-full bg-primary-container text-on-primary flex items-center justify-center text-xs font-bold shadow-sm"
        }
      >
        {done ? <Icon name="check" size={14} /> : n}
      </div>
      <span
        className={
          done
            ? "text-sm font-semibold text-on-surface"
            : "text-sm font-semibold text-primary-container"
        }
      >
        {label}
      </span>
    </div>
  );
}

function TextField({
  label,
  required,
  type = "text",
  value,
  onChange,
  placeholder,
}: {
  label: string;
  required?: boolean;
  type?: string;
  value: string;
  onChange: (v: string) => void;
  placeholder?: string;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">
        {label}
        {required && <span className="text-error"> *</span>}
      </label>
      <input
        type={type}
        value={value}
        required={required}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="bg-surface-container-highest border border-outline-variant/15 text-on-surface p-3 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all text-sm"
      />
    </div>
  );
}

function PatientSearch({ onPick }: { onPick: (p: Patient) => void }) {
  const [q, setQ] = useState("");
  const [debounced, setDebounced] = useState("");
  const [open, setOpen] = useState(false);
  const wrapRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const t = setTimeout(() => setDebounced(q.trim()), 250);
    return () => clearTimeout(t);
  }, [q]);

  const { data: patients, isFetching } = useQuery({
    queryKey: ["patients-search", debounced],
    queryFn: () => listPatients(debounced),
    enabled: open,
  });

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current) return;
      if (!wrapRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  const results = (patients ?? []).slice(0, 8);

  return (
    <div className="relative" ref={wrapRef}>
      <label className="text-xs text-on-surface-variant font-medium uppercase tracking-wider block mb-2">
        Search Existing Patient
      </label>
      <div className="relative">
        <Icon
          name="search"
          size={18}
          className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
        />
        <input
          value={q}
          onChange={(e) => {
            setQ(e.target.value);
            setOpen(true);
          }}
          onFocus={() => setOpen(true)}
          placeholder="Search by name or phone…"
          className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-3 pl-10 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all text-sm"
          autoComplete="off"
        />
      </div>
      {open && (
        <ul className="absolute top-full left-0 right-0 mt-1 z-40 bg-surface-container-lowest border border-outline-variant/30 rounded-md shadow-lg max-h-72 overflow-auto py-1 text-sm">
          {isFetching && (
            <li className="px-3 py-2 text-on-surface-variant text-xs">Searching…</li>
          )}
          {!isFetching && results.length === 0 && (
            <li className="px-3 py-2 text-on-surface-variant text-xs">
              {debounced ? "No patients found." : "Start typing to search…"}
            </li>
          )}
          {results.map((p) => (
            <li
              key={p.id}
              onMouseDown={(e) => {
                e.preventDefault();
                onPick(p);
                setQ(p.name);
                setOpen(false);
              }}
              className="px-3 py-2 cursor-pointer text-on-surface hover:bg-primary-container/20"
            >
              <div className="font-medium">{p.name}</div>
              <div className="text-[11px] text-on-surface-variant">
                {[
                  p.patient_code,
                  p.sex_display,
                  p.age != null ? `${p.age} ${p.age_unit}` : null,
                  p.phone,
                  p.city,
                ]
                  .filter(Boolean)
                  .join(" · ")}
              </div>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function DoctorAutocomplete({
  value,
  onChange,
  doctors,
}: {
  value: string;
  onChange: (v: string) => void;
  doctors: ReferringDoctor[];
}) {
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState(0);
  const wrapRef = useRef<HTMLDivElement>(null);

  const suggestions = useMemo(() => {
    const q = value.trim().toLowerCase();
    const pool = doctors.filter((d) => d.name);
    if (!q) return pool.slice(0, 8);
    return pool
      .filter((d) => d.name.toLowerCase().includes(q))
      .slice(0, 8);
  }, [value, doctors]);

  useEffect(() => {
    function onDocClick(e: MouseEvent) {
      if (!wrapRef.current) return;
      if (!wrapRef.current.contains(e.target as Node)) setOpen(false);
    }
    document.addEventListener("mousedown", onDocClick);
    return () => document.removeEventListener("mousedown", onDocClick);
  }, []);

  function pick(name: string) {
    onChange(name);
    setOpen(false);
  }

  return (
    <div className="relative" ref={wrapRef}>
      <input
        value={value}
        onChange={(e) => {
          onChange(e.target.value);
          setOpen(true);
          setHighlight(0);
        }}
        onFocus={() => setOpen(true)}
        onKeyDown={(e) => {
          if (!open) return;
          if (e.key === "ArrowDown") {
            e.preventDefault();
            setHighlight((h) => Math.min(h + 1, suggestions.length - 1));
          } else if (e.key === "ArrowUp") {
            e.preventDefault();
            setHighlight((h) => Math.max(h - 1, 0));
          } else if (e.key === "Enter" && suggestions[highlight]) {
            e.preventDefault();
            pick(suggestions[highlight].name);
          } else if (e.key === "Escape") {
            setOpen(false);
          }
        }}
        placeholder="Dr. Name (Optional)"
        className="w-full bg-surface-container-highest border border-outline-variant/30 text-sm text-on-surface px-2.5 py-1.5 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all placeholder:text-on-surface-variant/50"
        autoComplete="off"
      />
      {open && suggestions.length > 0 && (
        <ul className="absolute bottom-full left-0 right-0 mb-1 z-50 bg-surface-container-lowest border border-outline-variant/30 rounded-md shadow-lg max-h-56 overflow-auto py-1 text-sm">
          {suggestions.map((d, i) => (
            <li
              key={d.id}
              onMouseDown={(e) => {
                e.preventDefault();
                pick(d.name);
              }}
              onMouseEnter={() => setHighlight(i)}
              className={
                (i === highlight
                  ? "bg-primary-container/20 "
                  : "") +
                "px-3 py-1.5 cursor-pointer text-on-surface"
              }
            >
              <div className="font-medium">{d.name}</div>
              {(d.qualification || d.specialty) && (
                <div className="text-[11px] text-on-surface-variant">
                  {[d.qualification, d.specialty].filter(Boolean).join(" · ")}
                </div>
              )}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}

function SelectField({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  options: { value: string; label: string }[];
}) {
  return (
    <div className="flex flex-col gap-2">
      <label className="text-xs text-on-surface-variant font-medium uppercase tracking-wider">
        {label}
      </label>
      <div className="relative">
        <select
          value={value}
          onChange={(e) => onChange(e.target.value)}
          className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-3 pr-10 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all text-sm appearance-none"
        >
          {options.map((o) => (
            <option key={o.value} value={o.value}>
              {o.label}
            </option>
          ))}
        </select>
        <Icon
          name="expand_more"
          size={18}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
        />
      </div>
    </div>
  );
}
