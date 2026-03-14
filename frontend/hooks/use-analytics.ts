"use client"

import { api } from "@/lib/api"
import type {
  AnalyticsSitesResponse,
  AnalyticsStatsResponse,
  CreateSiteBody,
} from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useAnalyticsSites() {
  return useFetch<AnalyticsSitesResponse>(() => api.get("/analytics/sites"))
}

export function useAnalyticsStats(siteId: number | null, days: number = 30) {
  return useFetch<AnalyticsStatsResponse>(
    () => api.get("/analytics/stats", { site_id: siteId!, days }),
    [siteId, days],
  )
}

export function useCreateSite() {
  return useMutation((body: CreateSiteBody) =>
    api.post<{ id: number }>("/analytics/sites", body),
  )
}

export function useDeleteSite() {
  return useMutation((id: number) => api.delete(`/analytics/sites/${id}`))
}
