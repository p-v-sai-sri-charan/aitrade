import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Instrument, InstrumentStatus } from "@vaanitrade/shared-types";
import { apiClient } from "../lib/apiClient";

export function useInstrumentStatus() {
  return useQuery({
    queryKey: ["instrument-status"],
    queryFn: () => apiClient.get<InstrumentStatus>("/instruments/status"),
  });
}

export function useInstrumentSearch(query: string) {
  return useQuery({
    queryKey: ["instrument-search", query],
    queryFn: () => apiClient.get<Instrument[]>(`/instruments/search?q=${encodeURIComponent(query)}`),
    enabled: query.trim().length > 0,
  });
}

export function useRefreshInstruments() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<InstrumentStatus>("/instruments/refresh"),
    onSuccess: (data) => {
      queryClient.setQueryData(["instrument-status"], data);
    },
  });
}
