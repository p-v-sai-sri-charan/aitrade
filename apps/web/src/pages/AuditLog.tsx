import { useState } from "react";
import { AppShell } from "../components/layout/AppShell";
import { Card } from "../components/ui/Card";
import { useAuditLogs } from "../hooks/useAuditLogs";

export default function AuditLog() {
  const auditQuery = useAuditLogs(100);
  const [expandedId, setExpandedId] = useState<string | null>(null);

  return (
    <AppShell title="Audit Log">
      {auditQuery.isLoading && <Card>Loading audit log...</Card>}
      {auditQuery.data && auditQuery.data.length === 0 && (
        <Card>
          <p className="text-sm text-slate-500">
            Every voice command, validation result, and order response will appear here.
          </p>
        </Card>
      )}

      {auditQuery.data?.map((entry) => {
        const expanded = expandedId === entry.id;
        return (
          <Card key={entry.id}>
            <button
              type="button"
              className="w-full text-left"
              onClick={() => setExpandedId(expanded ? null : entry.id)}
              aria-expanded={expanded}
            >
              <div className="flex items-start justify-between gap-2">
                <p className="text-sm font-medium text-slate-800">
                  {entry.originalTranscript ?? entry.orderResponseSummary ?? "System event"}
                </p>
                <span
                  className={`shrink-0 rounded-full px-2 py-0.5 text-xs font-semibold ${
                    entry.validationValid ? "bg-emerald-100 text-emerald-700" : "bg-red-100 text-red-700"
                  }`}
                >
                  {entry.validationValid ? "Valid" : "Issue"}
                </span>
              </div>
              <p className="mt-1 text-xs text-slate-400">{new Date(entry.timestamp).toLocaleString()}</p>
            </button>

            {expanded && (
              <div className="mt-3 space-y-2 border-t border-slate-100 pt-3 text-xs">
                {entry.detectedLanguage && (
                  <p>
                    <span className="font-medium">Language:</span> {entry.detectedLanguage}
                  </p>
                )}
                {entry.aiProvider && (
                  <p>
                    <span className="font-medium">AI provider:</span> {entry.aiProvider}
                  </p>
                )}
                {entry.parsedIntent && (
                  <div>
                    <p className="font-medium">Parsed intent</p>
                    <pre className="mt-1 overflow-x-auto rounded-lg bg-slate-100 p-2">
                      {JSON.stringify(entry.parsedIntent, null, 2)}
                    </pre>
                  </div>
                )}
                {entry.validationErrors.length > 0 && (
                  <p>
                    <span className="font-medium">Validation errors:</span>{" "}
                    {entry.validationErrors.join(", ")}
                  </p>
                )}
                {entry.riskCheck && (
                  <div>
                    <p className="font-medium">Risk check</p>
                    <pre className="mt-1 overflow-x-auto rounded-lg bg-slate-100 p-2">
                      {JSON.stringify(entry.riskCheck, null, 2)}
                    </pre>
                  </div>
                )}
                {entry.userConfirmed !== null && entry.userConfirmed !== undefined && (
                  <p>
                    <span className="font-medium">User confirmed:</span>{" "}
                    {entry.userConfirmed ? "Yes" : "No"}
                  </p>
                )}
                {entry.orderResponseSummary && (
                  <p>
                    <span className="font-medium">Order response:</span> {entry.orderResponseSummary}
                  </p>
                )}
                {entry.orderId && (
                  <p>
                    <span className="font-medium">Order ID:</span> {entry.orderId}
                  </p>
                )}
              </div>
            )}
          </Card>
        );
      })}
    </AppShell>
  );
}
