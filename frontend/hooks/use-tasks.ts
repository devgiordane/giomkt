"use client"

import { api } from "@/lib/api"
import type {
  Task,
  TaskDetail,
  TaskOptions,
  NlpParseResult,
  CreateTaskBody,
  UpdateTaskBody,
  TaskComment,
} from "@/types/api"
import { useFetch, useMutation } from "./use-fetch"

interface TasksParams {
  priority?: string
  status?: string
  include_subtasks?: boolean
}

export function useTasks(params?: TasksParams) {
  return useFetch<Task[]>(
    () => api.get("/tasks", params as Record<string, string>),
    [JSON.stringify(params)],
  )
}

export function useTask(id: number | null) {
  return useFetch<TaskDetail>(
    () => api.get(`/tasks/${id}`),
    [id],
  )
}

export function useTaskOptions() {
  return useFetch<TaskOptions>(() => api.get("/tasks/options"))
}

export function useCreateTask() {
  return useMutation((body: CreateTaskBody) => api.post<{ id: number }>("/tasks", body))
}

export function useUpdateTask(id: number) {
  return useMutation((body: UpdateTaskBody) => api.put<{ ok: boolean }>(`/tasks/${id}`, body))
}

export function useToggleTask() {
  return useMutation((id: number) =>
    api.post<{ status: string; next_created?: boolean }>(`/tasks/${id}/toggle`),
  )
}

export function useDeleteTask() {
  return useMutation((id: number) => api.delete(`/tasks/${id}`))
}

export function useAddComment() {
  return useMutation(({ taskId, content }: { taskId: number; content: string }) =>
    api.post<{ id: number }>(`/tasks/${taskId}/comments`, { content }),
  )
}

export function useDeleteComment() {
  return useMutation((commentId: number) => api.delete(`/tasks/comments/${commentId}`))
}

export function useParseTask() {
  return useMutation((text: string) =>
    api.post<NlpParseResult>("/tasks/parse", { text }),
  )
}
