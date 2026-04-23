import { useEffect, useState } from "react";
import { updateReportPayment, type ReportListItem } from "@/api/reports";
import { Icon } from "@/components/ui/Icon";

type Props = {
  report: ReportListItem;
  onChanged?: () => void;
};

export function PaymentCell({ report, onChanged }: Props) {
  const [amount, setAmount] = useState<string>(
    report.total_amount != null ? String(report.total_amount) : "",
  );
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  useEffect(() => {
    setAmount(report.total_amount != null ? String(report.total_amount) : "");
  }, [report.total_amount]);

  if (report.payment_status === "paid") {
    return (
      <div className="flex items-center gap-2 justify-end">
        <span className="font-mono font-semibold text-on-surface">
          ₹{Number(report.total_amount ?? 0).toLocaleString("en-IN")}
        </span>
        <span className="inline-flex items-center gap-1 bg-secondary-container text-on-secondary-container text-[11px] font-bold px-2 py-0.5 rounded ring-1 ring-on-secondary-container/20">
          <Icon name="check_circle" size={12} /> Paid
        </span>
      </div>
    );
  }

  async function markPaid() {
    setErr(null);
    const trimmed = amount.trim();
    if (!trimmed) {
      setErr("Enter amount first.");
      return;
    }
    const n = Number(trimmed);
    if (!Number.isFinite(n) || n < 0) {
      setErr("Invalid amount.");
      return;
    }
    setBusy(true);
    try {
      await updateReportPayment(report.id, { total_amount: n, payment_status: "paid" });
      onChanged?.();
    } catch {
      setErr("Failed to save.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex items-center gap-2 justify-end">
      <div className="relative">
        <span className="absolute left-2 top-1/2 -translate-y-1/2 text-on-surface-variant text-xs">
          ₹
        </span>
        <input
          type="number"
          inputMode="decimal"
          min={0}
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder="0"
          className="w-24 bg-surface-container-highest border border-outline-variant/20 text-on-surface pl-5 pr-2 py-1 rounded text-sm font-mono text-right focus:bg-surface-container-lowest focus:border-secondary focus:ring-1 focus:ring-secondary outline-none"
          onClick={(e) => e.stopPropagation()}
        />
      </div>
      <button
        type="button"
        onClick={markPaid}
        disabled={busy}
        title="Mark as paid"
        className="inline-flex items-center gap-1 bg-primary-container text-on-primary text-xs font-bold px-2.5 py-1 rounded hover:opacity-90 transition-opacity disabled:opacity-60"
      >
        <Icon name="check" size={12} />
        {busy ? "…" : "Mark Paid"}
      </button>
      {err && <span className="text-[11px] text-error">{err}</span>}
    </div>
  );
}
