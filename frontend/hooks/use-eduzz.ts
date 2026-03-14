"use client"

import { api } from "@/lib/api"
import type {
  EduzzAccount,
  CreateEduzzAccountBody,
  SyncSalesBody,
} from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useEduzzAccounts() {
  return useFetch<EduzzAccount[]>(() => api.get("/eduzz/accounts"))
}

export function useCreateEduzzAccount() {
  return useMutation((body: CreateEduzzAccountBody) =>
    api.post<{ id: number; auth_url: string }>("/eduzz/accounts", body),
  )
}

export function useUpdateEduzzAccount(id: number) {
  return useMutation((body: { name?: string; active?: boolean }) =>
    api.put<{ ok: boolean }>(`/eduzz/accounts/${id}`, body),
  )
}

export function useDeleteEduzzAccount() {
  return useMutation((id: number) => api.delete(`/eduzz/accounts/${id}`))
}

export function useSyncEduzzSales(accountId: number) {
  return useMutation((body: SyncSalesBody) =>
    api.post(`/eduzz/accounts/${accountId}/sync`, body),
  )
}
