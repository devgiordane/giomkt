"use client"

import { api } from "@/lib/api"
import type {
  Client,
  ClientDetail,
  CreateClientBody,
  UpdateClientBody,
} from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useClients() {
  return useFetch<Client[]>(() => api.get("/clients"))
}

export function useClient(id: number | null) {
  return useFetch<ClientDetail>(
    () => api.get(`/clients/${id}`),
    [id],
  )
}

export function useCreateClient() {
  return useMutation((body: CreateClientBody) => api.post<{ id: number }>("/clients", body))
}

export function useUpdateClient(id: number) {
  return useMutation((body: UpdateClientBody) => api.put<{ ok: boolean }>(`/clients/${id}`, body))
}

export function useDeleteClient() {
  return useMutation((id: number) => api.delete(`/clients/${id}`))
}
