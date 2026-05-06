import { Link } from "react-router-dom";
import { useQuery } from "@tanstack/react-query";
import { getDashboardStats } from "@/api/dashboard";
import { downloadPdf } from "@/api/reports";
import { Icon } from "@/components/ui/Icon";

const STATUS_BADGE: Record<string, string> = {
  final: "bg-secondary-container text-on-secondary-container ring-on-secondary-container/20",
  draft: "bg-tertiary-fixed text-on-tertiary-fixed ring-on-tertiary-fixed/20",
  pending: "bg-tertiary-fixed text-on-tertiary-fixed ring-on-tertiary-fixed/20",
  critical: "bg-error-container text-on-error-container ring-on-error-container/20",
  cancelled: "bg-surface-container-high text-on-surface-variant ring-outline-variant/30",
};

function statusClass(status: string) {
  return STATUS_BADGE[status.toLowerCase()] ?? STATUS_BADGE.final;
}

export default function DashboardPage() {
  const { data, isLoading } = useQuery({ queryKey: ["dashboard"], queryFn: getDashboardStats });

  const byStatus = data?.reports_by_status ?? [];
  const total = byStatus.reduce((s, x) => s + x.count, 0) || (data?.reports_total ?? 0);
  const pct = (n: number) => (total ? Math.round((n / total) * 100) : 0);
  const completed = byStatus.find((x) => x.status === "final")?.count ?? 0;
  const pending = byStatus.find((x) => x.status === "draft" || x.status === "pending")?.count ?? 0;
  const critical = byStatus.find((x) => x.status === "cancelled")?.count ?? 0;

  const donutGradient = total
    ? `conic-gradient(#0b2a5b 0% ${pct(completed)}%, #6df5e1 ${pct(completed)}% ${
        pct(completed) + pct(pending)
      }%, #ffdad6 ${pct(completed) + pct(pending)}% 100%)`
    : "conic-gradient(#eceef0 0% 100%)";

  return (
    <div className="flex gap-8 items-start">
      {/* Main content */}
      <div className="flex-grow flex flex-col gap-8 min-w-0">
        <div>
          <h1 className="text-3xl font-extrabold text-on-primary-fixed tracking-tight">Overview</h1>
          <p className="text-on-surface-variant text-sm mt-1">
            Real-time metrics and recent accession activity.
          </p>
        </div>

        {/* Revenue (admin/lab_owner only) */}
        {data?.revenue && (
          <div className="bg-surface-container-lowest rounded-xl p-6 shadow-dossier ring-1 ring-outline-variant/15">
            <div className="flex items-baseline justify-between mb-4">
              <h3 className="text-xs font-bold text-on-primary-fixed uppercase tracking-wider flex items-center gap-2">
                <Icon name="payments" size={16} className="text-secondary" />
                Revenue (Paid)
              </h3>
              <span className="text-xs text-on-surface-variant">
                {data.revenue.paid_count} paid report
                {data.revenue.paid_count === 1 ? "" : "s"}
              </span>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <RevenueStat label="Today" amount={data.revenue.today} />
              <RevenueStat label="Last 7 days" amount={data.revenue.week} />
              <RevenueStat label="Last 30 days" amount={data.revenue.month} />
              <RevenueStat label="All time" amount={data.revenue.total} tone="primary" />
            </div>
          </div>
        )}

        {/* KPI cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          <KpiCard
            label="Reports Today"
            value={data?.reports_today}
            loading={isLoading}
            icon="lab_panel"
            iconTone="text-secondary"
            trend="+12% vs yesterday"
            trendTone="text-secondary"
            trendIcon="trending_up"
          />
          <KpiCard
            label="Reports This Week"
            value={data?.reports_this_week}
            loading={isLoading}
            icon="calendar_month"
            iconTone="text-primary-container"
            trend="+4.2% vs last week"
            trendTone="text-secondary"
            trendIcon="trending_up"
          />
          <KpiCard
            label="Pending Review"
            value={data?.reports_pending}
            loading={isLoading}
            icon="pending_actions"
            iconTone="text-on-tertiary-container"
            trend="Requires attention"
            trendTone="text-error"
            trendIcon="priority_high"
          />
          <KpiCard
            label="Total Patients"
            value={data?.patients_total}
            loading={isLoading}
            icon="groups"
            iconTone="text-on-surface-variant"
            trend="Steady growth"
            trendTone="text-on-surface-variant"
            trendIcon="horizontal_rule"
          />
        </div>

        {/* Donut + ledger */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6 items-start">
          <div className="bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 p-6 xl:col-span-1 h-full flex flex-col">
            <h3 className="text-xs font-semibold text-on-primary-fixed mb-6 uppercase tracking-wider">
              Reports by Status
            </h3>
            <div className="flex-grow flex items-center justify-center relative">
              <div
                className="w-40 h-40 rounded-full flex items-center justify-center relative"
                style={{ background: donutGradient }}
              >
                <div className="w-24 h-24 bg-surface-container-lowest rounded-full shadow-inner flex flex-col items-center justify-center absolute z-10">
                  <span className="text-xl font-bold text-on-primary-fixed font-mono">
                    {isLoading ? "—" : total}
                  </span>
                  <span className="text-[10px] text-on-surface-variant font-medium uppercase">
                    Total
                  </span>
                </div>
              </div>
            </div>
            <div className="mt-8 flex flex-col gap-3">
              <LegendRow color="bg-primary-container" label="Completed" pct={pct(completed)} />
              <LegendRow
                color="bg-secondary-container ring-1 ring-secondary/20"
                label="In Progress"
                pct={pct(pending)}
              />
              <LegendRow
                color="bg-error-container ring-1 ring-error/20"
                label="Cancelled"
                pct={pct(critical)}
              />
            </div>
          </div>

          <div className="bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 overflow-hidden xl:col-span-2">
            <div className="p-5 flex justify-between items-center bg-primary-container">
              <h3 className="text-xs font-semibold text-on-primary uppercase tracking-wider">
                {data?.top_patients ? "Top Patients by Revenue" : "Recent Reports"}
              </h3>
              <Link
                to={data?.top_patients ? "/patients" : "/reports"}
                className="text-on-primary text-sm hover:underline font-medium"
              >
                View All
              </Link>
            </div>
            {data?.top_patients ? (
              <div className="overflow-x-auto">
                <table className="w-full text-left border-collapse">
                  <thead>
                    <tr className="text-xs text-on-surface-variant uppercase tracking-wider bg-surface-container-low">
                      <th className="px-4 py-3 font-medium w-10">#</th>
                      <th className="px-4 py-3 font-medium">Patient</th>
                      <th className="px-4 py-3 font-medium">Phone</th>
                      <th className="px-4 py-3 font-medium text-right">Paid</th>
                      <th className="px-4 py-3 font-medium text-right">Reports</th>
                    </tr>
                  </thead>
                  <tbody className="text-sm">
                    {isLoading && (
                      <tr>
                        <td colSpan={5} className="px-4 py-10 text-center text-on-surface-variant">
                          Loading…
                        </td>
                      </tr>
                    )}
                    {!isLoading && data.top_patients.length === 0 && (
                      <tr>
                        <td colSpan={5} className="px-4 py-10 text-center text-on-surface-variant">
                          No paid reports yet — revenue ranking will appear once payments come in.
                        </td>
                      </tr>
                    )}
                    {data.top_patients.map((p, i) => (
                      <tr
                        key={p.id}
                        className={`${
                          i % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                        } hover:bg-surface-container transition-colors`}
                      >
                        <td className="px-4 py-2.5 font-mono text-on-surface-variant text-xs">
                          {i + 1}
                        </td>
                        <td className="px-4 py-2.5">
                          <Link
                            to={`/patients/${p.id}`}
                            className="font-semibold text-on-surface hover:text-primary-container hover:underline"
                          >
                            {p.name}
                          </Link>
                          <div className="text-[11px] text-on-surface-variant font-mono">
                            {p.patient_code}
                          </div>
                        </td>
                        <td className="px-4 py-2.5 text-on-surface-variant font-mono text-xs">
                          {p.phone || "—"}
                        </td>
                        <td className="px-4 py-2.5 text-right font-mono font-bold text-on-primary-fixed">
                          ₹{Number(p.total_paid).toLocaleString("en-IN", { maximumFractionDigits: 2 })}
                        </td>
                        <td className="px-4 py-2.5 text-right">
                          <span className="inline-flex items-center gap-1 bg-primary-container/20 text-primary-container text-xs font-semibold px-2 py-0.5 rounded">
                            <Icon name="description" size={12} />
                            {p.reports_generated}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
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
                  {!isLoading && (data?.recent_reports?.length ?? 0) === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-10 text-center text-on-surface-variant">
                        No reports yet.{" "}
                        <Link to="/reports/new" className="text-primary-container font-medium hover:underline">
                          Create the first one →
                        </Link>
                      </td>
                    </tr>
                  )}
                  {data?.recent_reports?.map((r, i) => (
                    <tr
                      key={r.id}
                      className={`${
                        i % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                      } hover:bg-surface-container transition-colors`}
                    >
                      <td className="px-4 py-2.5 font-mono text-primary-container font-medium">
                        <Link to={`/reports/${r.id}`} className="hover:underline">
                          {r.accession_number}
                        </Link>
                      </td>
                      <td className="px-4 py-2.5 text-on-surface font-medium">{r.patient_name}</td>
                      <td className="px-4 py-2.5 text-on-surface-variant">
                        {r.template_name ?? "—"}
                      </td>
                      <td className="px-4 py-2.5">
                        <span
                          className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-medium ring-1 ${statusClass(
                            r.status
                          )}`}
                        >
                          {r.status}
                        </span>
                      </td>
                      <td className="px-4 py-2.5 text-on-surface-variant font-mono text-xs">
                        {new Date(r.created_at).toLocaleString()}
                      </td>
                      <td className="px-4 py-2.5 text-right">
                        <button
                          onClick={() => downloadPdf(r.id, r.suggested_filename)}
                          className="text-primary-container font-medium hover:text-secondary transition-colors text-sm"
                        >
                          View PDF
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            )}
          </div>
        </div>
      </div>

      {/* Right sidebar */}
      <aside className="hidden xl:flex flex-col w-80 flex-shrink-0 gap-6 sticky top-24">
        <div className="bg-surface-container-low rounded-2xl p-6 ring-1 ring-outline-variant/10">
          <h3 className="text-xs font-bold text-on-primary-fixed mb-4 uppercase tracking-wider">
            Quick Actions
          </h3>
          <div className="flex flex-col gap-3">
            <Link
              to="/reports/new"
              className="w-full flex items-center justify-center gap-2 bg-gradient-to-b from-primary-container to-primary text-on-primary py-2.5 px-4 rounded-md font-medium text-sm shadow-md hover:shadow-lg transition-all active:scale-[0.98]"
            >
              <Icon name="add_circle" size={18} />
              New Report
            </Link>
            <Link
              to="/patients/new"
              className="w-full flex items-center justify-center gap-2 bg-surface-container-high text-primary-container py-2.5 px-4 rounded-md font-medium text-sm hover:bg-surface-container-highest transition-all active:scale-[0.98]"
            >
              <Icon name="person_add" size={18} />
              Register Patient
            </Link>
          </div>
        </div>

        <div className="bg-surface-container-lowest rounded-2xl p-6 ring-1 ring-outline-variant/15 shadow-ambient">
          <div className="flex items-center gap-3 mb-4">
            <Icon
              name="medical_services"
              size={24}
              filled
              className="text-primary-container"
            />
            <div>
              <h4 className="text-sm font-bold text-on-surface">Pathology Dept.</h4>
              <p className="text-xs text-on-surface-variant">Active Session</p>
            </div>
          </div>
          <div className="space-y-2 text-sm border-t border-outline-variant/10 pt-4 mt-2">
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Total Reports</span>
              <span className="font-medium text-on-surface font-mono">
                {data?.reports_total ?? "—"}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-on-surface-variant">Patients On File</span>
              <span className="font-medium text-on-surface font-mono">
                {data?.patients_total ?? "—"}
              </span>
            </div>
          </div>
        </div>
      </aside>
    </div>
  );
}

function KpiCard({
  label,
  value,
  loading,
  icon,
  iconTone,
  trend,
  trendTone,
  trendIcon,
}: {
  label: string;
  value?: number;
  loading?: boolean;
  icon: string;
  iconTone: string;
  trend: string;
  trendTone: string;
  trendIcon: string;
}) {
  return (
    <div className="bg-surface-container-lowest rounded-xl p-5 shadow-dossier ring-1 ring-outline-variant/15 flex flex-col justify-between">
      <div className="flex justify-between items-start mb-2">
        <span className="text-xs text-on-surface-variant font-medium">{label}</span>
        <Icon name={icon} size={18} className={iconTone} />
      </div>
      <div>
        <div className="text-3xl font-bold text-on-primary-fixed mb-1 font-mono tracking-tighter">
          {loading ? "—" : (value ?? 0).toLocaleString()}
        </div>
        <div className={`flex items-center text-xs font-medium ${trendTone}`}>
          <Icon name={trendIcon} size={14} className="mr-1" />
          <span>{trend}</span>
        </div>
      </div>
    </div>
  );
}

function RevenueStat({
  label,
  amount,
  tone = "default",
}: {
  label: string;
  amount: string;
  tone?: "default" | "primary";
}) {
  const n = Number(amount || 0);
  const pretty = Number.isFinite(n)
    ? `₹${n.toLocaleString("en-IN", { maximumFractionDigits: 2 })}`
    : `₹${amount}`;
  return (
    <div
      className={
        tone === "primary"
          ? "bg-primary-container text-on-primary rounded-lg p-4"
          : "bg-surface-container-low rounded-lg p-4 ring-1 ring-outline-variant/10"
      }
    >
      <div
        className={
          tone === "primary"
            ? "text-[11px] uppercase tracking-wider opacity-80"
            : "text-[11px] text-on-surface-variant uppercase tracking-wider"
        }
      >
        {label}
      </div>
      <div
        className={
          tone === "primary"
            ? "text-2xl font-bold font-mono mt-1"
            : "text-2xl font-bold font-mono text-on-primary-fixed mt-1"
        }
      >
        {pretty}
      </div>
    </div>
  );
}

function LegendRow({ color, label, pct }: { color: string; label: string; pct: number }) {
  return (
    <div className="flex items-center justify-between text-sm">
      <div className="flex items-center gap-2">
        <div className={`w-3 h-3 rounded-sm ${color}`} />
        <span className="text-on-surface-variant">{label}</span>
      </div>
      <span className="font-mono font-medium text-on-surface">{pct}%</span>
    </div>
  );
}
