"use client"

import { api } from "@/lib/api"
import type { DashboardKpis } from "@/types/api"
import { useFetch } from "./use-fetch"

export function useDashboardKpis() {
  return useFetch<DashboardKpis>(() => api.get("/dashboard/kpis"))
}
