import { apiClient } from "./client";

export type ReportListItem = {
  id: string;
  accession_number: string;
  patient_name: string;
  template_name: string | null;
  status: string;
  signed_at: string | null;
  created_at: string;
  total_amount: string | null;
  payment_status: "paid" | "partial" | "pending" | null;
  paid_at: string | null;
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
  package_id?: string | null;
  results: Array<{ test_id: string; value: string }>;
  referred_by_text?: string;
  clinical_history?: string;
  sample_collected_by_name?: string;
  sample_collected_at?: string | null;
  report_released_at?: string | null;
};

type Paginated<T> = { results: T[] } | T[];

function unwrap<T>(p: Paginated<T>): T[] {
  return Array.isArray(p) ? p : p.results;
}

export async function listReports(): Promise<ReportListItem[]> {
  const { data } = await apiClient.get<Paginated<ReportListItem>>("/v1/reports/");
  return unwrap(data);
}

export async function listMyReports(): Promise<ReportListItem[]> {
  const { data } = await apiClient.get<ReportListItem[]>("/v1/my-reports/");
  return data;
}

export async function getMyReport(id: string): Promise<ReportDetail> {
  const { data } = await apiClient.get<ReportDetail>(`/v1/my-reports/${id}/`);
  return data;
}

export async function downloadMyReportPdf(id: string, filename: string) {
  const resp = await apiClient.get(`/v1/my-reports/${id}/pdf/`, { responseType: "blob" });
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

export async function openMyReportPdf(id: string) {
  const resp = await apiClient.get(`/v1/my-reports/${id}/pdf/`, { responseType: "blob" });
  const blob = new Blob([resp.data], { type: "application/pdf" });
  const url = URL.createObjectURL(blob);
  window.open(url, "_blank", "noopener,noreferrer");
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
}

export type ReferringDoctor = {
  id: string;
  name: string;
  qualification: string;
  specialty: string;
  phone: string;
};

export async function listReferringDoctors(search = ""): Promise<ReferringDoctor[]> {
  const { data } = await apiClient.get<Paginated<ReferringDoctor>>(
    "/v1/referring-doctors/",
    { params: search ? { search } : {} },
  );
  return unwrap(data);
}

export async function createReferringDoctor(name: string): Promise<ReferringDoctor> {
  const { data } = await apiClient.post<ReferringDoctor>("/v1/referring-doctors/", { name });
  return data;
}

export async function listSampleCollectors(): Promise<string[]> {
  const { data } = await apiClient.get<string[]>("/v1/reports/sample-collectors/");
  return data;
}

export async function createReport(payload: CreateReportPayload): Promise<ReportDetail> {
  const { data } = await apiClient.post<ReportDetail>("/v1/reports/", payload);
  return data;
}

export async function getReport(id: string): Promise<ReportDetail> {
  const { data } = await apiClient.get<ReportDetail>(`/v1/reports/${id}/`);
  return data;
}

export async function updateReportPayment(
  id: string,
  payload: { total_amount?: number | null; payment_status?: "paid" | "partial" | "pending" },
): Promise<ReportDetail> {
  const { data } = await apiClient.post<ReportDetail>(`/v1/reports/${id}/payment/`, payload);
  return data;
}

export async function deleteReport(id: string): Promise<void> {
  await apiClient.delete(`/v1/reports/${id}/`);
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
