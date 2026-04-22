import { apiClient } from "./client";

export type ReportListItem = {
  id: string;
  accession_number: string;
  patient_name: string;
  template_name: string | null;
  status: string;
  signed_at: string | null;
  created_at: string;
};

export type ReportDetail = ReportListItem & {
  barcode_number: string;
  patient: string;
  report_template: string | null;
  referred_by_text: string;
  clinical_history: string;
  results: Array<{
    id: string;
    test: string;
    test_name: string;
    test_category: string;
    result_value: string;
    unit_used: string;
    reference_range_used: string;
    is_abnormal: boolean;
    flag: string;
  }>;
};

export type CreateReportPayload = {
  patient: {
    name: string;
    sex: "M" | "F" | "O";
    age: number | null;
    age_unit: "years" | "months" | "days";
    phone?: string;
    email?: string;
    city?: string;
    blood_group?: string;
  };
  template_id?: string | null;
  results: Array<{ test_id: string; value: string }>;
  referred_by_text?: string;
  clinical_history?: string;
};

type Paginated<T> = { results: T[] } | T[];

function unwrap<T>(p: Paginated<T>): T[] {
  return Array.isArray(p) ? p : p.results;
}

export async function listReports(): Promise<ReportListItem[]> {
  const { data } = await apiClient.get<Paginated<ReportListItem>>("/v1/reports/");
  return unwrap(data);
}

export async function createReport(payload: CreateReportPayload): Promise<ReportDetail> {
  const { data } = await apiClient.post<ReportDetail>("/v1/reports/", payload);
  return data;
}

export function pdfUrl(reportId: string): string {
  return `/api/v1/reports/${reportId}/pdf/`;
}

export async function downloadPdf(reportId: string, filename: string) {
  const resp = await apiClient.get(`/v1/reports/${reportId}/pdf/`, { responseType: "blob" });
  const blob = new Blob([resp.data], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
