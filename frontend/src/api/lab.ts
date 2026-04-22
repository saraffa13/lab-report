import { apiClient } from "./client";

export type Lab = {
  id: string;
  name: string;
  slug: string;
  address: string;
  city: string;
  state: string;
  pincode: string;
  country: string;
  phone: string;
  email: string;
  website: string;
  primary_color: string;
  secondary_color: string;
  tax_registration: string;
  accreditation_info: string;
  settings: Record<string, unknown>;
};

export async function getLab(): Promise<Lab> {
  const { data } = await apiClient.get<Lab>("/v1/lab/");
  return data;
}

export async function updateLab(body: Partial<Lab>): Promise<Lab> {
  const { data } = await apiClient.patch<Lab>("/v1/lab/", body);
  return data;
}
