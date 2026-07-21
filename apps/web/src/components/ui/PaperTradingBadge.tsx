export function PaperTradingBadge({ className = "" }: { className?: string }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-800 ring-1 ring-amber-300 ${className}`}
      role="status"
      aria-label="This app trades with simulated money only, not real money"
    >
      <span className="h-1.5 w-1.5 rounded-full bg-amber-500" />
      PAPER TRADING
    </span>
  );
}
