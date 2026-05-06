import { apiClient } from "./client";

export type ReferenceRange = {
  id: string;
  sex: "M" | "F" | "A";
  age_min_years: number | null;
  age_max_years: number | null;
  range_min: string | null;
  range_max: string | null;
  range_text: string;
  critical_low: string | null;
  critical_high: string | null;
  unit_override: string;
  note: string;
  display: string;
};

export type Test = {
  id: string;
  code: string;
  name: string;
  short_name: string;
  category: string;
  category_name: string;
  sample_type: string;
  method: string;
  unit: string;
  decimal_places?: number;
  clinical_significance?: string;
  display_order?: number;
  is_system?: boolean;
  is_editable?: boolean;
  reference_ranges: ReferenceRange[];
};

export type TestWriteRange = {
  sex: "M" | "F" | "A";
  age_min_years?: number | null;
  age_max_years?: number | null;
  range_min?: string | number | null;
  range_max?: string | number | null;
  range_text?: string;
  critical_low?: string | number | null;
  critical_high?: string | number | null;
  unit_override?: string;
  note?: string;
};

export type TestWriteBody = {
  code: string;
  name: string;
  short_name?: string;
  category: string;
  sample_type?: string;
  method?: string;
  unit?: string;
  decimal_places?: number;
  clinical_significance?: string;
  display_order?: number;
  is_active?: boolean;
  reference_ranges?: TestWriteRange[];
};

export type TemplateSummary = {
  id: string;
  code: string;
  name: string;
  description: string;
};

export type TemplateDetail = TemplateSummary & {
  template_tests: Array<{
    id: string;
    display_order: number;
    section: string;
    is_required: boolean;
    test: Test;
  }>;
  is_system: boolean;
  is_editable: boolean;
};

export type TemplateWriteBody = {
  name: string;
  code: string;
  description?: string;
  test_ids: string[];
};

type Paginated<T> = { results: T[] } | T[];

function unwrap<T>(p: Paginated<T>): T[] {
  return Array.isArray(p) ? p : p.results;
}

export async function listTemplates(): Promise<TemplateSummary[]> {
  const { data } = await apiClient.get<Paginated<TemplateSummary>>("/v1/catalog/templates/");
  return unwrap(data);
}

export async function getTemplate(id: string): Promise<TemplateDetail> {
  const { data } = await apiClient.get<TemplateDetail>(`/v1/catalog/templates/${id}/`);
  return data;
}

export async function listTests(): Promise<Test[]> {
  const { data } = await apiClient.get<Paginated<Test>>("/v1/catalog/tests/");
  return unwrap(data);
}

export async function getTest(id: string): Promise<Test> {
  const { data } = await apiClient.get<Test>(`/v1/catalog/tests/${id}/`);
  return data;
}

export async function createTest(body: TestWriteBody): Promise<Test> {
  const { data } = await apiClient.post<Test>("/v1/catalog/tests/", body);
  return data;
}

export async function updateTest(id: string, body: Partial<TestWriteBody>): Promise<Test> {
  const { data } = await apiClient.patch<Test>(`/v1/catalog/tests/${id}/`, body);
  return data;
}

export async function deleteTest(id: string): Promise<void> {
  await apiClient.delete(`/v1/catalog/tests/${id}/`);
}

export type TestCategoryOption = { id: string; code: string; name: string };

export async function listCategories(): Promise<TestCategoryOption[]> {
  // Derive distinct categories from the tests endpoint until a dedicated route exists.
  const tests = await listTests();
  const map = new Map<string, TestCategoryOption>();
  for (const t of tests) {
    if (!map.has(t.category)) {
      map.set(t.category, { id: t.category, code: "", name: t.category_name });
    }
  }
  return Array.from(map.values()).sort((a, b) => a.name.localeCompare(b.name));
}

export async function createTemplate(body: TemplateWriteBody): Promise<TemplateDetail> {
  const { data } = await apiClient.post<TemplateDetail>("/v1/catalog/templates/", body);
  return data;
}

export async function updateTemplate(
  id: string,
  body: Partial<TemplateWriteBody>,
): Promise<TemplateDetail> {
  const { data } = await apiClient.patch<TemplateDetail>(`/v1/catalog/templates/${id}/`, body);
  return data;
}

export async function deleteTemplate(id: string): Promise<void> {
  await apiClient.delete(`/v1/catalog/templates/${id}/`);
}

export async function cloneTemplate(
  id: string,
  body: { name?: string; code?: string } = {},
): Promise<TemplateDetail> {
  const { data } = await apiClient.post<TemplateDetail>(`/v1/catalog/templates/${id}/clone/`, body);
  return data;
}

// ─────────────────────────────────────────────────────────────────────────
// Packages (admin-only test bundles with discounted pricing)
// ─────────────────────────────────────────────────────────────────────────

export type PackageSummary = {
  id: string;
  code: string;
  name: string;
  name_alt: string;
  description: string;
  list_price: string;
  offer_price: string;
  is_active: boolean;
  display_order: number;
  template_count: number;
};

export type PackageMember = {
  id: string;
  template: string;
  template_code: string;
  template_name: string;
  display_order: number;
};

export type PackageDetail = Omit<PackageSummary, "template_count"> & {
  package_templates: PackageMember[];
  is_system: boolean;
  is_editable: boolean;
};

export type PackageWriteBody = {
  code: string;
  name: string;
  name_alt?: string;
  description?: string;
  list_price: string | number;
  offer_price: string | number;
  is_active?: boolean;
  display_order?: number;
  template_ids: string[];
};

export async function listPackages(): Promise<PackageSummary[]> {
  const { data } = await apiClient.get<Paginated<PackageSummary>>("/v1/catalog/packages/");
  return unwrap(data);
}

export async function getPackage(id: string): Promise<PackageDetail> {
  const { data } = await apiClient.get<PackageDetail>(`/v1/catalog/packages/${id}/`);
  return data;
}

export async function createPackage(body: PackageWriteBody): Promise<PackageDetail> {
  const { data } = await apiClient.post<PackageDetail>("/v1/catalog/packages/", body);
  return data;
}

export async function updatePackage(id: string, body: Partial<PackageWriteBody>): Promise<PackageDetail> {
  const { data } = await apiClient.patch<PackageDetail>(`/v1/catalog/packages/${id}/`, body);
  return data;
}

export async function deletePackage(id: string): Promise<void> {
  await apiClient.delete(`/v1/catalog/packages/${id}/`);
}
