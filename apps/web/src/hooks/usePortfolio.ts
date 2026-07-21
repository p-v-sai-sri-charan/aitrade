import { useQuery } from "@tanstack/react-query";
import type { Portfolio } from "@vaanitrade/shared-types";
import { apiClient } from "../lib/apiClient";

export function usePortfolio() {
  return useQuery({
    queryKey: ["portfolio"],
    queryFn: () => apiClient.get<Portfolio>("/portfolio"),
    refetchInterval: 15_000,
  });
}
