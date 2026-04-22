import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { downloadPdf, listReports } from "@/api/reports";
import { Icon } from "@/components/ui/Icon";

const STATUS_STYLES: Record<string, string> = {
  final: "bg-secondary-container text-on-secondary-container ring-on-secondary-container/20",
  draft: "bg-surface-container-highest text-on-surface-variant ring-outline-variant/50",
  pending: "bg-tertiary-fixed text-on-tertiary-fixed ring-on-tertiary-fixed/20",
  cancelled: "bg-error-container text-on-error-container ring-on-error-container/20",
};

function statusClass(s: string) {
  return STATUS_STYLES[s.toLowerCase()] ?? STATUS_STYLES.final;
}

export default function ReportsListPage() {
  const { data, isLoading, error } = useQuery({ queryKey: ["reports"], queryFn: listReports });
  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [templateFilter, setTemplateFilter] = useState("");

  const templateOptions = useMemo(() => {
    const set = new Set<string>();
    (data ?? []).forEach((r) => r.template_name && set.add(r.template_name));
    return Array.from(set).sort();
  }, [data]);

  const filtered = useMemo(() => {
    return (data ?? []).filter((r) => {
      if (status && r.status.toLowerCase() !== status) return false;
      if (templateFilter && r.template_name !== templateFilter) return false;
      if (search) {
        const q = search.toLowerCase();
        if (
          !r.accession_number.toLowerCase().includes(q) &&
          !r.patient_name.toLowerCase().includes(q)
        )
          return false;
      }
      return true;
    });
  }, [data, search, status, templateFilter]);

  function clearFilters() {
    setSearch("");
    setStatus("");
    setTemplateFilter("");
  }

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-on-primary-fixed tracking-tight">Reports Ledger</h1>
          <p className="text-on-surface-variant text-sm mt-1">
            Manage and review all diagnostic pathology reports.
          </p>
        </div>
        <Link
          to="/reports/new"
          className="inline-flex items-center gap-2 bg-gradient-to-b from-primary-container to-primary text-on-primary px-5 py-2.5 rounded-md font-medium text-sm shadow-md hover:opacity-90 transition-opacity whitespace-nowrap"
        >
          <Icon name="add" size={16} />
          New Report
        </Link>
      </div>

      {/* Filters */}
      <div className="bg-surface-container-lowest p-4 rounded-xl shadow-dossier ring-1 ring-outline-variant/15 flex flex-wrap items-center gap-3">
        <div className="relative flex-grow min-w-[220px]">
          <Icon
            name="search"
            size={16}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant"
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 bg-surface-container border-none rounded-md text-sm focus:ring-1 focus:ring-secondary focus:bg-surface-container-lowest outline-none transition-colors placeholder:text-on-surface-variant"
            placeholder="Search accession # or patient name..."
          />
        </div>
        <div className="relative min-w-[140px]">
          <select
            value={status}
            onChange={(e) => setStatus(e.target.value)}
            className="w-full appearance-none pl-4 pr-10 py-2 bg-surface-container border-none rounded-md text-sm focus:ring-1 focus:ring-secondary focus:bg-surface-container-lowest outline-none transition-colors text-on-surface cursor-pointer"
          >
            <option value="">All Statuses</option>
            <option value="final">Final</option>
            <option value="draft">Draft</option>
            <option value="pending">Pending</option>
            <option value="cancelled">Cancelled</option>
          </select>
          <Icon
            name="expand_more"
            size={16}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
          />
        </div>
        <div className="relative min-w-[180px]">
          <select
            value={templateFilter}
            onChange={(e) => setTemplateFilter(e.target.value)}
            className="w-full appearance-none pl-4 pr-10 py-2 bg-surface-container border-none rounded-md text-sm focus:ring-1 focus:ring-secondary focus:bg-surface-container-lowest outline-none transition-colors text-on-surface cursor-pointer"
          >
            <option value="">All Templates</option>
            {templateOptions.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
          <Icon
            name="expand_more"
            size={16}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
          />
        </div>
        <button
          onClick={clearFilters}
          className="p-2 text-on-surface-variant hover:text-primary-container hover:bg-surface-container rounded-md transition-colors"
          title="Clear filters"
        >
          <Icon name="filter_alt_off" size={18} />
        </button>
      </div>

      {/* Table */}
      <div className="bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead className="bg-primary-container text-on-primary">
              <tr>
                <th className="py-3 px-5 text-xs font-semibold tracking-wider uppercase w-32">
                  Accession #
                </th>
                <th className="py-3 px-5 text-xs font-semibold tracking-wider uppercase">
                  Patient Name
                </th>
                <th className="py-3 px-5 text-xs font-semibold tracking-wider uppercase">
                  Template
                </th>
                <th className="py-3 px-5 text-xs font-semibold tracking-wider uppercase w-24">
                  Status
                </th>
                <th className="py-3 px-5 text-xs font-semibold tracking-wider uppercase w-32">
                  Date
                </th>
                <th className="py-3 px-5 text-xs font-semibold tracking-wider uppercase text-right w-28">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {isLoading && (
                <tr>
                  <td colSpan={6} className="py-10 px-5 text-center text-on-surface-variant">
                    Loading reports…
                  </td>
                </tr>
              )}
              {error && !isLoading && (
                <tr>
                  <td colSpan={6} className="py-10 px-5 text-center text-on-error-container">
                    Failed to load reports.
                  </td>
                </tr>
              )}
              {!isLoading && !error && filtered.length === 0 && (
                <tr>
                  <td colSpan={6} className="py-16 px-5 text-center">
                    <Icon
                      name="description"
                      size={36}
                      className="text-outline-variant mb-2 block mx-auto"
                    />
                    <div className="text-on-surface-variant text-sm">
                      {(data?.length ?? 0) === 0
                        ? "No reports yet. "
                        : "No reports match your filters. "}
                      <Link
                        to="/reports/new"
                        className="text-primary-container font-medium hover:underline"
                      >
                        Create a new report →
                      </Link>
                    </div>
                  </td>
                </tr>
              )}
              {filtered.map((r, i) => (
                <tr
                  key={r.id}
                  className={`${
                    i % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                  } hover:bg-surface-container-highest transition-colors group`}
                >
                  <td className="py-2.5 px-5 font-mono text-on-primary-fixed-variant font-medium">
                    <Link to={`/reports/${r.id}`} className="hover:underline">
                      {r.accession_number}
                    </Link>
                  </td>
                  <td className="py-2.5 px-5 font-semibold text-on-surface">{r.patient_name}</td>
                  <td className="py-2.5 px-5 text-on-surface-variant">
                    {r.template_name ?? "—"}
                  </td>
                  <td className="py-2.5 px-5">
                    <span
                      className={`inline-flex items-center px-2 py-0.5 rounded-md text-xs font-medium ring-1 ${statusClass(
                        r.status,
                      )}`}
                    >
                      {r.status}
                    </span>
                  </td>
                  <td className="py-2.5 px-5 font-mono text-on-surface-variant text-xs">
                    {new Date(r.created_at).toLocaleDateString(undefined, {
                      day: "2-digit",
                      month: "short",
                      year: "numeric",
                    })}
                  </td>
                  <td className="py-2.5 px-5 text-right">
                    <div className="flex items-center justify-end gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Link
                        to={`/reports/${r.id}`}
                        className="p-1.5 text-primary-container hover:bg-surface-container-high rounded-md transition-colors"
                        title="View report"
                      >
                        <Icon name="visibility" size={18} />
                      </Link>
                      <button
                        onClick={() => downloadPdf(r.id, `${r.accession_number}.pdf`)}
                        className="p-1.5 text-primary-container hover:bg-surface-container-high rounded-md transition-colors"
                        title="Download PDF"
                      >
                        <Icon name="download" size={18} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="bg-surface-container px-5 py-3 flex items-center justify-between">
          <span className="text-xs text-on-surface-variant">
            Showing{" "}
            <span className="font-semibold text-on-surface">{filtered.length}</span> of{" "}
            <span className="font-semibold text-on-surface">{data?.length ?? 0}</span> reports
          </span>
        </div>
      </div>
    </div>
  );
}
