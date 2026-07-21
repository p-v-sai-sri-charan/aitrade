import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import type { Order, OrderPreview, OrderRequest } from "@vaanitrade/shared-types";
import { apiClient } from "../lib/apiClient";

export function useOrders(status?: string) {
  return useQuery({
    queryKey: ["orders", status ?? "all"],
    queryFn: () =>
      apiClient.get<Order[]>(`/orders${status ? `?status_filter=${status}` : ""}`),
    refetchInterval: 15_000,
  });
}

export function usePreviewOrder() {
  return useMutation({
    mutationFn: (request: OrderRequest) => apiClient.post<OrderPreview>("/orders/preview", request),
  });
}

export function useConfirmOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ previewId, idempotencyKey }: { previewId: string; idempotencyKey: string }) =>
      apiClient.post<Order>("/orders/confirm", { previewId, idempotencyKey }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
      queryClient.invalidateQueries({ queryKey: ["positions"] });
    },
  });
}

export function useCancelOrder() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (orderId: string) => apiClient.post<Order>(`/orders/${orderId}/cancel`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["orders"] });
      queryClient.invalidateQueries({ queryKey: ["portfolio"] });
    },
  });
}
