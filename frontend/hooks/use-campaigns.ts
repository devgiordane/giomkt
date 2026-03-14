"use client"

import { api } from "@/lib/api"
import type { CampaignsResponse } from "@/types/api"
import { useFetch } from "./use-fetch"

export function useCampaigns(limit?: number) {
  return useFetch<CampaignsResponse>(
    () => api.get("/campaigns/snapshots", limit ? { limit } : undefined),
    [limit],
  )
}
