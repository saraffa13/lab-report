import { apiClient } from "./client";

export type Patient = {
  id: string;
  patient_code: string;
  name: string;
  sex: "M" | "F" | "O";
  sex_display: string;
  age: number | null;
  age_unit: "years" | "months" | "days";
  date_of_birth: string | null;
  blood_group: string;
  phone: string;
  alternate_phone: string;
  email: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  emergency_contact_name: string;
  emergency_contact_phone: string;
  notes: string;
  reports_count: number;
  created_at: string;
  updated_at: string;
};

type Paginated<T> = { results: T[] } | T[];
const unwrap = <T,>(p: Paginated<T>): T[] => (Array.isArray(p) ? p : p.results);

export async function listPatients(search = ""): Promise<Patient[]> {
  const { data } = await apiClient.get<Paginated<Patient>>("/v1/patients/", {
    params: search ? { search } : {},
  });
  return unwrap(data);
}

export async function getPatient(id: string): Promise<Patient> {
  const { data } = await apiClient.get<Patient>(`/v1/patients/${id}/`);
  return data;
}

export async function createPatient(body: Partial<Patient>): Promise<Patient> {
  const { data } = await apiClient.post<Patient>("/v1/patients/", body);
  return data;
}

export async function updatePatient(id: string, body: Partial<Patient>): Promise<Patient> {
  const { data } = await apiClient.patch<Patient>(`/v1/patients/${id}/`, body);
  return data;
}

export async function deletePatient(id: string): Promise<void> {
  await apiClient.delete(`/v1/patients/${id}/`);
}

export async function getPatientReports(id: string) {
  const { data } = await apiClient.get(`/v1/patients/${id}/reports/`);
  return data;
}

export async function exportPatientData(id: string) {
  const { data } = await apiClient.get(`/v1/patients/${id}/export/`);
  return data;
}

export async function createPatientLogin(
  id: string,
  password?: string,
): Promise<{ user_id: string; phone: string; password: string; reused: boolean; detail: string }> {
  const { data } = await apiClient.post(`/v1/patients/${id}/create-login/`, password ? { password } : {});
  return data;
}
