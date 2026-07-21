import type { RiskCheckResult } from "@vaanitrade/shared-types";

export function RiskWarning({ riskCheck }: { riskCheck: RiskCheckResult }) {
  if (riskCheck.allowed) {
    return (
      <div
        role="status"
        className="flex items-start gap-2 rounded-xl bg-emerald-50 p-3 text-sm text-emerald-800 ring-1 ring-emerald-200"
      >
        <span aria-hidden className="mt-0.5">
          ✓
        </span>
        <p>{riskCheck.message}</p>
      </div>
    );
  }

  return (
    <div
      role="alert"
      className="flex items-start gap-2 rounded-xl bg-red-50 p-3 text-sm text-red-800 ring-1 ring-red-200"
    >
      <span aria-hidden className="mt-0.5">
        ⚠
      </span>
      <div>
        <p className="font-medium">{riskCheck.code.replaceAll("_", " ")}</p>
        <p>{riskCheck.message}</p>
      </div>
    </div>
  );
}
