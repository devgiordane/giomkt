"use client"

import { api } from "@/lib/api"
import type { Label, CreateLabelBody, UpdateLabelBody } from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useLabels() {
  return useFetch<Label[]>(() => api.get("/labels"))
}

export function useCreateLabel() {
  return useMutation((body: CreateLabelBody) => api.post<{ id: number }>("/labels", body))
}

export function useUpdateLabel(id: number) {
  return useMutation((body: UpdateLabelBody) => api.put<{ ok: boolean }>(`/labels/${id}`, body))
}

export function useDeleteLabel() {
  return useMutation((id: number) => api.delete(`/labels/${id}`))
}
