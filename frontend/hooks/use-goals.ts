"use client"

import { api } from "@/lib/api"
import type { Goal, UpsertGoalBody } from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

interface GoalsParams {
  month?: number
  year?: number
  view_mode?: "commission" | "total"
  sort_mode?: "default" | "closest" | "farthest"
}

export function useGoals(params?: GoalsParams) {
  return useFetch<Goal[]>(
    () => api.get("/goals", params as Record<string, string | number>),
    [JSON.stringify(params)],
  )
}

export function useUpsertGoal() {
  return useMutation((body: UpsertGoalBody) => api.post<{ id: number }>("/goals", body))
}
