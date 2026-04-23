import { useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { deletePatient, listPatients } from "@/api/patients";
import { Icon } from "@/components/ui/Icon";
import { BulkActionsBar } from "@/components/BulkActionsBar";
import { useAuth } from "@/hooks/useAuth";

const CAN_DELETE_ROLES = new Set(["admin", "lab_owner"]);

export default function PatientsListPage() {
  const [search, setSearch] = useState("");
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const canDelete =
    !!user && (user.is_superuser || (user.role_code && CAN_DELETE_ROLES.has(user.role_code)));
  const { data, isLoading } = useQuery({
    queryKey: ["patients", search],
    queryFn: () => listPatients(search),
  });
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [bulkBusy, setBulkBusy] = useState(false);

  function toggleOne(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }
  function clearSelection() {
    setSelected(new Set());
  }
  function toggleAllVisible() {
    setSelected((prev) => {
      const ids = (data ?? []).map((p) => p.id);
      const allSelectedHere = ids.length > 0 && ids.every((id) => prev.has(id));
      if (allSelectedHere) return new Set();
      return new Set(ids);
    });
  }
  async function bulkDelete() {
    if (selected.size === 0) return;
    if (
      !window.confirm(
        `Delete ${selected.size} patient${selected.size === 1 ? "" : "s"}? Their reports will remain. This cannot be undone.`,
      )
    )
      return;
    setBulkBusy(true);
    try {
      const ids = Array.from(selected);
      const results = await Promise.allSettled(ids.map((id) => deletePatient(id)));
      const failed = results.filter((r) => r.status === "rejected").length;
      await queryClient.invalidateQueries({ queryKey: ["patients"] });
      clearSelection();
      if (failed > 0) alert(`${failed} delete${failed === 1 ? "" : "s"} failed.`);
    } finally {
      setBulkBusy(false);
    }
  }

  const newThisWeek = useMemo(() => {
    if (!data) return 0;
    const weekAgo = Date.now() - 7 * 86400 * 1000;
    return data.filter((p) => new Date(p.created_at).getTime() > weekAgo).length;
  }, [data]);

  return (
    <div className="flex flex-col gap-8">
      {canDelete && (
        <BulkActionsBar
          count={selected.size}
          label="patient"
          onClear={clearSelection}
          onDelete={bulkDelete}
          busy={bulkBusy}
        />
      )}
      <header className="flex flex-col lg:flex-row gap-6 justify-between items-start lg:items-end">
        <div className="flex flex-col gap-2">
          <h1 className="text-4xl font-bold text-on-primary-fixed tracking-tight">
            Patient Directory
          </h1>
          <p className="text-on-surface-variant text-sm max-w-xl">
            Manage patient records, historical laboratory reports, and demographic information.
            Authorized personnel only.
          </p>
        </div>
        <div className="flex gap-4">
          <StatPill label="Total Active" value={data?.length ?? 0} tone="primary" />
          <StatPill label="New This Week" value={newThisWeek} tone="secondary" prefix="+" />
        </div>
      </header>

      <div className="flex flex-col sm:flex-row justify-between items-center gap-3 bg-surface-container-low p-2 rounded-xl">
        <div className="relative w-full sm:w-[400px]">
          <Icon
            name="search"
            size={18}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant"
          />
          <input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search by patient name, code, or phone..."
            className="w-full bg-surface-container-lowest border border-outline-variant/15 text-on-surface text-sm rounded-lg pl-10 pr-4 py-2.5 focus:border-secondary focus:ring-1 focus:ring-secondary outline-none transition-all shadow-sm placeholder:text-outline"
          />
        </div>
        <div className="flex items-center gap-3 w-full sm:w-auto">
          <Link
            to="/patients/new"
            className="bg-gradient-to-b from-primary-container to-primary text-on-primary text-sm font-medium px-5 py-2.5 rounded-lg flex items-center gap-2 hover:opacity-90 shadow-[0_4px_12px_rgba(11,42,91,0.2)] transition-all whitespace-nowrap"
          >
            <Icon name="add" size={18} />
            New Patient
          </Link>
        </div>
      </div>

      <div className="bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse whitespace-nowrap">
            <thead>
              <tr className="bg-primary-container text-on-primary text-xs uppercase tracking-wider">
                {canDelete && (
                  <th className="py-3.5 px-3 w-10 text-center">
                    <input
                      type="checkbox"
                      checked={(data?.length ?? 0) > 0 && (data ?? []).every((p) => selected.has(p.id))}
                      onChange={toggleAllVisible}
                      aria-label="Select all visible"
                      className="accent-on-primary cursor-pointer"
                    />
                  </th>
                )}
                <th className="py-3.5 px-5 font-semibold">Patient Code</th>
                <th className="py-3.5 px-5 font-semibold">Name</th>
                <th className="py-3.5 px-5 font-semibold">Sex / Age</th>
                <th className="py-3.5 px-5 font-semibold">Phone</th>
                <th className="py-3.5 px-5 font-semibold">City</th>
                <th className="py-3.5 px-5 font-semibold text-right">Reports</th>
                <th className="py-3.5 px-5 font-semibold">Created</th>
                <th className="py-3.5 px-5 font-semibold text-right w-20">Actions</th>
              </tr>
            </thead>
            <tbody className="text-sm">
              {isLoading && (
                <tr>
                  <td colSpan={canDelete ? 9 : 8} className="py-10 px-5 text-center text-on-surface-variant">
                    Loading patients…
                  </td>
                </tr>
              )}
              {!isLoading && data?.length === 0 && (
                <tr>
                  <td colSpan={canDelete ? 9 : 8} className="py-16 px-5 text-center">
                    <Icon
                      name="groups"
                      size={40}
                      className="text-outline-variant mb-2 block mx-auto"
                    />
                    <div className="text-on-surface-variant text-sm">
                      {search ? "No patients match your search." : "No patients yet. "}
                      <Link
                        to="/patients/new"
                        className="text-primary-container font-medium hover:underline"
                      >
                        Register the first patient →
                      </Link>
                    </div>
                  </td>
                </tr>
              )}
              {data?.map((p, i) => {
                const reportsTone =
                  p.reports_count >= 20
                    ? "bg-error-container text-on-error-container border-on-error-container/20"
                    : p.reports_count >= 5
                    ? "bg-secondary-container text-on-secondary-container border-on-secondary-container/20"
                    : "";
                return (
                  <tr
                    key={p.id}
                    className={`${
                      i % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                    } ${selected.has(p.id) ? "ring-2 ring-inset ring-primary-container" : ""} hover:bg-surface-container-high transition-colors group`}
                  >
                    {canDelete && (
                      <td className="py-3 px-3 text-center">
                        <input
                          type="checkbox"
                          checked={selected.has(p.id)}
                          onChange={() => toggleOne(p.id)}
                          aria-label={`Select ${p.name}`}
                          className="accent-primary-container cursor-pointer"
                        />
                      </td>
                    )}
                    <td className="py-3 px-5">
                      <Link
                        to={`/patients/${p.id}`}
                        className="font-mono font-semibold text-primary-container hover:underline"
                      >
                        {p.patient_code}
                      </Link>
                    </td>
                    <td className="py-3 px-5 font-semibold text-on-surface">
                      <Link to={`/patients/${p.id}`} className="hover:underline">
                        {p.name}
                      </Link>
                    </td>
                    <td className="py-3 px-5 text-on-surface-variant">
                      {p.sex_display}
                      {p.age ? ` / ${p.age}` : ""}
                    </td>
                    <td className="py-3 px-5 text-on-surface-variant font-mono text-xs">
                      {p.phone || "—"}
                    </td>
                    <td className="py-3 px-5 text-on-surface-variant">{p.city || "—"}</td>
                    <td className="py-3 px-5 text-right">
                      {reportsTone ? (
                        <span
                          className={`${reportsTone} text-xs font-semibold px-2 py-0.5 rounded border`}
                        >
                          {p.reports_count}
                        </span>
                      ) : (
                        <span className="font-mono text-on-surface-variant">
                          {p.reports_count}
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-5 text-on-surface-variant text-xs">
                      {new Date(p.created_at).toLocaleDateString(undefined, {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </td>
                    <td className="py-3 px-5 text-right">
                      <Link
                        to={`/patients/${p.id}`}
                        className="inline-flex items-center gap-1 text-primary-container hover:text-secondary text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity"
                      >
                        View <Icon name="arrow_forward" size={14} />
                      </Link>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="bg-surface-container px-5 py-3 flex items-center justify-between">
          <span className="text-xs text-on-surface-variant">
            Showing{" "}
            <span className="font-semibold text-on-surface">{data?.length ?? 0}</span>{" "}
            {data?.length === 1 ? "patient" : "patients"}
          </span>
        </div>
      </div>
    </div>
  );
}

function StatPill({
  label,
  value,
  tone,
  prefix = "",
}: {
  label: string;
  value: number;
  tone: "primary" | "secondary";
  prefix?: string;
}) {
  return (
    <div className="bg-surface-container-lowest px-5 py-3 rounded-xl shadow-dossier ring-1 ring-outline-variant/15 min-w-[140px]">
      <p className="text-xs text-on-surface-variant uppercase tracking-wider mb-1">{label}</p>
      <p
        className={`text-2xl font-bold font-mono ${
          tone === "primary" ? "text-primary-container" : "text-secondary"
        }`}
      >
        {prefix}
        {value.toLocaleString()}
      </p>
    </div>
  );
}
