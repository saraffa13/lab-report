import { Link, useNavigate, useParams } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/api/client";
import {
  deleteReport,
  downloadPdf,
  updateReportPayment,
  type ReportDetail,
} from "@/api/reports";
import { useEffect, useState } from "react";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/hooks/useAuth";

const CAN_DELETE_ROLES = new Set(["admin", "lab_owner"]);

const STATUS_STYLES: Record<string, string> = {
  final: "bg-secondary-container text-on-secondary-container ring-on-secondary-container/20",
  draft: "bg-surface-container-highest text-on-surface-variant ring-outline-variant/50",
  pending: "bg-tertiary-fixed text-on-tertiary-fixed ring-on-tertiary-fixed/20",
  cancelled: "bg-error-container text-on-error-container ring-on-error-container/20",
};

export default function ReportDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canDelete =
    !!user && (user.is_superuser || (user.role_code && CAN_DELETE_ROLES.has(user.role_code)));

  const { data: report, isLoading } = useQuery({
    queryKey: ["report", id],
    queryFn: async () => (await apiClient.get<ReportDetail>(`/v1/reports/${id}/`)).data,
  });
  const [pdfUrl, setPdfUrl] = useState<string | null>(null);
  const [priceInput, setPriceInput] = useState<string>("");
  const [savingPay, setSavingPay] = useState(false);
  const [payError, setPayError] = useState<string | null>(null);

  useEffect(() => {
    if (report?.total_amount != null) setPriceInput(String(report.total_amount));
  }, [report?.total_amount]);

  async function savePayment(markPaid: boolean) {
    if (!id) return;
    setPayError(null);
    setSavingPay(true);
    try {
      const amt = priceInput.trim() ? Number(priceInput) : null;
      if (priceInput.trim() && !Number.isFinite(amt as number)) {
        setPayError("Enter a valid amount.");
        return;
      }
      await updateReportPayment(id, {
        total_amount: amt,
        ...(markPaid ? { payment_status: "paid" as const } : {}),
      });
      await queryClient.invalidateQueries({ queryKey: ["report", id] });
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      await queryClient.invalidateQueries({ queryKey: ["dashboard"] });
    } catch (e: unknown) {
      const err = e as { response?: { data?: { detail?: string } } };
      setPayError(err.response?.data?.detail ?? "Failed to update payment.");
    } finally {
      setSavingPay(false);
    }
  }

  async function handleDelete() {
    if (!id) return;
    if (!window.confirm("Delete this report? This cannot be undone.")) return;
    try {
      await deleteReport(id);
      await queryClient.invalidateQueries({ queryKey: ["reports"] });
      navigate("/reports", { replace: true });
    } catch {
      alert("Failed to delete report.");
    }
  }

  useEffect(() => {
    if (!id) return;
    let revoked = false;
    let currentUrl: string | null = null;
    apiClient.get(`/v1/reports/${id}/pdf/`, { responseType: "blob" }).then((resp) => {
      const blob = new Blob([resp.data], { type: "application/pdf" });
      currentUrl = URL.createObjectURL(blob);
      if (!revoked) setPdfUrl(currentUrl);
    });
    return () => {
      revoked = true;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [id]);

  if (isLoading || !report) {
    return <p className="text-on-surface-variant text-sm">Loading report…</p>;
  }

  const statusClass =
    STATUS_STYLES[report.status.toLowerCase()] ?? STATUS_STYLES.final;

  const abnormal = report.results.filter((r) => r.is_abnormal).length;

  return (
    <div className="flex flex-col gap-8">
      {/* Header */}
      <section className="flex flex-col md:flex-row justify-between items-start md:items-end gap-4 pb-2">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <span className="text-xs font-semibold text-on-surface-variant tracking-wider uppercase">
              Accession #
            </span>
            <span className="font-bold text-lg text-on-primary-fixed font-mono">
              {report.accession_number}
            </span>
            <span
              className={`inline-flex items-center gap-1 text-xs font-semibold px-2.5 py-0.5 rounded-full ring-1 ${statusClass}`}
            >
              <Icon name="check_circle" size={14} />
              {report.status}
            </span>
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-on-primary-fixed tracking-tight">
            {report.template_name ?? report.package_name ?? "Ad-hoc Report"}
          </h1>
          <p className="text-on-surface-variant mt-2">
            Patient: <span className="font-semibold text-on-surface">{report.patient_name}</span>
            {" • "}
            Created:{" "}
            <span className="font-medium text-on-surface">
              {new Date(report.created_at).toLocaleString()}
            </span>
          </p>
        </div>
        <div className="flex gap-3">
          <Link
            to="/reports"
            className="bg-surface-container-high text-primary-container font-medium text-sm px-4 py-2 rounded-md hover:bg-surface-container-highest transition-colors flex items-center gap-2"
          >
            <Icon name="arrow_back" size={16} />
            Back
          </Link>
          <button
            onClick={() => downloadPdf(report.id, report.suggested_filename)}
            className="bg-gradient-to-b from-primary-container to-primary text-on-primary font-medium text-sm px-5 py-2 rounded-md hover:opacity-95 transition-opacity flex items-center gap-2 shadow-[0_4px_12px_rgba(11,42,91,0.2)]"
          >
            <Icon name="download" size={16} />
            Download PDF
          </button>
          {canDelete && (
            <button
              onClick={handleDelete}
              className="bg-error-container text-on-error-container font-medium text-sm px-4 py-2 rounded-md hover:opacity-90 transition-opacity flex items-center gap-2"
            >
              <Icon name="delete" size={16} />
              Delete
            </button>
          )}
        </div>
      </section>

      {/* Main grid */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left column */}
        <div className="lg:col-span-4 flex flex-col gap-6">
          <div className="bg-surface-container-lowest rounded-xl p-6 ring-1 ring-outline-variant/15 shadow-dossier">
            <h2 className="text-xs font-bold text-on-primary-fixed uppercase tracking-wider mb-5 flex items-center gap-2">
              <Icon name="person" size={16} className="text-primary-container" />
              Patient Demographics
            </h2>
            <div className="flex flex-col gap-3">
              <DossierRow label="Name" value={report.patient_name} strong />
              <DossierRow label="Patient ID" value={report.patient?.slice(0, 12) ?? "—"} mono />
              <DossierRow label="Accession #" value={report.accession_number} mono />
              <DossierRow
                label="Barcode"
                value={report.barcode_number || "—"}
                mono
              />
              <DossierRow
                label="Referring Dr."
                value={report.referred_by_text || "Self"}
              />
              <DossierRow
                label="Signed At"
                value={
                  report.signed_at
                    ? new Date(report.signed_at).toLocaleString()
                    : "—"
                }
              />
            </div>
          </div>

          {report.clinical_history && (
            <div className="bg-surface-container-lowest rounded-xl p-6 ring-1 ring-outline-variant/15 shadow-dossier relative overflow-hidden">
              <div className="absolute top-0 left-0 w-1 h-full bg-secondary" />
              <h2 className="text-xs font-bold text-on-primary-fixed uppercase tracking-wider mb-3 flex items-center gap-2">
                <Icon name="medical_information" size={16} className="text-secondary" />
                Clinical Notes
              </h2>
              <p className="text-sm text-on-surface-variant leading-relaxed">
                {report.clinical_history}
              </p>
            </div>
          )}

          <div className="bg-surface-container-lowest rounded-xl p-6 ring-1 ring-outline-variant/15 shadow-dossier">
            <h2 className="text-xs font-bold text-on-primary-fixed uppercase tracking-wider mb-4 flex items-center gap-2">
              <Icon name="payments" size={16} className="text-primary-container" />
              Billing
            </h2>
            <div className="flex flex-col gap-3">
              <div className="flex items-center justify-between">
                <span className="text-xs text-on-surface-variant uppercase tracking-wider">
                  Status
                </span>
                <PaymentBadge status={report.payment_status} />
              </div>
              <label className="flex flex-col gap-1">
                <span className="text-xs text-on-surface-variant uppercase tracking-wider">
                  Price (₹)
                </span>
                <input
                  type="number"
                  inputMode="decimal"
                  value={priceInput}
                  onChange={(e) => setPriceInput(e.target.value)}
                  placeholder="0.00"
                  className="bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none text-sm"
                />
              </label>
              {report.paid_at && (
                <div className="text-[11px] text-on-surface-variant">
                  Paid on {new Date(report.paid_at).toLocaleString()}
                </div>
              )}
              {payError && (
                <div className="text-xs text-error">{payError}</div>
              )}
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => savePayment(false)}
                  disabled={savingPay}
                  className="flex-1 bg-surface-container-high text-primary-container text-sm font-medium px-3 py-2 rounded-md hover:bg-surface-container-highest transition-colors disabled:opacity-60"
                >
                  Save Price
                </button>
                <button
                  type="button"
                  onClick={() => savePayment(true)}
                  disabled={savingPay || report.payment_status === "paid"}
                  className="flex-1 bg-gradient-to-b from-primary-container to-primary text-on-primary text-sm font-bold px-3 py-2 rounded-md hover:opacity-95 transition-opacity disabled:opacity-60 flex items-center justify-center gap-1"
                >
                  <Icon name="check_circle" size={14} />
                  {report.payment_status === "paid" ? "Paid" : "Mark Paid"}
                </button>
              </div>
            </div>
          </div>

          <div className="bg-surface-container-low rounded-xl p-6 ring-1 ring-outline-variant/10">
            <h2 className="text-xs font-bold text-on-primary-fixed uppercase tracking-wider mb-4 flex items-center gap-2">
              <Icon name="analytics" size={16} className="text-primary-container" />
              Summary
            </h2>
            <div className="grid grid-cols-2 gap-3">
              <SummaryStat label="Tests" value={report.results.length} />
              <SummaryStat
                label="Abnormal"
                value={abnormal}
                tone={abnormal > 0 ? "error" : "normal"}
              />
            </div>
          </div>
        </div>

        {/* Right column */}
        <div className="lg:col-span-8 flex flex-col gap-6">
          <div className="bg-surface-container-lowest rounded-xl ring-1 ring-outline-variant/15 overflow-hidden shadow-dossier">
            <div className="bg-primary-container px-6 py-4 flex items-center justify-between">
              <h3 className="text-base font-bold text-on-primary tracking-wide">
                Results Ledger
              </h3>
              <span className="text-xs text-primary-fixed-dim">
                {report.results.length} observations
              </span>
            </div>
            <div className="w-full overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="bg-surface-container-low text-on-surface-variant text-xs uppercase tracking-wider">
                    <th className="py-3 px-5 font-semibold">Test Description</th>
                    <th className="py-3 px-5 font-semibold">Result</th>
                    <th className="py-3 px-5 font-semibold">Units</th>
                    <th className="py-3 px-5 font-semibold">Reference Range</th>
                    <th className="py-3 px-5 font-semibold text-right">Flag</th>
                  </tr>
                </thead>
                <tbody className="text-sm">
                  {report.results.map((r, i) => (
                    <tr
                      key={r.id}
                      className={`${
                        i % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                      } hover:bg-surface-container-highest transition-colors`}
                    >
                      <td className="py-2.5 px-5 font-medium text-on-surface">
                        {r.test_name}
                        {r.test_category && (
                          <div className="text-[11px] text-on-surface-variant">
                            {r.test_category}
                          </div>
                        )}
                      </td>
                      <td
                        className={`py-2.5 px-5 font-bold font-mono ${
                          r.is_abnormal ? "text-error" : "text-on-surface"
                        }`}
                      >
                        {r.result_value}
                      </td>
                      <td className="py-2.5 px-5 text-on-surface-variant">
                        {r.unit_used || "—"}
                      </td>
                      <td className="py-2.5 px-5 text-on-surface-variant">
                        {r.reference_range_used || "—"}
                      </td>
                      <td className="py-2.5 px-5 text-right">
                        <FlagBadge flag={r.flag} />
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* PDF preview */}
          <div className="bg-surface-container-lowest rounded-xl ring-1 ring-outline-variant/15 shadow-dossier overflow-hidden flex flex-col">
            <div className="bg-surface-container-low px-4 py-3 flex justify-between items-center border-b border-outline-variant/15">
              <span className="text-sm font-semibold text-on-surface-variant flex items-center gap-2">
                <Icon name="picture_as_pdf" size={18} />
                {report.accession_number}.pdf
              </span>
              <div className="flex gap-2">
                {pdfUrl && (
                  <a
                    href={pdfUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="p-1.5 text-on-surface-variant hover:bg-surface-container-highest rounded transition-colors"
                    title="Open in new tab"
                  >
                    <Icon name="open_in_new" size={16} />
                  </a>
                )}
                <button
                  onClick={() =>
                    downloadPdf(report.id, report.suggested_filename)
                  }
                  className="p-1.5 text-on-surface-variant hover:bg-surface-container-highest rounded transition-colors"
                  title="Download"
                >
                  <Icon name="download" size={16} />
                </button>
              </div>
            </div>
            <div className="bg-surface-variant/30 h-[600px]">
              {pdfUrl ? (
                <iframe src={pdfUrl} title="Report PDF" className="w-full h-full" />
              ) : (
                <div className="h-full flex items-center justify-center flex-col gap-2">
                  <Icon name="hourglass_empty" size={28} className="text-outline" />
                  <p className="text-outline text-sm">Loading PDF preview…</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

function DossierRow({
  label,
  value,
  strong,
  mono,
}: {
  label: string;
  value: string;
  strong?: boolean;
  mono?: boolean;
}) {
  return (
    <div className="flex justify-between items-baseline gap-3">
      <span className="text-xs text-on-surface-variant">{label}</span>
      <span
        className={`text-sm ${strong ? "font-semibold" : "font-medium"} ${
          mono ? "font-mono" : ""
        } text-on-surface text-right truncate`}
      >
        {value}
      </span>
    </div>
  );
}

function SummaryStat({
  label,
  value,
  tone = "normal",
}: {
  label: string;
  value: number;
  tone?: "normal" | "error";
}) {
  return (
    <div className="bg-surface-container-lowest rounded-lg p-3 ring-1 ring-outline-variant/10">
      <div className="text-xs text-on-surface-variant">{label}</div>
      <div
        className={`text-2xl font-bold font-mono ${
          tone === "error" ? "text-error" : "text-on-primary-fixed"
        }`}
      >
        {value}
      </div>
    </div>
  );
}

function PaymentBadge({ status }: { status: ReportDetail["payment_status"] }) {
  if (status === "paid") {
    return (
      <span className="inline-flex items-center gap-1 bg-secondary-container text-on-secondary-container text-[11px] font-bold px-2 py-0.5 rounded ring-1 ring-on-secondary-container/20">
        <Icon name="check_circle" size={12} /> Paid
      </span>
    );
  }
  if (status === "partial") {
    return (
      <span className="inline-flex items-center gap-1 bg-tertiary-fixed text-on-tertiary-fixed text-[11px] font-bold px-2 py-0.5 rounded">
        Partial
      </span>
    );
  }
  return (
    <span className="inline-flex items-center gap-1 bg-surface-container-highest text-on-surface-variant text-[11px] font-bold px-2 py-0.5 rounded ring-1 ring-outline-variant/30">
      Pending
    </span>
  );
}

function FlagBadge({ flag }: { flag: string }) {
  if (!flag || flag === "normal") return <span className="text-on-surface-variant">—</span>;
  if (flag === "high" || flag === "critical_high") {
    return (
      <span className="inline-flex items-center gap-1 bg-error-container text-on-error-container text-[11px] font-bold px-2 py-0.5 rounded ring-1 ring-on-error-container/20">
        <Icon name={flag === "critical_high" ? "warning" : "arrow_upward"} size={12} />
        {flag === "critical_high" ? "CRITICAL" : "HIGH"}
      </span>
    );
  }
  if (flag === "low" || flag === "critical_low") {
    return (
      <span className="inline-flex items-center gap-1 bg-tertiary-fixed text-on-tertiary-fixed text-[11px] font-bold px-2 py-0.5 rounded ring-1 ring-on-tertiary-fixed/20">
        <Icon name={flag === "critical_low" ? "warning" : "arrow_downward"} size={12} />
        {flag === "critical_low" ? "CRITICAL" : "LOW"}
      </span>
    );
  }
  return (
    <span className="inline-flex bg-surface-container-highest text-on-surface-variant text-[11px] font-bold px-2 py-0.5 rounded ring-1 ring-outline-variant/30 uppercase">
      {flag}
    </span>
  );
}
