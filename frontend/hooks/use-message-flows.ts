"use client"

import { api } from "@/lib/api"
import type { MessageFlowsResponse, CreateMessageFlowBody } from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useMessageFlows(productId?: number) {
  return useFetch<MessageFlowsResponse>(
    () => api.get("/message-flows", productId ? { product_id: productId } : undefined),
    [productId],
  )
}

export function useCreateMessageFlow() {
  return useMutation((body: CreateMessageFlowBody) =>
    api.post<{ id: number }>("/message-flows", body),
  )
}

export function useToggleMessageFlow() {
  return useMutation((id: number) =>
    api.post<{ active: boolean }>(`/message-flows/${id}/toggle`),
  )
}

export function useDeleteMessageFlow() {
  return useMutation((id: number) => api.delete(`/message-flows/${id}`))
}
