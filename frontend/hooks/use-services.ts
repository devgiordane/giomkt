"use client"

import { api } from "@/lib/api"
import type { ServicesResponse, CreateServiceBody, UpdateServiceBody } from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useServices() {
  return useFetch<ServicesResponse>(() => api.get("/services"))
}

export function useCreateService() {
  return useMutation((body: CreateServiceBody) => api.post<{ id: number }>("/services", body))
}

export function useUpdateService(id: number) {
  return useMutation((body: UpdateServiceBody) => api.put<{ ok: boolean }>(`/services/${id}`, body))
}

export function useDeleteService() {
  return useMutation((id: number) => api.delete(`/services/${id}`))
}
