"use client"

import { api } from "@/lib/api"
import type {
  WebhookSubscriptionsResponse,
  WebhookEvent,
  CreateWebhookBody,
} from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useWebhookSubscriptions() {
  return useFetch<WebhookSubscriptionsResponse>(() => api.get("/webhooks/subscriptions"))
}

export function useWebhookEvents(subscriptionId?: number) {
  return useFetch<WebhookEvent[]>(
    () => api.get("/webhooks/events", subscriptionId ? { subscription_id: subscriptionId } : undefined),
    [subscriptionId],
  )
}

export function useCreateWebhookSubscription() {
  return useMutation((body: CreateWebhookBody) =>
    api.post("/webhooks/subscriptions", body),
  )
}

export function useSetSubscriptionStatus() {
  return useMutation(({ id, status }: { id: number; status: "active" | "disabled" }) =>
    api.put(`/webhooks/subscriptions/${id}/status`, { status }),
  )
}

export function useDeleteWebhookSubscription() {
  return useMutation((id: number) => api.delete(`/webhooks/subscriptions/${id}`))
}

export function useTestWebhook() {
  return useMutation(({ id, event }: { id: number; event?: string }) =>
    api.post(`/webhooks/subscriptions/${id}/test`, { event }),
  )
}
