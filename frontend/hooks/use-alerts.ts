"use client"

import { api } from "@/lib/api"
import type {
  Alert,
  AlertRulesResponse,
  CreateAlertRuleBody,
  CheckAlertsResponse,
} from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useAlerts(resolved?: boolean) {
  return useFetch<Alert[]>(
    () => api.get("/alerts", resolved !== undefined ? { resolved } : undefined),
    [resolved],
  )
}

export function useResolveAlert() {
  return useMutation((id: number) => api.post<{ ok: boolean }>(`/alerts/${id}/resolve`))
}

export function useCheckAlerts() {
  return useMutation(() => api.post<CheckAlertsResponse>("/alerts/check"))
}

export function useAlertRules() {
  return useFetch<AlertRulesResponse>(() => api.get("/alerts/rules"))
}

export function useCreateAlertRule() {
  return useMutation((body: CreateAlertRuleBody) =>
    api.post<{ id: number }>("/alerts/rules", body),
  )
}

export function useDeleteAlertRule() {
  return useMutation((id: number) => api.delete(`/alerts/rules/${id}`))
}
