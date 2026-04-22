import { apiClient } from "./client";
import type { ReportListItem } from "./reports";

export type DashboardStats = {
  reports_today: number;
  reports_this_week: number;
  reports_pending: number;
  reports_total: number;
  patients_total: number;
  reports_by_status: Array<{ status: string; count: number }>;
  recent_reports: ReportListItem[];
};

export async function getDashboardStats(): Promise<DashboardStats> {
  const { data } = await apiClient.get<DashboardStats>("/v1/dashboard/stats/");
  return data;
}
