import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { UserSettings } from "@vaanitrade/shared-types";
import { apiClient } from "../lib/apiClient";

export function useSettings() {
  return useQuery({
    queryKey: ["settings"],
    queryFn: () => apiClient.get<UserSettings>("/settings"),
  });
}

export function useUpdateSettings() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (partial: Partial<UserSettings>) => apiClient.put<UserSettings>("/settings", partial),
    onSuccess: (data) => {
      queryClient.setQueryData(["settings"], data);
    },
  });
}

export function useResetPaperTrading() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: () => apiClient.post<UserSettings>("/settings/reset-paper-trading"),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["positions"] });
      queryClient.invalidateQueries({ queryKey: ["orders"] });
    },
  });
}
