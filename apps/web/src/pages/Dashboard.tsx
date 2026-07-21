import { Link } from "react-router-dom";
import { AppShell } from "../components/layout/AppShell";
import { Card } from "../components/ui/Card";
import { useAuditLogs } from "../hooks/useAuditLogs";
import { useOrders } from "../hooks/useOrders";
import { usePortfolio } from "../hooks/usePortfolio";

function formatInr(value: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(
    value,
  );
}

export default function Dashboard() {
  const portfolioQuery = usePortfolio();
  const ordersQuery = useOrders("PENDING");
  const auditQuery = useAuditLogs(5);

  return (
    <AppShell title="Dashboard">
      {portfolioQuery.isLoading && <Card>Loading your paper portfolio...</Card>}
      {portfolioQuery.isError && <Card>Couldn't load your portfolio. Pull to refresh.</Card>}

      {portfolioQuery.data && (
        <div className="grid grid-cols-2 gap-3">
          <Card title="Paper balance">
            <p className="text-xl font-bold">{formatInr(portfolioQuery.data.availableBalance)}</p>
          </Card>
          <Card title="Portfolio value">
            <p className="text-xl font-bold">{formatInr(portfolioQuery.data.portfolioValue)}</p>
          </Card>
          <Card title="Day P&amp;L" className="col-span-2">
            <p
              className={`text-2xl font-bold ${portfolioQuery.data.dayPnl >= 0 ? "text-profit" : "text-loss"}`}
            >
              {portfolioQuery.data.dayPnl >= 0 ? "+" : ""}
              {formatInr(portfolioQuery.data.dayPnl)}{" "}
              <span className="text-sm font-medium">({portfolioQuery.data.dayPnlPct.toFixed(2)}%)</span>
            </p>
          </Card>
        </div>
      )}

      <Card title="Open orders">
        {ordersQuery.isLoading && <p className="text-sm text-slate-500">Loading...</p>}
        {ordersQuery.data && ordersQuery.data.length === 0 && (
          <p className="text-sm text-slate-500">No pending orders.</p>
        )}
        {ordersQuery.data && ordersQuery.data.length > 0 && (
          <ul className="divide-y divide-slate-100">
            {ordersQuery.data.map((order) => (
              <li key={order.id} className="flex justify-between py-2 text-sm">
                <span>
                  {order.side} {order.quantity} {order.symbol}
                </span>
                <span className="text-slate-500">{order.orderType}</span>
              </li>
            ))}
          </ul>
        )}
        <Link to="/orders" className="mt-2 inline-block text-sm font-medium text-brand-600">
          View all orders &rarr;
        </Link>
      </Card>

      <Card title="Recent activity">
        {auditQuery.data && auditQuery.data.length === 0 && (
          <p className="text-sm text-slate-500">No activity yet -- try the Voice Trade tab.</p>
        )}
        {auditQuery.data && auditQuery.data.length > 0 && (
          <ul className="space-y-2">
            {auditQuery.data.map((entry) => (
              <li key={entry.id} className="text-sm">
                <p className="text-slate-800">{entry.orderResponseSummary ?? entry.originalTranscript}</p>
                <p className="text-xs text-slate-400">{new Date(entry.timestamp).toLocaleString()}</p>
              </li>
            ))}
          </ul>
        )}
        <Link to="/audit-log" className="mt-2 inline-block text-sm font-medium text-brand-600">
          View full audit log &rarr;
        </Link>
      </Card>

      <Link
        to="/voice"
        className="block rounded-2xl bg-brand-600 p-4 text-center text-base font-semibold text-white shadow-sm"
      >
        Start a voice trade
      </Link>
    </AppShell>
  );
}
