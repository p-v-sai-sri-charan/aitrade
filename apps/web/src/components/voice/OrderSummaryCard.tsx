import type { OrderPreview } from "@vaanitrade/shared-types";
import { Button } from "../ui/Button";
import { Card } from "../ui/Card";
import { RiskWarning } from "../ui/RiskWarning";

interface OrderSummaryCardProps {
  preview: OrderPreview;
  onConfirm: () => void;
  onCancel: () => void;
  isConfirming?: boolean;
}

function formatInr(value: number): string {
  return new Intl.NumberFormat("en-IN", { style: "currency", currency: "INR", maximumFractionDigits: 2 }).format(
    value,
  );
}

export function OrderSummaryCard({ preview, onConfirm, onCancel, isConfirming }: OrderSummaryCardProps) {
  const { request } = preview;
  const canConfirm = preview.riskCheck.allowed;

  return (
    <Card title="Order summary">
      <dl className="grid grid-cols-2 gap-y-2 text-sm">
        <dt className="text-slate-500">Company</dt>
        <dd className="text-right font-medium">{preview.companyName}</dd>
        <dt className="text-slate-500">Symbol</dt>
        <dd className="text-right font-medium">{request.symbol}</dd>
        <dt className="text-slate-500">Side</dt>
        <dd className={`text-right font-semibold ${request.side === "BUY" ? "text-profit" : "text-loss"}`}>
          {request.side}
        </dd>
        <dt className="text-slate-500">Quantity</dt>
        <dd className="text-right font-medium">{request.quantity}</dd>
        <dt className="text-slate-500">Order type</dt>
        <dd className="text-right font-medium">{request.orderType}</dd>
        {request.orderType === "LIMIT" && (
          <>
            <dt className="text-slate-500">Limit price</dt>
            <dd className="text-right font-medium">{formatInr(request.limitPrice ?? 0)}</dd>
          </>
        )}
        <dt className="text-slate-500">Est. price</dt>
        <dd className="text-right font-medium">{formatInr(preview.estimatedPrice)}</dd>
        <dt className="text-slate-500">Est. value</dt>
        <dd className="text-right font-medium">{formatInr(preview.estimatedValue)}</dd>
        <dt className="text-slate-500">Brokerage + taxes</dt>
        <dd className="text-right font-medium">
          {formatInr(preview.estimatedBrokerage + preview.estimatedTaxes)}
        </dd>
        <dt className="font-semibold text-slate-700">Est. total</dt>
        <dd className="text-right text-base font-bold">{formatInr(preview.estimatedTotal)}</dd>
      </dl>

      <div className="mt-4">
        <RiskWarning riskCheck={preview.riskCheck} />
      </div>

      <div className="mt-4 flex gap-3">
        <Button variant="secondary" className="flex-1" onClick={onCancel} disabled={isConfirming}>
          Cancel
        </Button>
        <Button
          variant="primary"
          className="flex-1"
          onClick={onConfirm}
          disabled={!canConfirm || isConfirming}
        >
          {isConfirming ? "Placing..." : `Confirm ${request.side.toLowerCase()}`}
        </Button>
      </div>
      {!canConfirm && (
        <p className="mt-2 text-center text-xs text-slate-500">
          This order can't be placed until the issue above is resolved.
        </p>
      )}
    </Card>
  );
}
