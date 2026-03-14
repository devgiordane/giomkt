"use client"

import { api } from "@/lib/api"
import type { WhatsAppSettings, UpdateWhatsAppSettingsBody } from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

export function useWhatsAppSettings() {
  return useFetch<WhatsAppSettings>(() => api.get("/settings/whatsapp"))
}

export function useSaveWhatsAppSettings() {
  return useMutation((body: UpdateWhatsAppSettingsBody) =>
    api.put<{ ok: boolean }>("/settings/whatsapp", body),
  )
}

export function useTestWhatsAppConnection() {
  return useMutation(() =>
    api.post<{ status: number; ok: boolean }>("/settings/whatsapp/test"),
  )
}
