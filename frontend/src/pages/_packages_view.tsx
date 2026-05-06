// Auxiliary file holding the Packages tab components for CatalogPage.
import { useEffect, useMemo, useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  createPackage,
  getPackage,
  listPackages,
  listTemplates,
  updatePackage,
  type PackageSummary,
} from "@/api/catalog";
import { Icon } from "@/components/ui/Icon";

const inputCls =
  "w-full bg-surface-container-highest border border-outline-variant/15 text-on-surface p-2.5 rounded-md text-sm focus:bg-surface-container-lowest focus:border-secondary outline-none";

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="text-xs font-semibold uppercase tracking-wider text-on-surface-variant">{label}</span>
      <div className="mt-1">{children}</div>
    </label>
  );
}

export function PackagesView({
  canManage,
  onConfirmDelete,
}: {
  canManage: boolean;
  onConfirmDelete: (pkg: PackageSummary) => void;
}) {
  const queryClient = useQueryClient();
  const { data: packages } = useQuery({ queryKey: ["packages"], queryFn: listPackages });
  const [editorMode, setEditorMode] = useState<{ kind: "create" } | { kind: "edit"; id: string } | null>(null);

  return (
    <div className="bg-surface-container-lowest rounded-xl shadow-dossier ring-1 ring-outline-variant/15 overflow-hidden">
      <div className="p-4 flex items-center justify-between border-b border-outline-variant/10 gap-4">
        <h3 className="text-lg font-bold text-on-primary-fixed">Health Packages</h3>
        <div className="flex items-center gap-2">
          <span className="text-sm text-on-surface-variant whitespace-nowrap">
            {packages ? `${packages.length} packages` : "Loading…"}
          </span>
          {canManage && (
            <button
              onClick={() => setEditorMode({ kind: "create" })}
              className="inline-flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm bg-primary-container text-on-primary-container hover:opacity-90"
            >
              <Icon name="add" size={16} /> New Package
            </button>
          )}
        </div>
      </div>

      <div className="max-h-[calc(100vh-260px)] overflow-auto">
        <table className="w-full text-left border-collapse">
          <thead className="bg-primary-container text-on-primary sticky top-0 z-10">
            <tr>
              <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase w-32">Code</th>
              <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase">Name</th>
              <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase w-28">List Price</th>
              <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase w-28">Offer Price</th>
              <th className="px-4 py-3 text-xs font-semibold tracking-wide uppercase w-24">Templates</th>
              {canManage && <th className="px-3 py-3 w-32"></th>}
            </tr>
          </thead>
          <tbody className="text-sm text-on-surface">
            {(packages ?? []).map((p, i) => (
              <tr
                key={p.id}
                className={`${i % 2 === 0 ? "bg-surface" : "bg-surface-container-lowest"} hover:bg-surface-container-high transition-colors group`}
              >
                <td className="px-4 py-2.5 font-mono text-primary-container font-medium text-[13px]">{p.code}</td>
                <td className="px-4 py-2.5">
                  <div className="font-semibold text-on-primary-fixed">{p.name}</div>
                  {p.name_alt && <div className="text-[11px] text-on-surface-variant mt-0.5">{p.name_alt}</div>}
                </td>
                <td className="px-4 py-2.5 text-on-surface-variant line-through">₹{Number(p.list_price).toFixed(0)}</td>
                <td className="px-4 py-2.5 font-bold text-error">₹{Number(p.offer_price).toFixed(0)}</td>
                <td className="px-4 py-2.5 text-on-surface-variant">{p.template_count}</td>
                {canManage && (
                  <td className="px-3 py-2.5 text-right whitespace-nowrap">
                    <button
                      onClick={() => setEditorMode({ kind: "edit", id: p.id })}
                      className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-1 px-2 py-1 rounded text-xs bg-secondary-container text-on-secondary-container hover:opacity-90"
                    >
                      <Icon name="edit" size={14} /> Edit
                    </button>
                    <button
                      onClick={() => onConfirmDelete(p)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity inline-flex items-center gap-1 px-2 py-1 ml-1 rounded text-xs bg-error-container text-on-error-container hover:opacity-90"
                    >
                      <Icon name="delete" size={14} />
                    </button>
                  </td>
                )}
              </tr>
            ))}
            {packages && packages.length === 0 && (
              <tr>
                <td colSpan={canManage ? 6 : 5} className="px-4 py-12 text-center text-on-surface-variant">
                  No packages yet. Click <b>New Package</b> to bundle templates.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>

      {editorMode && (
        <PackageEditor
          mode={editorMode}
          onClose={() => setEditorMode(null)}
          onSaved={() => {
            setEditorMode(null);
            queryClient.invalidateQueries({ queryKey: ["packages"] });
          }}
        />
      )}
    </div>
  );
}

export function PackageEditor({
  mode,
  onClose,
  onSaved,
}: {
  mode: { kind: "create" } | { kind: "edit"; id: string };
  onClose: () => void;
  onSaved: () => void;
}) {
  const isEdit = mode.kind === "edit";

  const { data: detail } = useQuery({
    queryKey: ["package-detail", isEdit ? mode.id : ""],
    queryFn: () => getPackage(mode.kind === "edit" ? mode.id : ""),
    enabled: isEdit,
  });
  const { data: templates } = useQuery({ queryKey: ["templates"], queryFn: listTemplates });

  const [code, setCode] = useState("");
  const [name, setName] = useState("");
  const [nameAlt, setNameAlt] = useState("");
  const [description, setDescription] = useState("");
  const [listPrice, setListPrice] = useState("");
  const [offerPrice, setOfferPrice] = useState("");
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [templateSearch, setTemplateSearch] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!isEdit || !detail) return;
    setCode(detail.code);
    setName(detail.name);
    setNameAlt(detail.name_alt);
    setDescription(detail.description);
    setListPrice(detail.list_price);
    setOfferPrice(detail.offer_price);
    setSelectedIds(
      detail.package_templates
        .sort((a, b) => a.display_order - b.display_order)
        .map((pt) => pt.template),
    );
  }, [detail, isEdit]);

  const selectedSet = useMemo(() => new Set(selectedIds), [selectedIds]);
  const available = useMemo(() => {
    const list = templates ?? [];
    const q = templateSearch.trim().toLowerCase();
    return list.filter(
      (t) =>
        !selectedSet.has(t.id) &&
        (q === "" || t.name.toLowerCase().includes(q) || t.code.toLowerCase().includes(q)),
    );
  }, [templates, selectedSet, templateSearch]);
  const selectedTemplates = useMemo(() => {
    if (!templates) return [];
    const byId = new Map(templates.map((t) => [t.id, t]));
    return selectedIds.map((id) => byId.get(id)).filter((t): t is NonNullable<typeof t> => !!t);
  }, [templates, selectedIds]);

  const saveMutation = useMutation({
    mutationFn: async () => {
      const body = {
        code: code.trim().toUpperCase(),
        name: name.trim(),
        name_alt: nameAlt.trim(),
        description: description.trim(),
        list_price: listPrice,
        offer_price: offerPrice,
        template_ids: selectedIds,
      };
      if (mode.kind === "edit") return updatePackage(mode.id, body);
      return createPackage(body);
    },
    onSuccess: onSaved,
    onError: (err: unknown) => {
      const data = (err as { response?: { data?: unknown } })?.response?.data;
      if (typeof data === "string") setError(data);
      else if (data && typeof data === "object" && "detail" in data)
        setError(String((data as { detail: unknown }).detail));
      else if (data) setError(Object.values(data as Record<string, unknown>).flat().join(" "));
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
  const canSave = name.trim() && code.trim() && listPrice && offerPrice && selectedIds.length > 0;

  return (
    <div className="fixed inset-0 z-50 bg-black/50 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="w-full max-w-5xl max-h-[92vh] bg-surface-container-lowest rounded-2xl shadow-2xl flex flex-col overflow-hidden ring-1 ring-outline-variant/20">
        <div className="px-6 py-4 border-b border-outline-variant/15 flex items-center justify-between">
          <h2 className="text-xl font-bold text-on-primary-fixed">
            {isEdit ? "Edit Package" : "New Package"}
          </h2>
          <button
            onClick={onClose}
            className="p-1.5 rounded-md hover:bg-surface-container-highest text-on-surface-variant"
          >
            <Icon name="close" size={20} />
          </button>
        </div>

        <div className="px-6 py-4 grid grid-cols-1 md:grid-cols-2 gap-3 border-b border-outline-variant/15">
          <Field label="Code *">
            <input
              value={code}
              onChange={(e) => setCode(e.target.value.toUpperCase())}
              placeholder="PKG-CUSTOM"
              className={inputCls + " font-mono"}
            />
          </Field>
          <Field label="Name *">
            <input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="Custom Health Package"
              className={inputCls}
            />
          </Field>
          <Field label="Alternate Name (Hindi / regional)">
            <input
              value={nameAlt}
              onChange={(e) => setNameAlt(e.target.value)}
              placeholder=""
              className={inputCls}
            />
          </Field>
          <Field label="Description">
            <input
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Optional"
              className={inputCls}
            />
          </Field>
          <Field label="List Price *">
            <input
              type="number"
              step="0.01"
              value={listPrice}
              onChange={(e) => setListPrice(e.target.value)}
              placeholder="999"
              className={inputCls}
            />
          </Field>
          <Field label="Offer Price *">
            <input
              type="number"
              step="0.01"
              value={offerPrice}
              onChange={(e) => setOfferPrice(e.target.value)}
              placeholder="499"
              className={inputCls}
            />
          </Field>
        </div>

        <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-0 min-h-0">
          <div className="flex flex-col min-h-0 border-r border-outline-variant/15">
            <div className="px-5 pt-4 pb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-on-primary-fixed">Available Templates</h3>
              <span className="text-xs text-on-surface-variant">
                {templates ? templates.length - selectedIds.length : 0} available
              </span>
            </div>
            <div className="px-5 pb-2">
              <input
                value={templateSearch}
                onChange={(e) => setTemplateSearch(e.target.value)}
                placeholder="Search templates by name or code"
                className={inputCls}
              />
            </div>
            <div className="flex-1 overflow-auto px-3 pb-3">
              {available.map((t) => (
                <button
                  type="button"
                  key={t.id}
                  onClick={() => add(t.id)}
                  className="w-full text-left px-2 py-1.5 rounded hover:bg-surface-container-high group flex items-center justify-between"
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
              {templates && available.length === 0 && (
                <div className="p-6 text-center text-sm text-on-surface-variant">
                  {templateSearch
                    ? `No templates match "${templateSearch}".`
                    : "All templates already added."}
                </div>
              )}
            </div>
          </div>

          <div className="flex flex-col min-h-0">
            <div className="px-5 pt-4 pb-2 flex items-center justify-between">
              <h3 className="text-sm font-semibold text-on-primary-fixed">
                Selected Templates{" "}
                <span className="text-on-surface-variant font-normal">(in render order)</span>
              </h3>
              <span className="text-xs text-on-surface-variant">{selectedIds.length} selected</span>
            </div>
            <div className="flex-1 overflow-auto px-3 pb-3">
              {selectedTemplates.length === 0 && (
                <div className="p-8 text-center text-sm text-on-surface-variant">
                  Click templates on the left to add them here.
                </div>
              )}
              {selectedTemplates.map((t, i) => (
                <div
                  key={t.id}
                  className="flex items-center gap-2 px-2 py-1.5 rounded hover:bg-surface-container-high"
                >
                  <span className="text-xs font-mono w-6 text-on-surface-variant">{i + 1}.</span>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-on-surface truncate">{t.name}</div>
                    <div className="text-[11px] font-mono text-on-surface-variant">{t.code}</div>
                  </div>
                  <button
                    type="button"
                    onClick={() => move(t.id, -1)}
                    disabled={i === 0}
                    className="p-1 rounded hover:bg-surface-container-highest text-on-surface-variant disabled:opacity-30"
                  >
                    <Icon name="arrow_upward" size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => move(t.id, 1)}
                    disabled={i === selectedTemplates.length - 1}
                    className="p-1 rounded hover:bg-surface-container-highest text-on-surface-variant disabled:opacity-30"
                  >
                    <Icon name="arrow_downward" size={16} />
                  </button>
                  <button
                    type="button"
                    onClick={() => remove(t.id)}
                    className="p-1 rounded hover:bg-error-container text-error"
                  >
                    <Icon name="close" size={16} />
                  </button>
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
            type="button"
            onClick={onClose}
            className="px-4 py-2 rounded-lg text-sm text-on-surface-variant hover:bg-surface-container-highest"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={() => {
              setError(null);
              saveMutation.mutate();
            }}
            disabled={!canSave || saveMutation.isPending}
            className="px-5 py-2 rounded-lg text-sm font-semibold bg-primary-container text-on-primary-container hover:opacity-90 disabled:opacity-50"
          >
            {saveMutation.isPending ? "Saving…" : isEdit ? "Save Changes" : "Create Package"}
          </button>
        </div>
      </div>
    </div>
  );
}
