import { apiClient } from "./client";

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
  reference_ranges: Array<{
    id: string;
    sex: "M" | "F" | "A";
    display: string;
  }>;
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
