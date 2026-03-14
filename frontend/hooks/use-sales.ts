"use client"

import { api } from "@/lib/api"
import type { SalesResponse, CreateSaleBody } from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

interface SalesParams {
  product_id?: number
  month?: string   // "YYYY-MM"
}

export function useSales(params?: SalesParams) {
  return useFetch<SalesResponse>(
    () => api.get("/sales", params as Record<string, string | number>),
    [JSON.stringify(params)],
  )
}

export function useCreateSale() {
  return useMutation((body: CreateSaleBody) => api.post<{ id: number }>("/sales", body))
}

export function useDeleteSale() {
  return useMutation((id: number) => api.delete(`/sales/${id}`))
}

export function useSyncSales() {
  return useMutation((days: number = 7) => api.post("/sales/sync", { days }))
}
