import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { getTemplate, listTemplates } from "@/api/catalog";
import { Icon } from "@/components/ui/Icon";

const TEMPLATE_ICON: Record<string, string> = {
  CBC: "bloodtype",
  LFT: "science",
  KFT: "nephrology",
  TFT: "monitor_heart",
  URINE: "water_drop",
  LIPID: "water_drop",
  WIDAL: "biotech",
  DENGUE: "coronavirus",
  MALARIA: "bug_report",
};

function iconFor(code: string) {
  return TEMPLATE_ICON[code.toUpperCase()] ?? "science";
}

export default function CatalogPage() {
  const { data: templates } = useQuery({ queryKey: ["templates"], queryFn: listTemplates });
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");

  const { data: detail } = useQuery({
    queryKey: ["template-detail", selectedId],
    queryFn: () => getTemplate(selectedId!),
    enabled: !!selectedId,
  });

  const filtered = useMemo(() => {
    const list = templates ?? [];
    if (!search) return list;
    const q = search.toLowerCase();
    return list.filter(
      (t) => t.name.toLowerCase().includes(q) || t.code.toLowerCase().includes(q),
    );
  }, [templates, search]);

  const activeTemplate = templates?.find((t) => t.id === selectedId) ?? null;

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-on-primary-fixed tracking-tight mb-3">
            Laboratory Catalog
          </h1>
          <div className="flex items-center gap-1 bg-surface-container-low p-1 rounded-lg w-fit ring-1 ring-outline-variant/15">
            <button className="px-5 py-2 rounded-lg bg-surface-container-lowest text-primary-container font-semibold text-sm shadow-sm transition-all">
              Report Templates
            </button>
            <button
              disabled
              className="px-5 py-2 rounded-lg text-on-surface-variant/60 font-medium text-sm cursor-not-allowed"
              title="Coming soon"
            >
              Reference Ranges
            </button>
          </div>
        </div>
      </div>

      <main className="flex flex-col lg:flex-row gap-6">
        {/* Left sidebar — template list */}
        <aside className="w-full lg:w-80 shrink-0 bg-surface-container-low rounded-xl p-4 flex flex-col ring-1 ring-outline-variant/10 h-fit max-h-[calc(100vh-200px)]">
          <div className="relative mb-3 group">
            <Icon
              name="filter_list"
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant"
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Filter templates..."
              className="w-full bg-surface-container-highest text-on-surface text-sm rounded-lg pl-9 pr-3 py-2 ring-1 ring-outline-variant/15 focus:bg-surface-container-lowest focus:ring-secondary focus:outline-none transition-all placeholder:text-on-surface-variant/70"
            />
          </div>
          <div className="flex justify-between items-center mb-2 px-2">
            <span className="text-xs font-semibold text-on-surface-variant uppercase tracking-wider">
              Templates
            </span>
            <span className="text-xs bg-surface-container-highest text-on-surface-variant px-2 py-0.5 rounded-full font-medium">
              {filtered.length}
            </span>
          </div>
          <nav className="flex-1 overflow-y-auto flex flex-col gap-1 pr-1">
            {!templates && (
              <div className="text-on-surface-variant text-sm p-3">Loading…</div>
            )}
            {filtered.map((t) => {
              const active = t.id === selectedId;
              return (
                <button
                  key={t.id}
                  onClick={() => setSelectedId(t.id)}
                  className={
                    active
                      ? "w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm bg-surface-container-lowest shadow-sm text-primary-container text-left"
                      : "w-full flex items-center justify-between px-3 py-2.5 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container-highest transition-colors text-left group"
                  }
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <Icon
                      name={iconFor(t.code)}
                      size={18}
                      className={active ? "text-secondary" : "opacity-70"}
                    />
                    <span
                      className={active ? "font-bold truncate" : "font-medium truncate"}
                    >
                      {t.name}
                    </span>
                  </div>
                  <span className="text-xs font-mono opacity-70">{t.code}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Right — test ledger */}
        <div className="flex-1 min-w-0 bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 overflow-hidden flex flex-col">
          <div className="p-5 flex items-center justify-between border-b border-outline-variant/10">
            <div className="flex items-center gap-3 min-w-0">
              <h3 className="text-lg font-bold text-on-primary-fixed truncate">
                {activeTemplate ? activeTemplate.name : "Select a template"}
              </h3>
              {activeTemplate && (
                <>
                  <div className="h-4 w-px bg-outline-variant/30" />
                  <span className="text-sm text-on-surface-variant font-mono">
                    {activeTemplate.code}
                  </span>
                </>
              )}
            </div>
            {detail && (
              <span className="text-sm text-on-surface-variant whitespace-nowrap">
                {detail.template_tests.length} tests
              </span>
            )}
          </div>

          {!selectedId && (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
              <Icon
                name="fact_check"
                size={48}
                className="text-outline-variant mb-3"
              />
              <h4 className="text-on-primary-fixed font-semibold text-lg">
                Browse a template
              </h4>
              <p className="text-on-surface-variant text-sm mt-1 max-w-sm">
                Pick a report template from the left to see the included tests and their default
                reference ranges.
              </p>
            </div>
          )}

          {selectedId && detail && (
            <div className="flex-1 overflow-auto">
              <table className="w-full text-left border-collapse">
                <thead className="bg-primary-container text-on-primary sticky top-0 z-10">
                  <tr>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase w-24">
                      Code
                    </th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase">
                      Test Name
                    </th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase">
                      Category
                    </th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase">
                      Specimen
                    </th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase w-24">
                      Unit
                    </th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase">
                      Ref. Range
                    </th>
                  </tr>
                </thead>
                <tbody className="text-sm text-on-surface">
                  {detail.template_tests.map((tt, i) => {
                    const t = tt.test;
                    const range =
                      t.reference_ranges.find((r) => r.sex === "A") ??
                      t.reference_ranges[0];
                    return (
                      <tr
                        key={tt.id}
                        className={`${
                          i % 2 === 0 ? "bg-surface" : "bg-surface-container-lowest"
                        } hover:bg-surface-container-high transition-colors`}
                      >
                        <td className="px-4 py-2.5 font-mono text-primary-container font-medium text-[13px]">
                          {t.code}
                        </td>
                        <td className="px-4 py-2.5">
                          <div className="font-semibold text-on-primary-fixed">{t.name}</div>
                          {t.method && (
                            <div className="text-[11px] text-on-surface-variant mt-0.5">
                              {t.method}
                            </div>
                          )}
                        </td>
                        <td className="px-4 py-2.5 text-on-surface-variant">
                          {t.category_name || "—"}
                        </td>
                        <td className="px-4 py-2.5 text-on-surface-variant">
                          {t.sample_type || "—"}
                        </td>
                        <td className="px-4 py-2.5 text-on-surface-variant font-mono">
                          {t.unit || "—"}
                        </td>
                        <td className="px-4 py-2.5 text-on-surface-variant font-mono text-[12px]">
                          {range?.display ? (
                            range.display
                          ) : (
                            <span className="italic text-outline">Age/Gender specific</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
