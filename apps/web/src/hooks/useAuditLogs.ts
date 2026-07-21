import { useQuery } from "@tanstack/react-query";
import type { AuditLogEntry } from "@vaanitrade/shared-types";
import { apiClient } from "../lib/apiClient";

export function useAuditLogs(limit = 50) {
  return useQuery({
    queryKey: ["audit-logs", limit],
    queryFn: () => apiClient.get<AuditLogEntry[]>(`/audit-logs?limit=${limit}`),
  });
}
