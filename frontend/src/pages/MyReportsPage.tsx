import { useQuery } from "@tanstack/react-query";
import { listMyReports, downloadMyReportPdf, openMyReportPdf } from "@/api/reports";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/hooks/useAuth";

const STATUS_BADGE: Record<string, string> = {
  final: "bg-secondary-container text-on-secondary-container ring-on-secondary-container/20",
  draft: "bg-tertiary-fixed text-on-tertiary-fixed ring-on-tertiary-fixed/20",
  pending: "bg-tertiary-fixed text-on-tertiary-fixed ring-on-tertiary-fixed/20",
  cancelled: "bg-surface-container-high text-on-surface-variant ring-outline-variant/30",
};

export default function MyReportsPage() {
  const { user } = useAuth();
  const { data, isLoading } = useQuery({
    queryKey: ["my-reports"],
    queryFn: listMyReports,
  });

  return (
    <div className="flex flex-col gap-6 max-w-5xl mx-auto">
      <header>
        <h1 className="text-3xl font-extrabold text-on-primary-fixed tracking-tight">
          My Reports
        </h1>
        <p className="text-sm text-on-surface-variant mt-1">
          All reports linked to the phone number {user?.phone || "on this account"}.
        </p>
      </header>

      <div className="bg-surface-container-lowest rounded-xl ring-1 ring-outline-variant/15 shadow-dossier overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="text-xs text-on-surface-variant uppercase tracking-wider bg-surface-container-low">
                <th className="px-4 py-3 font-medium">Accession #</th>
                <th className="px-4 py-3 font-medium">Patient</th>
                <th className="px-4 py-3 font-medium">Template</th>
                <th className="px-4 py-3 font-medium">Status</th>
                <th className="px-4 py-3 font-medium">Date</th>
                <th className="px-4 py-3 font-medium text-right">Action</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {isLoading && (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-on-surface-variant">
                    Loading…
                  </td>
                </tr>
              )}
              {!isLoading && (data?.length ?? 0) === 0 && (
                <tr>
                  <td colSpan={6} className="px-4 py-10 text-center text-on-surface-variant">
                    No reports yet.
                  </td>
                </tr>
              )}
              {data?.map((r, i) => (
                <tr
                  key={r.id}
                  className={`${
                    i % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                  } hover:bg-surface-container transition-colors`}
                >
                  <td className="px-4 py-3 font-mono text-primary-container font-medium">
                    {r.accession_number}
                  </td>
                  <td className="px-4 py-3 text-on-surface font-medium">{r.patient_name}</td>
                  <td className="px-4 py-3 text-on-surface-variant">
                    {r.template_name ?? "—"}
                  </td>
                  <td className="px-4 py-3">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ring-1 ${
                        STATUS_BADGE[r.status.toLowerCase()] ?? STATUS_BADGE.final
                      }`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-on-surface-variant font-mono text-xs">
                    {new Date(r.created_at).toLocaleString()}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <div className="inline-flex items-center gap-3">
                      <button
                        onClick={() => openMyReportPdf(r.id)}
                        className="inline-flex items-center gap-1 text-primary-container font-medium hover:underline text-sm"
                      >
                        <Icon name="visibility" size={14} />
                        View
                      </button>
                      <button
                        onClick={() => downloadMyReportPdf(r.id, `${r.accession_number}.pdf`)}
                        className="inline-flex items-center gap-1 text-primary-container font-medium hover:underline text-sm"
                      >
                        <Icon name="download" size={14} />
                        Download
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
