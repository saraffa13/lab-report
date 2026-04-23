import { FormEvent, useMemo, useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createUser, deleteUser, listRoles, listUsers, updateUser, type LabUser } from "@/api/users";
import { Icon } from "@/components/ui/Icon";
import { useAuth } from "@/hooks/useAuth";

const CAN_DELETE_ROLES = new Set(["admin", "lab_owner"]);
const CAN_ASSIGN_PRIVILEGED_ROLES = new Set(["admin", "lab_owner"]);

export default function UsersPage() {
  const qc = useQueryClient();
  const { user: me } = useAuth();
  const canDelete =
    !!me && (me.is_superuser || (me.role_code && CAN_DELETE_ROLES.has(me.role_code)));
  // Anyone but a patient (and they can't see this page anyway) may invite.
  const canInvite = !!me && me.role_code !== "patient";
  // Only admin/lab_owner/superuser may assign privileged roles.
  const canAssignPrivileged =
    !!me && (me.is_superuser || (me.role_code && CAN_ASSIGN_PRIVILEGED_ROLES.has(me.role_code)));
  const { data: users } = useQuery({ queryKey: ["users"], queryFn: listUsers });
  const { data: roles } = useQuery({ queryKey: ["roles"], queryFn: listRoles });
  const [creating, setCreating] = useState(false);
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => {
    if (!users) return [];
    if (!search) return users;
    const q = search.toLowerCase();
    return users.filter(
      (u) =>
        u.email.toLowerCase().includes(q) ||
        (u.full_name ?? "").toLowerCase().includes(q) ||
        (u.role_name ?? "").toLowerCase().includes(q),
    );
  }, [users, search]);

  async function handleToggleActive(u: LabUser) {
    await updateUser(u.id, { is_active: !u.is_active });
    qc.invalidateQueries({ queryKey: ["users"] });
  }

  async function handleDelete(u: LabUser) {
    if (me?.id === u.id) {
      alert("You cannot delete your own account.");
      return;
    }
    if (!window.confirm(`Delete user ${u.email}? This cannot be undone.`)) return;
    try {
      await deleteUser(u.id);
      qc.invalidateQueries({ queryKey: ["users"] });
    } catch {
      alert("Failed to delete user.");
    }
  }

  return (
    <div className="flex flex-col gap-8">
      <header className="flex flex-col md:flex-row md:items-end justify-between gap-6">
        <div className="flex flex-col gap-1">
          <h1 className="text-3xl font-black text-on-primary-fixed tracking-tight">
            Personnel Registry
          </h1>
          <p className="text-sm text-on-surface-variant max-w-xl">
            Manage clinical access, review role assignments, and monitor system activity across
            the institution.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="relative">
            <Icon
              name="search"
              size={16}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-outline"
            />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search ID or name"
              className="bg-surface-container-highest ring-1 ring-outline-variant/15 rounded-lg py-2 pl-9 pr-4 text-sm text-on-surface w-60 placeholder:text-outline focus:bg-surface-container-lowest focus:ring-secondary outline-none transition-all"
            />
          </div>
          {canInvite && (
            <button
              onClick={() => setCreating(true)}
              className="bg-gradient-to-b from-primary-container to-primary text-on-primary px-5 py-2.5 rounded-lg flex items-center gap-2 font-medium text-sm hover:opacity-95 transition-opacity shadow-sm"
            >
              <Icon name="person_add" size={18} filled />
              Invite User
            </button>
          )}
        </div>
      </header>

      {creating && canInvite && (
        <CreateUserForm
          roles={(roles ?? []).filter((r) => {
            // Patient logins are created from the patient detail page, not here.
            if (r.code === "patient") return false;
            // PA users can only assign PA role; admin/lab_owner can assign any.
            if ((r.code === "admin" || r.code === "lab_owner") && !canAssignPrivileged) {
              return false;
            }
            return true;
          })}
          onCancel={() => setCreating(false)}
          onCreated={() => {
            setCreating(false);
            qc.invalidateQueries({ queryKey: ["users"] });
          }}
        />
      )}

      <div className="bg-surface-container-lowest rounded-xl shadow-ambient ring-1 ring-outline-variant/15 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-primary-container text-on-primary">
                <th className="py-3 px-5 text-xs uppercase tracking-wider font-semibold w-[35%]">
                  Personnel Details
                </th>
                <th className="py-3 px-5 text-xs uppercase tracking-wider font-semibold">
                  Assigned Role
                </th>
                <th className="py-3 px-5 text-xs uppercase tracking-wider font-semibold">
                  Status
                </th>
                <th className="py-3 px-5 text-xs uppercase tracking-wider font-semibold">
                  Last Activity
                </th>
                <th className="py-3 px-5 text-xs uppercase tracking-wider font-semibold text-right w-32">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody className="text-sm text-on-surface">
              {!users && (
                <tr>
                  <td colSpan={5} className="py-10 px-5 text-center text-on-surface-variant">
                    Loading users…
                  </td>
                </tr>
              )}
              {users && filtered.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-16 px-5 text-center">
                    <Icon
                      name="group_off"
                      size={36}
                      className="text-outline-variant mb-2 block mx-auto"
                    />
                    <div className="text-on-surface-variant text-sm">
                      {search ? "No users match your search." : "No users yet."}
                    </div>
                  </td>
                </tr>
              )}
              {filtered.map((u, i) => {
                const initials = (u.full_name || u.email)
                  .split(/[\s@.]+/)
                  .map((x) => x[0])
                  .filter(Boolean)
                  .slice(0, 2)
                  .join("")
                  .toUpperCase();
                return (
                  <tr
                    key={u.id}
                    className={`${
                      i % 2 === 0 ? "bg-surface" : "bg-surface-container-low"
                    } hover:bg-surface-container-high transition-colors group`}
                  >
                    <td className="py-3 px-5">
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-full bg-surface-container-highest flex items-center justify-center text-primary-container font-bold text-xs">
                          {initials}
                        </div>
                        <div className="flex flex-col min-w-0">
                          <span className="font-semibold text-on-primary-fixed truncate">
                            {u.full_name || "—"}
                          </span>
                          <span className="text-xs text-on-surface-variant font-mono truncate">
                            {u.email}
                          </span>
                        </div>
                      </div>
                    </td>
                    <td className="py-3 px-5">
                      <span className="bg-surface-container-highest text-on-surface px-2.5 py-1 rounded-md text-xs font-medium ring-1 ring-outline-variant/15">
                        {u.role_name || "Unassigned"}
                      </span>
                    </td>
                    <td className="py-3 px-5">
                      {u.is_active ? (
                        <span className="inline-flex items-center gap-1.5 bg-secondary-container text-on-secondary-container px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ring-on-secondary-container/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-on-secondary-container" />
                          Active
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 bg-error-container text-on-error-container px-2.5 py-1 rounded-full text-xs font-semibold ring-1 ring-on-error-container/20">
                          <span className="w-1.5 h-1.5 rounded-full bg-on-error-container" />
                          Disabled
                        </span>
                      )}
                    </td>
                    <td className="py-3 px-5 text-on-surface-variant font-mono text-xs">
                      {new Date(u.created_at).toLocaleDateString(undefined, {
                        day: "2-digit",
                        month: "short",
                        year: "numeric",
                      })}
                    </td>
                    <td className="py-3 px-5 text-right">
                      <div className="flex items-center justify-end gap-3">
                        <button
                          onClick={() => handleToggleActive(u)}
                          className="text-primary-container hover:text-secondary text-sm font-medium transition-colors"
                        >
                          {u.is_active ? "Disable" : "Enable"}
                        </button>
                        {canDelete && (
                          <button
                            onClick={() => handleDelete(u)}
                            className="text-error hover:text-on-error-container text-sm font-medium transition-colors"
                            title="Delete user"
                          >
                            Delete
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <div className="bg-surface-container px-5 py-3 flex items-center justify-between">
          <span className="text-xs text-on-surface-variant">
            Showing{" "}
            <span className="font-semibold text-on-surface">{filtered.length}</span> of{" "}
            <span className="font-semibold text-on-surface">{users?.length ?? 0}</span> personnel
          </span>
        </div>
      </div>
    </div>
  );
}

function CreateUserForm({
  roles,
  onCancel,
  onCreated,
}: {
  roles: { id: number; name: string; code: string }[];
  onCancel: () => void;
  onCreated: () => void;
}) {
  const [form, setForm] = useState({
    email: "",
    full_name: "",
    phone: "",
    password: "",
    role: "",
  });
  const [err, setErr] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setErr(null);
    setBusy(true);
    try {
      await createUser({
        email: form.email,
        full_name: form.full_name,
        phone: form.phone,
        password: form.password,
        role: form.role ? Number(form.role) : null,
        is_active: true,
      });
      onCreated();
    } catch (e: unknown) {
      const ex = e as { response?: { data?: unknown } };
      setErr(
        typeof ex.response?.data === "string"
          ? (ex.response.data as string)
          : JSON.stringify(ex.response?.data ?? "Failed"),
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <form
      onSubmit={submit}
      className="bg-surface-container-lowest rounded-xl p-6 ring-1 ring-outline-variant/15 shadow-dossier flex flex-col gap-4"
    >
      <div className="flex items-center justify-between">
        <h3 className="font-bold text-on-primary-fixed text-base flex items-center gap-2">
          <Icon name="person_add" size={18} className="text-primary-container" />
          Invite New User
        </h3>
        <button
          type="button"
          onClick={onCancel}
          className="text-on-surface-variant hover:text-on-surface p-1 rounded"
        >
          <Icon name="close" size={18} />
        </button>
      </div>
      <div className="grid gap-4 md:grid-cols-2">
        <InputField
          label="Email"
          required
          type="email"
          value={form.email}
          onChange={(v) => setForm({ ...form, email: v })}
        />
        <InputField
          label="Full Name"
          value={form.full_name}
          onChange={(v) => setForm({ ...form, full_name: v })}
        />
        <InputField
          label="Phone"
          value={form.phone}
          onChange={(v) => setForm({ ...form, phone: v })}
        />
        <InputField
          label="Temporary Password"
          required
          type="password"
          value={form.password}
          onChange={(v) => setForm({ ...form, password: v })}
        />
        <div className="md:col-span-2">
          <label className="block text-xs font-medium uppercase tracking-wider text-on-surface-variant mb-1.5">
            Role
          </label>
          <div className="relative">
            <select
              className="w-full bg-surface-container-highest ring-1 ring-outline-variant/15 rounded-md py-2.5 px-3 pr-9 text-sm text-on-surface focus:bg-surface-container-lowest focus:ring-secondary outline-none appearance-none"
              value={form.role}
              onChange={(e) => setForm({ ...form, role: e.target.value })}
            >
              <option value="">— Select role —</option>
              {roles.map((r) => (
                <option key={r.id} value={r.id}>
                  {r.name}
                </option>
              ))}
            </select>
            <Icon
              name="expand_more"
              size={18}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-on-surface-variant pointer-events-none"
            />
          </div>
        </div>
      </div>
      {err && (
        <div className="rounded-lg bg-error-container text-on-error-container px-4 py-2.5 text-sm flex items-center gap-2">
          <Icon name="error" size={16} />
          {err}
        </div>
      )}
      <div className="flex gap-3 justify-end pt-2">
        <button
          type="button"
          onClick={onCancel}
          className="px-4 py-2 rounded-lg text-sm font-medium text-on-surface-variant hover:bg-surface-container-low transition-colors"
        >
          Cancel
        </button>
        <button
          disabled={busy}
          className="bg-gradient-to-b from-primary-container to-primary text-on-primary px-5 py-2 rounded-lg font-medium text-sm hover:opacity-95 transition-opacity flex items-center gap-2 disabled:opacity-60 shadow-sm"
        >
          {busy ? "Creating…" : "Create User"}
        </button>
      </div>
    </form>
  );
}

function InputField({
  label,
  required,
  type = "text",
  value,
  onChange,
}: {
  label: string;
  required?: boolean;
  type?: string;
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <label className="block">
      <span className="block text-xs font-medium uppercase tracking-wider text-on-surface-variant mb-1.5">
        {label}
        {required && <span className="text-error"> *</span>}
      </span>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="w-full bg-surface-container-highest ring-1 ring-outline-variant/15 rounded-md py-2.5 px-3 text-sm text-on-surface focus:bg-surface-container-lowest focus:ring-secondary outline-none transition-all"
      />
    </label>
  );
}
