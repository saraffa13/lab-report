import { Link, useParams } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { createPatientLogin, exportPatientData, getPatient, getPatientReports } from "@/api/patients";
import { downloadPdf, type ReportListItem } from "@/api/reports";
import { Icon } from "@/components/ui/Icon";
import { PaymentCell } from "@/components/PaymentCell";
import { useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useAuth } from "@/hooks/useAuth";

const USER_MANAGE_ROLES = new Set(["admin", "lab_owner"]);

type Tab = "reports" | "consents" | "export";

const STATUS_STYLES: Record<string, string> = {
  final: "bg-secondary-container text-on-secondary-container ring-on-secondary-container/20",
  draft: "bg-surface-container-highest text-on-surface-variant ring-outline-variant/50",
  pending: "bg-tertiary-fixed text-on-tertiary-fixed ring-on-tertiary-fixed/20",
  cancelled: "bg-error-container text-on-error-container ring-on-error-container/20",
};

export default function PatientDetailPage() {
  const { id } = useParams<{ id: string }>();
  const [tab, setTab] = useState<Tab>("reports");
  const queryClient = useQueryClient();
  const { user: me } = useAuth();
  const canManageUsers =
    !!me && (me.is_superuser || (me.role_code && USER_MANAGE_ROLES.has(me.role_code)));
  const [loginResult, setLoginResult] = useState<{ phone: string; password: string } | null>(null);
  const [loginBusy, setLoginBusy] = useState(false);
  const { data: patient } = useQuery({
    queryKey: ["patient", id],
    queryFn: () => getPatient(id!),
  });
  const { data: reports } = useQuery({
    queryKey: ["patient-reports", id],
    queryFn: () => getPatientReports(id!) as Promise<ReportListItem[]>,
  });

  if (!patient) {
    return <p className="text-on-surface-variant text-sm">Loading patient…</p>;
  }

  const initials = patient.name
    .split(/\s+/)
    .map((x) => x[0])
    .filter(Boolean)
    .slice(0, 2)
    .join("")
    .toUpperCase();

  async function handleCreateLogin() {
    if (!patient) return;
    if (!patient.phone) {
      alert("Add a phone number to this patient before creating a login.");
      return;
    }
    setLoginBusy(true);
    try {
      const res = await createPatientLogin(patient.id);
      setLoginResult({ phone: res.phone, password: res.password });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      alert(err.response?.data?.detail ?? "Failed to create patient login.");
    } finally {
      setLoginBusy(false);
    }
  }

  async function handleExport() {
    if (!patient) return;
    const blob = await exportPatientData(patient.id);
    const json = JSON.stringify(blob, null, 2);
    const url = URL.createObjectURL(new Blob([json], { type: "application/json" }));
    const a = document.createElement("a");
    a.href = url;
    a.download = `${patient.patient_code}-export.json`;
    a.click();
    URL.revokeObjectURL(url);
  }

  return (
    <div className="flex flex-col gap-8">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
        <div>
          <div className="flex items-center gap-2 text-on-surface-variant mb-2">
            <Link to="/patients" className="hover:text-primary-container text-sm font-medium">
              Patients
            </Link>
            <Icon name="chevron_right" size={16} />
            <span className="text-sm font-medium text-on-surface font-mono">
              {patient.patient_code}
            </span>
          </div>
          <h1 className="text-3xl font-bold text-on-primary-fixed tracking-tight">
            {patient.name}
          </h1>
        </div>
        <div className="flex gap-3 flex-wrap">
          <Link
            to={`/reports/new?patient=${patient.id}`}
            className="px-4 py-2 bg-surface-container-high text-primary-container rounded-md text-sm font-medium hover:bg-surface-container-highest transition-colors flex items-center gap-2"
          >
            <Icon name="add" size={16} />
            New Report
          </Link>
          {canManageUsers && (
            <button
              onClick={handleCreateLogin}
              disabled={loginBusy}
              className="px-4 py-2 bg-surface-container-high text-primary-container rounded-md text-sm font-medium hover:bg-surface-container-highest transition-colors flex items-center gap-2 disabled:opacity-60"
            >
              <Icon name="lock_reset" size={16} />
              {loginBusy ? "Working…" : "Create Patient Login"}
            </button>
          )}
          <button
            onClick={handleExport}
            className="px-5 py-2 bg-gradient-to-b from-primary-container to-primary text-on-primary rounded-md text-sm font-medium hover:opacity-95 transition-opacity flex items-center gap-2 shadow-[0_4px_12px_rgba(11,42,91,0.2)]"
          >
            <Icon name="download" size={16} />
            Export Data
          </button>
        </div>
      </div>

      {loginResult && (
        <div className="bg-secondary-container text-on-secondary-container rounded-xl p-4 ring-1 ring-on-secondary-container/20 flex items-start gap-3">
          <Icon name="check_circle" size={20} className="mt-0.5" />
          <div className="flex-1 min-w-0">
            <div className="font-semibold text-sm mb-1">Patient login ready</div>
            <div className="text-sm">
              Phone: <code className="font-mono">{loginResult.phone}</code>
              {" · "}
              Password:{" "}
              <code className="font-mono bg-surface-container-lowest px-1.5 py-0.5 rounded">
                {loginResult.password}
              </code>
            </div>
            <div className="text-xs mt-1 opacity-80">
              Share this with the patient. Save it now — it won't be shown again.
            </div>
          </div>
          <button
            onClick={() => setLoginResult(null)}
            className="p-1 rounded hover:bg-surface-container-lowest/40"
          >
            <Icon name="close" size={16} />
          </button>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Left column */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 overflow-hidden">
            <div className="p-6 flex items-center gap-4">
              <div className="w-16 h-16 rounded-full bg-surface-container-low flex items-center justify-center text-primary-container font-bold text-xl border-2 border-surface-container-lowest shadow-sm">
                {initials}
              </div>
              <div className="min-w-0">
                <h2 className="text-lg font-bold text-on-surface truncate">{patient.name}</h2>
                <p className="text-sm text-on-surface-variant mt-0.5 flex items-center gap-1">
                  <Icon name="cake" size={14} />
                  {patient.age ? `${patient.age} ${patient.age_unit}` : "Age N/A"} (
                  {patient.sex_display})
                </p>
              </div>
            </div>
            <div className="px-6 pb-6 grid grid-cols-2 gap-x-3 gap-y-4">
              <DossierField label="Patient ID" value={patient.patient_code} mono />
              <DossierField label="Blood Group" value={patient.blood_group || "—"} />
              <DossierField label="Phone" value={patient.phone || "—"} />
              <DossierField label="Alt. Phone" value={patient.alternate_phone || "—"} />
              <DossierField label="Email" value={patient.email || "—"} className="col-span-2" />
              <DossierField
                label="Address"
                value={
                  [patient.address, patient.city, patient.state, patient.pincode]
                    .filter(Boolean)
                    .join(", ") || "—"
                }
                className="col-span-2"
              />
            </div>
            {(patient.emergency_contact_name || patient.emergency_contact_phone) && (
              <div className="bg-surface-container-low p-6 border-t border-outline-variant/10">
                <span className="text-xs text-on-surface-variant uppercase tracking-wider font-semibold block mb-2">
                  Emergency Contact
                </span>
                <div className="flex items-center gap-3">
                  <Icon name="emergency_heat" size={18} className="text-error" />
                  <span className="text-sm font-semibold text-on-surface">
                    {patient.emergency_contact_name || "—"}
                    {patient.emergency_contact_phone && (
                      <span className="text-on-surface-variant font-normal">
                        {" · "}
                        {patient.emergency_contact_phone}
                      </span>
                    )}
                  </span>
                </div>
              </div>
            )}
          </div>

          {patient.notes && (
            <div className="bg-surface-container-lowest rounded-xl p-6 ring-1 ring-outline-variant/15 shadow-dossier relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-secondary" />
              <h3 className="text-xs font-bold text-on-primary-fixed uppercase tracking-wider mb-3 flex items-center gap-2">
                <Icon name="sticky_note_2" size={16} className="text-secondary" />
                Notes
              </h3>
              <p className="text-sm text-on-surface-variant leading-relaxed whitespace-pre-wrap">
                {patient.notes}
              </p>
            </div>
          )}
        </div>

        {/* Right column */}
        <div className="lg:col-span-8 flex flex-col gap-5">
          <div className="flex border-b border-surface-container-high">
            <TabButton label="Reports" active={tab === "reports"} onClick={() => setTab("reports")} />
            <TabButton
              label="Consents"
              active={tab === "consents"}
              onClick={() => setTab("consents")}
            />
            <TabButton
              label="Export"
              active={tab === "export"}
              onClick={() => setTab("export")}
            />
          </div>

          {tab === "reports" && (
            <div className="bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 overflow-hidden">
              <div className="bg-primary-container px-6 py-4 flex justify-between items-center">
                <h3 className="text-on-primary font-bold text-base tracking-tight">
                  Diagnostic Ledger
                </h3>
                <span className="text-xs text-primary-fixed-dim">
                  {reports?.length ?? 0} reports
                </span>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="bg-surface-container-low text-on-surface-variant text-xs uppercase tracking-wider">
                      <th className="px-6 py-3 font-semibold">Date</th>
                      <th className="px-6 py-3 font-semibold">Accession #</th>
                      <th className="px-6 py-3 font-semibold">Template</th>
                      <th className="px-6 py-3 font-semibold">Status</th>
                      <th className="px-6 py-3 font-semibold text-right">Payment</th>
                      <th className="px-6 py-3 font-semibold text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {!reports && (
                      <tr>
                        <td colSpan={6} className="px-6 py-10 text-center text-on-surface-variant">
                          Loading reports…
                        </td>
                      </tr>
                    )}
                    {reports?.length === 0 && (
                      <tr>
                        <td colSpan={6} className="px-6 py-10 text-center">
                          <Icon
                            name="description"
                            size={32}
                            className="text-outline-variant mb-2 block mx-auto"
                          />
                          <div className="text-on-surface-variant text-sm">
                            No reports yet.{" "}
                            <Link
                              to={`/reports/new?patient=${patient.id}`}
                              className="text-primary-container font-medium hover:underline"
                            >
                              Create one →
                            </Link>
                          </div>
                        </td>
                      </tr>
                    )}
                    {reports?.map((r, i) => {
                      const styles =
                        STATUS_STYLES[r.status.toLowerCase()] ?? STATUS_STYLES.final;
                      return (
                        <tr
                          key={r.id}
                          className={`${
                            i % 2 === 0 ? "bg-surface" : "bg-surface-container-low/60"
                          } hover:bg-surface-container-high transition-colors group`}
                        >
                          <td className="px-6 py-3.5 font-medium text-on-surface whitespace-nowrap">
                            {new Date(r.created_at).toLocaleDateString(undefined, {
                              day: "2-digit",
                              month: "short",
                              year: "numeric",
                            })}
                          </td>
                          <td className="px-6 py-3.5 text-on-surface-variant font-mono">
                            <Link to={`/reports/${r.id}`} className="hover:underline">
                              {r.accession_number}
                            </Link>
                          </td>
                          <td className="px-6 py-3.5 font-medium text-on-surface">
                            {r.template_name ?? "—"}
                          </td>
                          <td className="px-6 py-3.5">
                            <span
                              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-xs font-semibold ring-1 ${styles}`}
                            >
                              <Icon
                                name={r.status === "final" ? "check_circle" : "hourglass_empty"}
                                size={12}
                              />
                              {r.status}
                            </span>
                          </td>
                          <td className="px-6 py-3.5 text-right">
                            <PaymentCell
                              report={r}
                              onChanged={() => {
                                queryClient.invalidateQueries({
                                  queryKey: ["patient-reports", id],
                                });
                                queryClient.invalidateQueries({ queryKey: ["reports"] });
                                queryClient.invalidateQueries({ queryKey: ["dashboard"] });
                              }}
                            />
                          </td>
                          <td className="px-6 py-3.5 text-right">
                            <div className="flex justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                              <Link
                                to={`/reports/${r.id}`}
                                className="p-1.5 text-primary-container hover:bg-surface-container-high rounded-md transition-colors"
                                title="View"
                              >
                                <Icon name="visibility" size={18} />
                              </Link>
                              <button
                                onClick={() =>
                                  downloadPdf(r.id, r.suggested_filename)
                                }
                                className="p-1.5 text-primary-container hover:bg-surface-container-high rounded-md transition-colors"
                                title="Download"
                              >
                                <Icon name="download" size={18} />
                              </button>
                            </div>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {tab === "consents" && (
            <div className="bg-surface-container-lowest rounded-xl p-10 ring-1 ring-outline-variant/15 shadow-dossier text-center">
              <Icon
                name="assignment_turned_in"
                size={36}
                className="text-outline-variant mb-2 block mx-auto"
              />
              <h3 className="text-on-primary-fixed font-semibold mb-1">
                Consent records
              </h3>
              <p className="text-on-surface-variant text-sm">
                Patient consent tracking will appear here.
              </p>
            </div>
          )}

          {tab === "export" && (
            <div className="bg-surface-container-lowest rounded-xl p-8 ring-1 ring-outline-variant/15 shadow-dossier">
              <h3 className="text-on-primary-fixed font-bold mb-2 flex items-center gap-2">
                <Icon name="policy" size={18} className="text-primary-container" />
                DPDP Act Data Export
              </h3>
              <p className="text-on-surface-variant text-sm mb-6">
                Download a machine-readable dump of this patient's profile, reports, and
                results. Provided for compliance with the Digital Personal Data Protection Act.
              </p>
              <button
                onClick={handleExport}
                className="bg-gradient-to-b from-primary-container to-primary text-on-primary px-5 py-2.5 rounded-md font-medium text-sm hover:opacity-95 transition-opacity flex items-center gap-2 shadow-md"
              >
                <Icon name="file_download" size={16} />
                Export JSON
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function DossierField({
  label,
  value,
  mono,
  className = "",
}: {
  label: string;
  value: string;
  mono?: boolean;
  className?: string;
}) {
  return (
    <div className={className}>
      <span className="text-[11px] text-on-surface-variant uppercase tracking-wider font-semibold block mb-1">
        {label}
      </span>
      <span
        className={`text-sm font-medium text-on-surface block leading-tight ${
          mono ? "font-mono" : ""
        }`}
      >
        {value}
      </span>
    </div>
  );
}

function TabButton({
  label,
  active,
  onClick,
}: {
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
          ? "px-6 py-3 text-sm font-bold text-primary-container border-b-2 border-primary-container bg-surface-container-lowest/50"
          : "px-6 py-3 text-sm font-medium text-on-surface-variant hover:text-primary-container hover:bg-surface-container-low transition-colors"
      }
    >
      {label}
    </button>
  );
}
