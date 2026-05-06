import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  cloneTemplate,
  createTemplate,
  createTest,
  deleteTemplate,
  deleteTest,
  getTemplate,
  listCategories,
  listTemplates,
  listTests,
  updateTemplate,
  updateTest,
  type Test,
  type TemplateDetail,
  type TestWriteBody,
  type TestWriteRange,
} from "@/api/catalog";
import { cachedUser } from "@/api/auth";
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

function deriveCode(name: string): string {
  const cleaned = name.trim().toUpperCase();
  if (!cleaned) return "";
  const words = cleaned.split(/\s+/).filter(Boolean);
  if (words.length === 1) return words[0].slice(0, 8).replace(/[^A-Z0-9]/g, "");
  return words
    .map((w) => w[0])
    .join("")
    .replace(/[^A-Z0-9]/g, "")
    .slice(0, 8);
}

type EditorMode = { kind: "create" } | { kind: "edit"; template: TemplateDetail };
type TestEditorMode = { kind: "create" } | { kind: "edit"; test: Test };

export default function CatalogPage() {
  const queryClient = useQueryClient();
  const user = cachedUser();
  const canManage = !!user && (user.is_superuser || user.role_code === "admin" || user.role_code === "lab_owner");

  const { data: templates } = useQuery({ queryKey: ["templates"], queryFn: listTemplates });
  const [tab, setTab] = useState<"templates" | "tests">("templates");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [search, setSearch] = useState("");
  const [allTestsSearch, setAllTestsSearch] = useState("");
  const [editor, setEditor] = useState<EditorMode | null>(null);
  const [confirmDelete, setConfirmDelete] = useState<TemplateDetail | null>(null);
  const [testEditor, setTestEditor] = useState<TestEditorMode | null>(null);
  const [confirmDeleteTest, setConfirmDeleteTest] = useState<Test | null>(null);
  const [deleteTestError, setDeleteTestError] = useState<string | null>(null);

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

  const cloneMutation = useMutation({
    mutationFn: (id: string) => cloneTemplate(id),
    onSuccess: (created) => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      setSelectedId(created.id);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteTemplate(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["templates"] });
      setConfirmDelete(null);
      setSelectedId(null);
    },
  });

  const deleteTestMutation = useMutation({
    mutationFn: (id: string) => deleteTest(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["catalog-tests"] });
      if (selectedId) queryClient.invalidateQueries({ queryKey: ["template-detail", selectedId] });
      setConfirmDeleteTest(null);
      setDeleteTestError(null);
    },
    onError: (err: any) => {
      setDeleteTestError(err?.response?.data?.detail ?? "Could not delete test.");
    },
  });

  return (
    <div className="flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-on-primary-fixed tracking-tight mb-3">
            Laboratory Catalog
          </h1>
          <div className="flex items-center gap-1 bg-surface-container-low p-1 rounded-lg w-fit ring-1 ring-outline-variant/15">
            <button
              onClick={() => setTab("templates")}
              className={
                tab === "templates"
                  ? "px-5 py-2 rounded-lg bg-surface-container-lowest text-primary-container font-semibold text-sm shadow-sm transition-all"
                  : "px-5 py-2 rounded-lg text-on-surface-variant/80 font-medium text-sm hover:text-on-primary-fixed transition-all"
              }
            >
              Report Templates
            </button>
            <button
              onClick={() => setTab("tests")}
              className={
                tab === "tests"
                  ? "px-5 py-2 rounded-lg bg-surface-container-lowest text-primary-container font-semibold text-sm shadow-sm transition-all"
                  : "px-5 py-2 rounded-lg text-on-surface-variant/80 font-medium text-sm hover:text-on-primary-fixed transition-all"
              }
            >
              All Tests
            </button>
          </div>
        </div>
        {canManage && (
          <div className="flex items-center gap-2">
            <button
              onClick={() => setTestEditor({ kind: "create" })}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-secondary-container text-on-secondary-container font-semibold text-sm shadow-sm hover:opacity-90 transition-opacity"
            >
              <Icon name="biotech" size={18} />
              New Test
            </button>
            <button
              onClick={() => setEditor({ kind: "create" })}
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-primary-container text-on-primary-container font-semibold text-sm shadow-sm hover:opacity-90 transition-opacity"
            >
              <Icon name="add" size={18} />
              New Template
            </button>
          </div>
        )}
      </div>

      {tab === "tests" && (
        <AllTestsView
          search={allTestsSearch}
          onSearch={setAllTestsSearch}
          canManage={canManage}
          onEdit={(t) => setTestEditor({ kind: "edit", test: t })}
          onDelete={(t) => {
            setDeleteTestError(null);
            setConfirmDeleteTest(t);
          }}
        />
      )}

      {tab === "templates" && (
      <main className="flex flex-col lg:flex-row gap-6">
        {/* Left sidebar */}
        <aside className="w-full lg:w-[28rem] shrink-0 bg-surface-container-low rounded-xl p-4 flex flex-col ring-1 ring-outline-variant/10 h-fit max-h-[calc(100vh-200px)]">
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
            {!templates && <div className="text-on-surface-variant text-sm p-3">Loading…</div>}
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
                    <span className={active ? "font-bold truncate" : "font-medium truncate"}>
                      {t.name}
                    </span>
                  </div>
                  <span className="text-xs font-mono opacity-70">{t.code}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        {/* Right pane */}
        <div className="flex-1 min-w-0 bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 overflow-hidden flex flex-col">
          <div className="p-5 flex items-center justify-between border-b border-outline-variant/10 gap-4">
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
                  {detail?.is_system && (
                    <span className="text-[11px] uppercase tracking-wider px-2 py-0.5 rounded-full bg-tertiary-container text-on-tertiary-container font-semibold">
                      System
                    </span>
                  )}
                </>
              )}
            </div>
            <div className="flex items-center gap-2">
              {detail && (
                <span className="text-sm text-on-surface-variant whitespace-nowrap">
                  {detail.template_tests.length} tests
                </span>
              )}
              {canManage && detail && detail.is_editable && (
                <>
                  <button
                    onClick={() => setEditor({ kind: "edit", template: detail })}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm bg-secondary-container text-on-secondary-container hover:opacity-90"
                  >
                    <Icon name="edit" size={16} /> Edit
                  </button>
                  <button
                    onClick={() => setConfirmDelete(detail)}
                    className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm bg-error-container text-on-error-container hover:opacity-90"
                  >
                    <Icon name="delete" size={16} /> Delete
                  </button>
                </>
              )}
              {canManage && detail && (
                <button
                  onClick={() => cloneMutation.mutate(detail.id)}
                  disabled={cloneMutation.isPending}
                  className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm bg-surface-container-high text-on-surface hover:bg-surface-container-highest disabled:opacity-50"
                >
                  <Icon name="content_copy" size={16} /> Clone
                </button>
              )}
            </div>
          </div>

          {!selectedId && (
            <div className="flex-1 flex flex-col items-center justify-center p-12 text-center">
              <Icon name="fact_check" size={48} className="text-outline-variant mb-3" />
              <h4 className="text-on-primary-fixed font-semibold text-lg">Browse a template</h4>
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
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase w-24">Code</th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase">Test Name</th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase">Category</th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase">Specimen</th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase w-24">Unit</th>
                    <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase">Ref. Range</th>
                    {canManage && <th className="px-3 py-3 text-xs font-semibold tracking-wide uppercase w-32"></th>}
                  </tr>
                </thead>
                <tbody className="text-sm text-on-surface">
                  {detail.template_tests.map((tt, i) => {
                    const t = tt.test;
                    const range = t.reference_ranges.find((r) => r.sex === "A") ?? t.reference_ranges[0];
                    return (
                      <tr
                        key={tt.id}
                        className={`${
                          i % 2 === 0 ? "bg-surface" : "bg-surface-container-lowest"
                        } hover:bg-surface-container-high transition-colors group`}
                      >
                        <td className="px-4 py-2.5 font-mono text-primary-container font-medium text-[13px]">
                          {t.code}
                        </td>
                        <td className="px-4 py-2.5">
                          <div className="font-semibold text-on-primary-fixed">{t.name}</div>
                          {t.method && (
                            <div className="text-[11px] text-on-surface-variant mt-0.5">{t.method}</div>
                          )}
                        </td>
                        <td className="px-4 py-2.5 text-on-surface-variant">{t.category_name || "—"}</td>
                        <td className="px-4 py-2.5 text-on-surface-variant">{t.sample_type || "—"}</td>
                        <td className="px-4 py-2.5 text-on-surface-variant font-mono">{t.unit || "—"}</td>
                        <td className="px-4 py-2.5 text-on-surface-variant font-mono text-[12px]">
                          {range?.display ? (
                            range.display
                          ) : (
                            <span className="italic text-outline">Age/Gender specific</span>
                          )}
                        </td>
                        {canManage && (
                          <td className="px-3 py-2.5 text-right whitespace-nowrap">
                            <button
                              onClick={() => setTestEditor({ kind: "edit", test: t })}
                              className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-secondary-container text-on-secondary-container hover:opacity-90"
                              title="Edit test"
                            >
                              <Icon name="edit" size={14} /> Edit
                            </button>
                            <button
                              onClick={() => {
                                setDeleteTestError(null);
                                setConfirmDeleteTest(t);
                              }}
                              className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-1 px-2 py-1 ml-1 rounded text-xs bg-error-container text-on-error-container hover:opacity-90"
                              title="Delete test"
                            >
                              <Icon name="delete" size={14} />
                            </button>
                          </td>
                        )}
                      </tr>
                    );
                  })}
                  {detail.template_tests.length === 0 && (
                    <tr>
                      <td colSpan={6} className="px-4 py-12 text-center text-on-surface-variant text-sm">
                        No tests in this template yet. Click <b>Edit</b> to add some.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </main>
      )}

      {editor && (
        <TemplateEditor
          mode={editor}
          onClose={() => setEditor(null)}
          onSaved={(saved) => {
            setEditor(null);
            queryClient.invalidateQueries({ queryKey: ["templates"] });
            queryClient.invalidateQueries({ queryKey: ["template-detail", saved.id] });
            setSelectedId(saved.id);
          }}
        />
      )}

      {confirmDelete && (
        <ConfirmDialog
          title="Delete template?"
          message={`"${confirmDelete.name}" will be removed. This cannot be undone from the UI.`}
          confirmLabel="Delete"
          confirmVariant="danger"
          loading={deleteMutation.isPending}
          onCancel={() => setConfirmDelete(null)}
          onConfirm={() => deleteMutation.mutate(confirmDelete.id)}
        />
      )}

      {testEditor && (
        <TestEditor
          mode={testEditor}
          onClose={() => setTestEditor(null)}
          onSaved={() => {
            setTestEditor(null);
            queryClient.invalidateQueries({ queryKey: ["catalog-tests"] });
            if (selectedId) queryClient.invalidateQueries({ queryKey: ["template-detail", selectedId] });
          }}
        />
      )}

      {confirmDeleteTest && (
        <ConfirmDialog
          title="Delete test?"
          message={
            deleteTestError ??
            `"${confirmDeleteTest.name}" will be removed. If it's used by any template, the delete will be blocked.`
          }
          confirmLabel="Delete"
          confirmVariant="danger"
          loading={deleteTestMutation.isPending}
          onCancel={() => {
            setConfirmDeleteTest(null);
            setDeleteTestError(null);
          }}
          onConfirm={() => deleteTestMutation.mutate(confirmDeleteTest.id)}
        />
      )}
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Template editor modal — handles create + edit
// ────────────────────────────────────────────────────────────────────────────
function TemplateEditor({
  mode,
  onClose,
  onSaved,
}: {
  mode: EditorMode;
  onClose: () => void;
  onSaved: (saved: TemplateDetail) => void;
}) {
  const isEdit = mode.kind === "edit";
  const initial = isEdit ? mode.template : null;

  const [name, setName] = useState(initial?.name ?? "");
  const [codeTouched, setCodeTouched] = useState(isEdit);
  const [code, setCode] = useState(initial?.code ?? "");
  const [description, setDescription] = useState(initial?.description ?? "");
  const [selectedIds, setSelectedIds] = useState<string[]>(
    initial ? initial.template_tests.map((tt) => tt.test.id) : [],
  );
  const [testSearch, setTestSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  const { data: tests } = useQuery({ queryKey: ["catalog-tests"], queryFn: listTests });

  useEffect(() => {
    if (!codeTouched) setCode(deriveCode(name));
  }, [name, codeTouched]);

  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const selectedTests = useMemo(() => {
    if (!tests) return [];
    const byId = new Map(tests.map((t) => [t.id, t]));
    return selectedIds.map((id) => byId.get(id)).filter((t): t is Test => !!t);
  }, [tests, selectedIds]);

  const groupedAvailable = useMemo(() => {
    if (!tests) return [] as Array<{ category: string; tests: Test[] }>;
    const q = testSearch.trim().toLowerCase();
    const filtered = tests.filter(
      (t) =>
        !selectedSet.has(t.id) &&
        (q === "" ||
          t.name.toLowerCase().includes(q) ||
          t.code.toLowerCase().includes(q) ||
          (t.category_name || "").toLowerCase().includes(q)),
    );
    const map = new Map<string, Test[]>();
    for (const t of filtered) {
      const key = t.category_name || "Uncategorized";
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(t);
    }
    return Array.from(map.entries())
      .map(([category, ts]) => ({ category, tests: ts }))
      .sort((a, b) => a.category.localeCompare(b.category));
  }, [tests, selectedSet, testSearch]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const body = {
        name: name.trim(),
        code: code.trim().toUpperCase(),
        description: description.trim(),
        test_ids: selectedIds,
      };
      if (mode.kind === "edit") return updateTemplate(mode.template.id, body);
      return createTemplate(body);
    },
    onSuccess: onSaved,
    onError: (err: any) => {
      const data = err?.response?.data;
      if (typeof data === "string") setError(data);
      else if (data?.detail) setError(data.detail);
      else if (data) setError(Object.values(data).flat().join(" "));
      else setError("Save failed.");
    },
  });

  function add(id: string) {
    setSelectedIds((cur) => (cur.includes(id) ? cur : [...cur, id]));
  }
  function remove(id: string) {
    setSelectedIds((cur) => cur.filter((x) => x !== id));
  }
  function move(id: string, dir: -1 | 1) {
    setSelectedIds((cur) => {
      const i = cur.indexOf(id);
      const j = i + dir;
      if (i < 0 || j < 0 || j >= cur.length) return cur;
      const next = cur.slice();
      [next[i], next[j]] = [next[j], next[i]];
      return next;
    });
  }

  const canSave = name.trim().length > 0 && code.trim().length > 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-5xl max-h-[92vh] bg-surface-container-lowest rounded-2xl shadow-2xl flex flex-col overflow-hidden ring-1 ring-outline-variant/20">
        <div className="px-6 py-4 border-b border-outline-variant/15 flex items-center justify-between">
          <h2 className="text-xl font-bold text-on-primary-fixed">
            {isEdit ? "Edit Template" : "New Template"}
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-surface-container-highest text-on-surface-variant"
          >
            <Icon name="close" size={20} />
          </button>
        </div>

        <div className="px-6 py-4 grid grid-cols-1 md:grid-cols-3 gap-4 border-b border-outline-variant/15">
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
              Name *
            </label>
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Liver Function Test"
              className="mt-1 w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md text-sm focus:bg-surface-container-lowest focus:border-secondary outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
              Code *
            </label>
            <input
              value={code}
              onChange={(e) => {
                setCode(e.target.value.toUpperCase());
                setCodeTouched(true);
              }}
              placeholder="LFT"
              className="mt-1 w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md text-sm font-mono focus:bg-surface-container-lowest focus:border-secondary outline-none"
            />
          </div>
          <div>
            <label className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">
              Description
            </label>
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional"
              className="mt-1 w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md text-sm focus:bg-surface-container-lowest focus:border-secondary outline-none"
            />
          </div>
        </div>

        {/* Two-pane test picker */}
        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-0 min-h-0">
          {/* Available */}
          <div className="flex flex-col min-h-0 border-r border-outline-variant/15">
            <div className="px-5 pt-4 pb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-on-primary-fixed">Available Tests</h3>
              <span className="text-xs text-on-surface-variant">
                {tests ? tests.length - selectedIds.length : 0} available
              </span>
            </div>
            <div className="px-5 pb-2">
              <input
                value={testSearch}
                onChange={(e) => setTestSearch(e.target.value)}
                placeholder="Search tests by name, code, or category…"
                className="w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2 rounded-md text-sm focus:bg-surface-container-lowest focus:border-secondary outline-none"
              />
            </div>
            <div className="flex-1 overflow-auto px-3 pb-3">
              {!tests && <div className="p-3 text-sm text-on-surface-variant">Loading tests…</div>}
              {groupedAvailable.map((g) => (
                <div key={g.category} className="mb-3">
                  <div className="text-[11px] uppercase tracking-wider font-bold text-on-surface-variant px-2 py-1">
                    {g.category}
                  </div>
                  <div className="flex flex-col gap-0.5">
                    {g.tests.map((t) => (
                      <button
                        key={t.id}
                        onClick={() => add(t.id)}
                        className="text-left px-2 py-1.5 rounded hover:bg-surface-container-high group flex items-center justify-between"
                      >
                        <div className="min-w-0">
                          <div className="text-sm text-on-surface truncate">{t.name}</div>
                          <div className="text-[11px] font-mono text-on-surface-variant">{t.code}</div>
                        </div>
                        <Icon
                          name="add"
                          size={18}
                          className="text-on-surface-variant opacity-0 group-hover:opacity-100"
                        />
                      </button>
                    ))}
                  </div>
                </div>
              ))}
              {tests && groupedAvailable.length === 0 && (
                <div className="p-6 text-center text-sm text-on-surface-variant">
                  No tests match "{testSearch}".
                </div>
              )}
            </div>
          </div>

          {/* Selected */}
          <div className="flex flex-col min-h-0">
            <div className="px-5 pt-4 pb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-on-primary-fixed">
                Selected Tests <span className="text-on-surface-variant font-normal">(in order)</span>
              </h3>
              <span className="text-xs text-on-surface-variant">{selectedIds.length} selected</span>
            </div>
            <div className="flex-1 overflow-auto px-3 pb-3">
              {selectedTests.length === 0 && (
                <div className="p-8 text-center text-sm text-on-surface-variant">
                  Click tests on the left to add them here.
                </div>
              )}
              {selectedTests.map((t, i) => (
                <div
                  key={t.id}
                  className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-surface-container-high"
                >
                  <span className="text-xs font-mono w-6 text-on-surface-variant">{i + 1}.</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-on-surface truncate">{t.name}</div>
                    <div className="text-[11px] font-mono text-on-surface-variant">
                      {t.code} · {t.category_name}
                    </div>
                  </div>
                  <div className="flex items-center gap-0.5">
                    <button
                      onClick={() => move(t.id, -1)}
                      disabled={i === 0}
                      className="p-1 rounded hover:bg-surface-container-highest text-on-surface-variant disabled:opacity-30"
                    >
                      <Icon name="arrow_upward" size={16} />
                    </button>
                    <button
                      onClick={() => move(t.id, 1)}
                      disabled={i === selectedTests.length - 1}
                      className="p-1 rounded hover:bg-surface-container-highest text-on-surface-variant disabled:opacity-30"
                    >
                      <Icon name="arrow_downward" size={16} />
                    </button>
                    <button
                      onClick={() => remove(t.id)}
                      className="p-1 rounded hover:bg-error-container text-error"
                    >
                      <Icon name="close" size={16} />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {error && (
          <div className="px-6 py-2 bg-error-container text-on-error-container text-sm">{error}</div>
        )}
        <div className="px-6 py-4 border-t border-outline-variant/15 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container-highest"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              setError(null);
              saveMutation.mutate();
            }}
            disabled={!canSave || saveMutation.isPending}
            className="px-5 py-2 rounded-lg text-sm font-semibold bg-primary-container text-on-primary-container hover:opacity-90 disabled:opacity-50"
          >
            {saveMutation.isPending ? "Saving…" : isEdit ? "Save Changes" : "Create Template"}
          </button>
        </div>
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// All Tests view — flat list grouped by category with search + edit/delete
// ────────────────────────────────────────────────────────────────────────────
function AllTestsView({
  search,
  onSearch,
  canManage,
  onEdit,
  onDelete,
}: {
  search: string;
  onSearch: (v: string) => void;
  canManage: boolean;
  onEdit: (t: Test) => void;
  onDelete: (t: Test) => void;
}) {
  const { data: tests } = useQuery({ queryKey: ["catalog-tests"], queryFn: listTests });

  const grouped = useMemo(() => {
    if (!tests) return [] as Array<{ category: string; tests: Test[] }>;
    const q = search.trim().toLowerCase();
    const filtered = tests.filter(
      (t) =>
        q === "" ||
        t.name.toLowerCase().includes(q) ||
        t.code.toLowerCase().includes(q) ||
        (t.category_name || "").toLowerCase().includes(q),
    );
    const map = new Map<string, Test[]>();
    for (const t of filtered) {
      const key = t.category_name || "Uncategorized";
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(t);
    }
    return Array.from(map.entries())
      .map(([category, ts]) => ({ category, tests: ts }))
      .sort((a, b) => a.category.localeCompare(b.category));
  }, [tests, search]);

  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 overflow-hidden">
      <div className="p-4 flex items-center justify-between border-b border-outline-variant/10 gap-4">
        <div className="relative flex-1 max-w-md">
          <Icon
            name="search"
            size={18}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant"
          />
          <input
            value={search}
            onChange={(e) => onSearch(e.target.value)}
            placeholder="Search tests by name, code, or category…"
            className="w-full bg-surface-container-highest text-on-surface text-sm rounded-lg pl-9 pr-3 py-2 ring-1 ring-outline-variant/15 focus:bg-surface-container-lowest focus:ring-secondary focus:outline-none transition-all"
          />
        </div>
        <span className="text-sm text-on-surface-variant whitespace-nowrap">
          {tests ? `${tests.length} tests` : "Loading…"}
        </span>
      </div>

      <div className="max-h-[calc(100vh-260px)] overflow-auto">
        {grouped.map((g) => (
          <div key={g.category}>
            <div className="sticky top-0 z-10 bg-primary-container text-on-primary px-4 py-2 text-xs font-bold uppercase tracking-wider">
              {g.category} <span className="opacity-70 font-normal">({g.tests.length})</span>
            </div>
            <table className="w-full text-left border-collapse">
              <tbody className="text-sm text-on-surface">
                {g.tests.map((t, i) => {
                  const range = t.reference_ranges.find((r) => r.sex === "A") ?? t.reference_ranges[0];
                  return (
                    <tr
                      key={t.id}
                      className={`${
                        i % 2 === 0 ? "bg-surface" : "bg-surface-container-lowest"
                      } hover:bg-surface-container-high transition-colors group`}
                    >
                      <td className="px-4 py-2.5 font-mono text-primary-container font-medium text-[13px] w-28">
                        {t.code}
                      </td>
                      <td className="px-4 py-2.5">
                        <div className="font-semibold text-on-primary-fixed">{t.name}</div>
                        {t.method && (
                          <div className="text-[11px] text-on-surface-variant mt-0.5">{t.method}</div>
                        )}
                      </td>
                      <td className="px-4 py-2.5 text-on-surface-variant">{t.sample_type || "—"}</td>
                      <td className="px-4 py-2.5 text-on-surface-variant font-mono w-24">{t.unit || "—"}</td>
                      <td className="px-4 py-2.5 text-on-surface-variant font-mono text-[12px]">
                        {range?.display ? (
                          range.display
                        ) : (
                          <span className="italic text-outline">Age/Gender specific</span>
                        )}
                      </td>
                      {canManage && (
                        <td className="px-3 py-2.5 text-right whitespace-nowrap w-32">
                          <button
                            onClick={() => onEdit(t)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-secondary-container text-on-secondary-container hover:opacity-90"
                          >
                            <Icon name="edit" size={14} /> Edit
                          </button>
                          <button
                            onClick={() => onDelete(t)}
                            className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-1 px-2 py-1 ml-1 rounded text-xs bg-error-container text-on-error-container hover:opacity-90"
                          >
                            <Icon name="delete" size={14} />
                          </button>
                        </td>
                      )}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ))}
        {tests && grouped.length === 0 && (
          <div className="p-12 text-center text-on-surface-variant">No tests match "{search}".</div>
        )}
      </div>
    </div>
  );
}

// ────────────────────────────────────────────────────────────────────────────
// Test editor modal — handles create + edit (details + reference ranges)
// ────────────────────────────────────────────────────────────────────────────
type RangeRow = {
  sex: "M" | "F" | "A";
  age_min_years: string;
  age_max_years: string;
  range_min: string;
  range_max: string;
  range_text: string;
  critical_low: string;
  critical_high: string;
  unit_override: string;
  note: string;
};

function emptyRange(): RangeRow {
  return {
    sex: "A",
    age_min_years: "",
    age_max_years: "",
    range_min: "",
    range_max: "",
    range_text: "",
    critical_low: "",
    critical_high: "",
    unit_override: "",
    note: "",
  };
}

function rangeToRow(r: Test["reference_ranges"][number]): RangeRow {
  return {
    sex: r.sex,
    age_min_years: r.age_min_years?.toString() ?? "",
    age_max_years: r.age_max_years?.toString() ?? "",
    range_min: r.range_min?.toString() ?? "",
    range_max: r.range_max?.toString() ?? "",
    range_text: r.range_text ?? "",
    critical_low: r.critical_low?.toString() ?? "",
    critical_high: r.critical_high?.toString() ?? "",
    unit_override: r.unit_override ?? "",
    note: r.note ?? "",
  };
}

function rowToWrite(r: RangeRow): TestWriteRange {
  const num = (s: string) => (s.trim() === "" ? null : s.trim());
  const intNum = (s: string) => (s.trim() === "" ? null : Number.parseInt(s.trim(), 10));
  return {
    sex: r.sex,
    age_min_years: intNum(r.age_min_years),
    age_max_years: intNum(r.age_max_years),
    range_min: num(r.range_min),
    range_max: num(r.range_max),
    range_text: r.range_text,
    critical_low: num(r.critical_low),
    critical_high: num(r.critical_high),
    unit_override: r.unit_override,
    note: r.note,
  };
}

function TestEditor({
  mode,
  onClose,
  onSaved,
}: {
  mode: TestEditorMode;
  onClose: () => void;
  onSaved: (saved: Test) => void;
}) {
  const isEdit = mode.kind === "edit";
  const initial = isEdit ? mode.test : null;

  const [name, setName] = useState(initial?.name ?? "");
  const [code, setCode] = useState(initial?.code ?? "");
  const [shortName, setShortName] = useState(initial?.short_name ?? "");
  const [categoryId, setCategoryId] = useState(initial?.category ?? "");
  const [sampleType, setSampleType] = useState(initial?.sample_type ?? "");
  const [method, setMethod] = useState(initial?.method ?? "");
  const [unit, setUnit] = useState(initial?.unit ?? "");
  const [decimalPlaces, setDecimalPlaces] = useState((initial?.decimal_places ?? 2).toString());
  const [clinicalSignificance, setClinicalSignificance] = useState(initial?.clinical_significance ?? "");
  const [ranges, setRanges] = useState<RangeRow[]>(
    initial && initial.reference_ranges.length
      ? initial.reference_ranges.map(rangeToRow)
      : [emptyRange()],
  );
  const [error, setError] = useState<string | null>(null);

  const { data: categories } = useQuery({ queryKey: ["catalog-categories"], queryFn: listCategories });

  // For new tests, default to first category once loaded.
  useEffect(() => {
    if (!isEdit && !categoryId && categories && categories.length) {
      setCategoryId(categories[0].id);
    }
  }, [isEdit, categoryId, categories]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const body: TestWriteBody = {
        code: code.trim().toUpperCase(),
        name: name.trim(),
        short_name: shortName.trim(),
        category: categoryId,
        sample_type: sampleType.trim(),
        method: method.trim(),
        unit: unit.trim(),
        decimal_places: Number.parseInt(decimalPlaces, 10) || 0,
        clinical_significance: clinicalSignificance.trim(),
        reference_ranges: ranges.map(rowToWrite),
      };
      if (mode.kind === "edit") return updateTest(mode.test.id, body);
      return createTest(body);
    },
    onSuccess: onSaved,
    onError: (err: any) => {
      const data = err?.response?.data;
      if (typeof data === "string") setError(data);
      else if (data?.detail) setError(data.detail);
      else if (data) setError(Object.values(data).flat().join(" "));
      else setError("Save failed.");
    },
  });

  const canSave = name.trim().length > 0 && code.trim().length > 0 && categoryId;

  function updateRange(i: number, patch: Partial<RangeRow>) {
    setRanges((cur) => cur.map((r, idx) => (idx === i ? { ...r, ...patch } : r)));
  }
  function addRange() {
    setRanges((cur) => [...cur, emptyRange()]);
  }
  function removeRange(i: number) {
    setRanges((cur) => cur.filter((_, idx) => idx !== i));
  }

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-4xl max-h-[92vh] bg-surface-container-lowest rounded-2xl shadow-2xl flex flex-col overflow-hidden ring-1 ring-outline-variant/20">
        <div className="px-6 py-4 border-b border-outline-variant/15 flex items-center justify-between">
          <h2 className="text-xl font-bold text-on-primary-fixed">
            {isEdit ? "Edit Test" : "New Test"}
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-surface-container-highest text-on-surface-variant"
          >
            <Icon name="close" size={20} />
          </button>
        </div>

        <div className="flex-1 overflow-auto px-6 py-4 space-y-5">
          {/* Details */}
          <section>
            <h3 className="text-sm font-semibold text-on-primary-fixed mb-2">Details</h3>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <Field label="Name *">
                <input
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  placeholder="e.g. Total Cholesterol"
                  className={inputCls}
                />
              </Field>
              <Field label="Code *">
                <input
                  value={code}
                  onChange={(e) => setCode(e.target.value.toUpperCase())}
                  placeholder="LIPID-CHOL"
                  className={inputCls + " font-mono"}
                />
              </Field>
              <Field label="Short Name">
                <input
                  value={shortName}
                  onChange={(e) => setShortName(e.target.value)}
                  placeholder="T.Chol"
                  className={inputCls}
                />
              </Field>
              <Field label="Category *">
                <select
                  value={categoryId}
                  onChange={(e) => setCategoryId(e.target.value)}
                  className={inputCls}
                >
                  <option value="">— pick a category —</option>
                  {categories?.map((c) => (
                    <option key={c.id} value={c.id}>
                      {c.name}
                    </option>
                  ))}
                </select>
              </Field>
              <Field label="Sample Type">
                <input
                  value={sampleType}
                  onChange={(e) => setSampleType(e.target.value)}
                  placeholder="Serum / EDTA"
                  className={inputCls}
                />
              </Field>
              <Field label="Method">
                <input
                  value={method}
                  onChange={(e) => setMethod(e.target.value)}
                  placeholder="CHOD-PAP / HPLC"
                  className={inputCls}
                />
              </Field>
              <Field label="Unit">
                <input
                  value={unit}
                  onChange={(e) => setUnit(e.target.value)}
                  placeholder="mg/dL"
                  className={inputCls + " font-mono"}
                />
              </Field>
              <Field label="Decimal Places">
                <input
                  type="number"
                  min={0}
                  max={6}
                  value={decimalPlaces}
                  onChange={(e) => setDecimalPlaces(e.target.value)}
                  className={inputCls}
                />
              </Field>
              <div className="md:col-span-3">
                <Field label="Clinical Significance">
                  <textarea
                    value={clinicalSignificance}
                    onChange={(e) => setClinicalSignificance(e.target.value)}
                    rows={2}
                    placeholder="Optional — printed on the report under Clinical Significance."
                    className={inputCls + " resize-y min-h-[60px]"}
                  />
                </Field>
              </div>
            </div>
          </section>

          {/* Reference ranges */}
          <section>
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-semibold text-on-primary-fixed">Reference Ranges</h3>
              <button
                onClick={addRange}
                className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs bg-secondary-container text-on-secondary-container hover:opacity-90"
              >
                <Icon name="add" size={14} /> Add range
              </button>
            </div>
            <div className="overflow-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="text-[11px] uppercase tracking-wider text-on-surface-variant">
                    <th className="text-left px-2 py-1 w-20">Sex</th>
                    <th className="text-left px-2 py-1 w-24">Age min</th>
                    <th className="text-left px-2 py-1 w-24">Age max</th>
                    <th className="text-left px-2 py-1">Range min</th>
                    <th className="text-left px-2 py-1">Range max</th>
                    <th className="text-left px-2 py-1">Range text</th>
                    <th className="text-left px-2 py-1">Crit low</th>
                    <th className="text-left px-2 py-1">Crit high</th>
                    <th className="text-left px-2 py-1">Note</th>
                    <th className="px-2 py-1 w-8"></th>
                  </tr>
                </thead>
                <tbody>
                  {ranges.map((r, i) => (
                    <tr key={i} className="border-t border-outline-variant/15">
                      <td className="px-1 py-1">
                        <select
                          value={r.sex}
                          onChange={(e) => updateRange(i, { sex: e.target.value as RangeRow["sex"] })}
                          className={cellCls}
                        >
                          <option value="A">All</option>
                          <option value="M">Male</option>
                          <option value="F">Female</option>
                        </select>
                      </td>
                      <td className="px-1 py-1">
                        <input
                          value={r.age_min_years}
                          onChange={(e) => updateRange(i, { age_min_years: e.target.value })}
                          placeholder="—"
                          className={cellCls}
                        />
                      </td>
                      <td className="px-1 py-1">
                        <input
                          value={r.age_max_years}
                          onChange={(e) => updateRange(i, { age_max_years: e.target.value })}
                          placeholder="—"
                          className={cellCls}
                        />
                      </td>
                      <td className="px-1 py-1">
                        <input
                          value={r.range_min}
                          onChange={(e) => updateRange(i, { range_min: e.target.value })}
                          placeholder="—"
                          className={cellCls + " font-mono"}
                        />
                      </td>
                      <td className="px-1 py-1">
                        <input
                          value={r.range_max}
                          onChange={(e) => updateRange(i, { range_max: e.target.value })}
                          placeholder="—"
                          className={cellCls + " font-mono"}
                        />
                      </td>
                      <td className="px-1 py-1">
                        <input
                          value={r.range_text}
                          onChange={(e) => updateRange(i, { range_text: e.target.value })}
                          placeholder='e.g. "Non-reactive"'
                          className={cellCls}
                        />
                      </td>
                      <td className="px-1 py-1">
                        <input
                          value={r.critical_low}
                          onChange={(e) => updateRange(i, { critical_low: e.target.value })}
                          placeholder="—"
                          className={cellCls + " font-mono"}
                        />
                      </td>
                      <td className="px-1 py-1">
                        <input
                          value={r.critical_high}
                          onChange={(e) => updateRange(i, { critical_high: e.target.value })}
                          placeholder="—"
                          className={cellCls + " font-mono"}
                        />
                      </td>
                      <td className="px-1 py-1">
                        <input
                          value={r.note}
                          onChange={(e) => updateRange(i, { note: e.target.value })}
                          placeholder="Optional"
                          className={cellCls}
                        />
                      </td>
                      <td className="px-1 py-1 text-right">
                        <button
                          onClick={() => removeRange(i)}
                          className="p-1 rounded hover:bg-error-container text-error"
                          title="Remove range"
                        >
                          <Icon name="close" size={16} />
                        </button>
                      </td>
                    </tr>
                  ))}
                  {ranges.length === 0 && (
                    <tr>
                      <td colSpan={10} className="px-2 py-6 text-center text-on-surface-variant">
                        No reference ranges. Click <b>Add range</b> to define one.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
            <p className="text-[11px] text-on-surface-variant mt-2">
              Use either numeric (range min/max) or text (e.g. "Non-reactive") — leave the others blank. Use multiple
              rows for sex- or age-specific ranges.
            </p>
          </section>
        </div>

        {error && (
          <div className="px-6 py-2 bg-error-container text-on-error-container text-sm">{error}</div>
        )}
        <div className="px-6 py-4 border-t border-outline-variant/15 flex items-center justify-end gap-2">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container-highest"
          >
            Cancel
          </button>
          <button
            onClick={() => {
              setError(null);
              saveMutation.mutate();
            }}
            disabled={!canSave || saveMutation.isPending}
            className="px-5 py-2 rounded-lg text-sm font-semibold bg-primary-container text-on-primary-container hover:opacity-90 disabled:opacity-50"
          >
            {saveMutation.isPending ? "Saving…" : isEdit ? "Save Changes" : "Create Test"}
          </button>
        </div>
      </div>
    </div>
  );
}

const inputCls =
  "w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md text-sm focus:bg-surface-container-lowest focus:border-secondary outline-none";
const cellCls =
  "w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-1.5 rounded text-xs focus:bg-surface-container-lowest focus:border-secondary outline-none";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

function ConfirmDialog({
  title,
  message,
  confirmLabel,
  confirmVariant = "primary",
  loading,
  onConfirm,
  onCancel,
}: {
  title: string;
  message: string;
  confirmLabel: string;
  confirmVariant?: "primary" | "danger";
  loading?: boolean;
  onConfirm: () => void;
  onCancel: () => void;
}) {
  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-md bg-surface-container-lowest rounded-xl shadow-2xl ring-1 ring-outline-variant/20 p-6">
        <h3 className="text-lg font-bold text-on-primary-fixed">{title}</h3>
        <p className="text-sm text-on-surface-variant mt-2">{message}</p>
        <div className="mt-5 flex items-center justify-end gap-2">
          <button
            onClick={onCancel}
            className="px-4 py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container-highest"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={
              confirmVariant === "danger"
                ? "px-4 py-2 rounded-lg text-sm font-semibold bg-error-container text-on-error-container hover:opacity-90 disabled:opacity-50"
                : "px-4 py-2 rounded-lg text-sm font-semibold bg-primary-container text-on-primary-container hover:opacity-90 disabled:opacity-50"
            }
          >
            {loading ? "Working…" : confirmLabel}
          </button>
        </div>
      </div>
    </div>
  );
}
