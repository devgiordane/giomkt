"use client"

import { CalendarClock, Clock, Circle, CheckCircle2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useTasks, useToggleTask } from "@/hooks/use-tasks"
import { cn } from "@/lib/utils"
import type { Task, TaskPriority } from "@/types/api"

const PRIORITY_VARIANT: Record<TaskPriority, "destructive" | "warning" | "info" | "outline"> = {
  1: "destructive",
  2: "warning",
  3: "info",
  4: "outline",
}

export default function TodayPage() {
  const today = new Date().toISOString().slice(0, 10)
  const { data: tasks, loading, error, refetch } = useTasks({ due_date: today, status: "pending" })
  const { mutate: toggle } = useToggleTask()

  async function handleToggle(id: number) {
    await toggle(id)
    refetch()
  }

  // Sort by start_time
  const sorted = [...(tasks ?? [])].sort((a, b) => {
    if (!a.start_time) return 1
    if (!b.start_time) return -1
    return a.start_time.localeCompare(b.start_time)
  })

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold">Hoje</h1>
        <p className="text-sm text-muted-foreground">
          {new Date().toLocaleDateString("pt-BR", {
            weekday: "long",
            day: "numeric",
            month: "long",
          })}
        </p>
      </div>

      {loading ? (
        <SkeletonTable rows={5} />
      ) : error ? (
        <EmptyState
          icon={<CalendarClock className="size-5" />}
          title="Erro ao carregar tarefas"
          description={error}
        />
      ) : !sorted.length ? (
        <EmptyState
          icon={<CalendarClock className="size-5" />}
          title="Dia livre!"
          description="Nenhuma tarefa para hoje. Aproveite ou adicione uma."
          className="min-h-[300px]"
        />
      ) : (
        <div className="space-y-2">
          {sorted.map((task) => (
            <TodayTaskRow key={task.id} task={task} onToggle={handleToggle} />
          ))}
        </div>
      )}
    </div>
  )
}

function TodayTaskRow({ task, onToggle }: { task: Task; onToggle: (id: number) => void }) {
  const done = task.status === "done"
  return (
    <div
      className={cn(
        "flex items-center gap-4 rounded-xl border bg-card px-4 py-3 shadow-sm transition-colors",
        done && "opacity-60",
      )}
    >
      {/* Time column */}
      <div className="w-14 shrink-0 text-center">
        {task.start_time ? (
          <div>
            <p className="text-sm font-semibold">{task.start_time}</p>
            {task.duration_minutes && (
              <p className="text-[10px] text-muted-foreground">{task.duration_minutes}min</p>
            )}
          </div>
        ) : (
          <Clock className="mx-auto size-4 text-muted-foreground" />
        )}
      </div>

      {/* Divider */}
      <div className="h-10 w-px bg-border" />

      {/* Toggle */}
      <button
        onClick={() => onToggle(task.id)}
        className="shrink-0 text-muted-foreground hover:text-primary transition-colors"
      >
        {done ? (
          <CheckCircle2 className="size-5 text-emerald-500" />
        ) : (
          <Circle className="size-5" />
        )}
      </button>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className={cn("text-sm font-medium", done && "line-through")}>{task.title}</p>
        {task.client && (
          <p className="text-xs text-muted-foreground">{task.client}</p>
        )}
      </div>

      <Badge variant={PRIORITY_VARIANT[task.priority]} className="shrink-0 text-[10px]">
        P{task.priority}
      </Badge>
    </div>
  )
}
