import { useQuery } from "@tanstack/react-query";
import type { Quote } from "@vaanitrade/shared-types";
import { apiClient } from "../lib/apiClient";

export function useQuote(symbol?: string) {
  return useQuery({
    queryKey: ["quote", symbol],
    queryFn: () => apiClient.get<Quote>(`/quotes/${symbol}`),
    enabled: !!symbol,
  });
}
