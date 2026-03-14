"use client"

import { api } from "@/lib/api"
import type { NotesResponse, CreateNoteBody } from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

interface NotesParams {
  client_id?: number
  wiki?: boolean
  limit?: number
}

export function useNotes(params?: NotesParams) {
  return useFetch<NotesResponse>(
    () => api.get("/notes", params as Record<string, string | number | boolean>),
    [JSON.stringify(params)],
  )
}

export function useCreateNote() {
  return useMutation((body: CreateNoteBody) => api.post<{ id: number }>("/notes", body))
}

export function useUpdateNote() {
  return useMutation(({ id, content }: { id: number; content: string }) =>
    api.put<{ id: number }>(`/notes/${id}`, { content }),
  )
}

export function useDeleteNote() {
  return useMutation((id: number) => api.delete(`/notes/${id}`))
}
