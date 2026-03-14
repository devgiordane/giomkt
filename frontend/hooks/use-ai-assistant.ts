"use client"

import { api } from "@/lib/api"
import type {
  AiAction,
  AiProcessResult,
  SaveTasksBody,
  SaveTasksResponse,
} from "@/types/api"
import { useMutation } from "./use-fetch"

export function useAiProcess() {
  return useMutation(({ action, content }: { action: AiAction; content: string }) =>
    api.post<AiProcessResult>("/ai/process", { action, content }),
  )
}

export function useSaveAiTasks() {
  return useMutation((body: SaveTasksBody) =>
    api.post<SaveTasksResponse>("/ai/save-tasks", body),
  )
}
