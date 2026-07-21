import { useQuery } from "@tanstack/react-query";
import type { Position } from "@vaanitrade/shared-types";
import { apiClient } from "../lib/apiClient";

export function usePositions() {
  return useQuery({
    queryKey: ["positions"],
    queryFn: () => apiClient.get<Position[]>("/positions"),
    refetchInterval: 15_000,
  });
}
