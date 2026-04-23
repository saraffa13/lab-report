import { Icon } from "@/components/ui/Icon";

type Props = {
  count: number;
  label: string;
  onClear: () => void;
  onDelete: () => void;
  busy?: boolean;
};

export function BulkActionsBar({ count, label, onClear, onDelete, busy }: Props) {
  if (count === 0) return null;
  return (
    <div className="sticky top-16 z-30 bg-primary-container text-on-primary rounded-xl px-4 py-2.5 flex items-center justify-between shadow-[0_6px_18px_rgba(11,42,91,0.2)]">
      <div className="flex items-center gap-3 text-sm font-medium">
        <Icon name="check_box" size={18} />
        <span>
          <span className="font-bold">{count}</span> {label}
          {count === 1 ? "" : "s"} selected
        </span>
      </div>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={onClear}
          className="text-sm font-medium px-3 py-1.5 rounded hover:bg-white/10 transition-colors"
        >
          Clear
        </button>
        <button
          type="button"
          onClick={onDelete}
          disabled={busy}
          className="inline-flex items-center gap-1 bg-error-container text-on-error-container text-sm font-bold px-3 py-1.5 rounded hover:opacity-90 transition-opacity disabled:opacity-60"
        >
          <Icon name="delete" size={14} />
          {busy ? "Deleting…" : `Delete ${count}`}
        </button>
      </div>
    </div>
  );
}
