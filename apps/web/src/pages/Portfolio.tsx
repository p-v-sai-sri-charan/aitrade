import { AppShell } from "../components/layout/AppShell";
import { Card } from "../components/ui/Card";
import { usePositions } from "../hooks/usePositions";

function formatInr(value: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(
    value,
  );
}

export default function Portfolio() {
  const positionsQuery = usePositions();

  return (
    <AppShell title="Portfolio">
      {positionsQuery.isLoading && <Card>Loading holdings...</Card>}
      {positionsQuery.isError && <Card>Couldn't load your holdings. Pull to refresh.</Card>}
      {positionsQuery.data && positionsQuery.data.length === 0 && (
        <Card>
          <p className="text-sm text-slate-500">
            You don't hold any positions yet. Place a paper trade from the Voice Trade tab to get
            started.
          </p>
        </Card>
      )}

      {positionsQuery.data?.map((position) => (
        <Card key={position.symbol}>
          <div className="flex items-start justify-between">
            <div>
              <p className="font-semibold text-slate-900">{position.symbol}</p>
              <p className="text-xs text-slate-500">{position.companyName}</p>
            </div>
            <div className="text-right">
              <p
                className={`text-sm font-semibold ${position.unrealizedPnl >= 0 ? "text-profit" : "text-loss"}`}
              >
                {position.unrealizedPnl >= 0 ? "+" : ""}
                {formatInr(position.unrealizedPnl)}
              </p>
              <p className="text-xs text-slate-400">{position.unrealizedPnlPct.toFixed(2)}%</p>
            </div>
          </div>
          <dl className="mt-3 grid grid-cols-3 gap-2 text-xs text-slate-500">
            <div>
              <dt>Qty</dt>
              <dd className="text-sm font-medium text-slate-800">{position.quantity}</dd>
            </div>
            <div>
              <dt>Avg. price</dt>
              <dd className="text-sm font-medium text-slate-800">{formatInr(position.averagePrice)}</dd>
            </div>
            <div>
              <dt>LTP</dt>
              <dd className="text-sm font-medium text-slate-800">{formatInr(position.currentPrice)}</dd>
            </div>
          </dl>
        </Card>
      ))}
    </AppShell>
  );
}
