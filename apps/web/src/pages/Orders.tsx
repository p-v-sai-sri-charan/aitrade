import { useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { Button } from "../components/ui/Button";
import { Card } from "../components/ui/Card";
import { useCancelOrder, useOrders } from "../hooks/useOrders";

const TABS = [
  { key: "PENDING", label: "Pending" },
  { key: "FILLED", label: "Completed" },
  { key: "REJECTED", label: "Rejected" },
  { key: "CANCELLED", label: "Cancelled" },
] as const;

type TabKey = (typeof TABS)[number]["key"];

function formatInr(value: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(
    value,
  );
}

export default function Orders() {
  const [tab, setTab] = useState<TabKey>("PENDING");
  const ordersQuery = useOrders(tab);
  const cancelOrder = useCancelOrder();

  return (
    <AppShell title="Orders">
      <div className="flex gap-2 overflow-x-auto scrollbar-none">
        {TABS.map((t) => (
          <button
            key={t.key}
            type="button"
            onClick={() => setTab(t.key)}
            className={`whitespace-nowrap rounded-full px-3 py-1.5 text-xs font-medium ${
              tab === t.key ? "bg-brand-600 text-white" : "bg-slate-100 text-slate-600"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {ordersQuery.isLoading && <Card>Loading orders...</Card>}
      {ordersQuery.data && ordersQuery.data.length === 0 && (
        <Card>
          <p className="text-sm text-slate-500">No {tab.toLowerCase()} orders.</p>
        </Card>
      )}

      {ordersQuery.data?.map((order) => (
        <Card key={order.id}>
          <div className="flex items-start justify-between">
            <div>
              <p className="font-semibold text-slate-900">
                {order.side} {order.quantity} {order.symbol}
              </p>
              <p className="text-xs text-slate-500">{order.companyName}</p>
              <p className="mt-1 text-xs text-slate-400">
                {order.orderType}
                {order.limitPrice ? ` @ ${formatInr(order.limitPrice)}` : ""} &middot;{" "}
                {new Date(order.createdAt).toLocaleString()}
              </p>
              {order.rejectionReason && <p className="mt-1 text-xs text-loss">{order.rejectionReason}</p>}
            </div>
            <span
              className={`rounded-full px-2 py-0.5 text-xs font-semibold ${
                order.status === "FILLED"
                  ? "bg-emerald-100 text-emerald-700"
                  : order.status === "REJECTED"
                    ? "bg-red-100 text-red-700"
                    : order.status === "CANCELLED"
                      ? "bg-slate-200 text-slate-600"
                      : "bg-amber-100 text-amber-700"
              }`}
            >
              {order.status}
            </span>
          </div>
          {order.status === "PENDING" && (
            <Button
              variant="secondary"
              className="mt-3 w-full"
              onClick={() => cancelOrder.mutate(order.id)}
              disabled={cancelOrder.isPending}
            >
              Cancel order
            </Button>
          )}
        </Card>
      ))}
    </AppShell>
  );
}
