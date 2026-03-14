"use client"

import { CalendarDays, Calendar, Circle, CheckCircle2 } from "lucide-react"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useTasks, useToggleTask } from "@/hooks/use-tasks"
import { formatDate } from "@/lib/utils"
import { cn } from "@/lib/utils"
import type { Task } from "@/types/api"

export default function UpcomingPage() {
  const { data: tasks, loading, error, refetch } = useTasks({ status: "pending" })
  const { mutate: toggle } = useToggleTask()

  async function handleToggle(id: number) {
    await toggle(id)
    refetch()
  }

  const today = new Date().toISOString().slice(0, 10)

  // Only tasks with due_date >= today, sorted
  const upcoming = (tasks ?? [])
    .filter((t) => t.due_date && t.due_date >= today)
    .sort((a, b) => (a.due_date ?? "").localeCompare(b.due_date ?? ""))

  // Group by date
  const grouped = upcoming.reduce<Record<string, Task[]>>((acc, t) => {
    const d = t.due_date!
    acc[d] = acc[d] ?? []
    acc[d].push(t)
    return acc
  }, {})

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold">Próximas</h1>
        <p className="text-sm text-muted-foreground">{upcoming.length} tarefas agendadas</p>
      </div>

      {loading ? (
        <SkeletonTable rows={6} />
      ) : error ? (
        <EmptyState
          icon={<CalendarDays className="size-5" />}
          title="Erro ao carregar tarefas"
          description={error}
        />
      ) : !upcoming.length ? (
        <EmptyState
          icon={<CalendarDays className="size-5" />}
          title="Agenda livre"
          description="Nenhuma tarefa agendada para os próximos dias."
          className="min-h-[300px]"
        />
      ) : (
        <div className="space-y-5">
          {Object.entries(grouped).map(([date, items]) => (
            <div key={date}>
              <div className="mb-2 flex items-center gap-2">
                <Calendar className="size-3.5 text-muted-foreground" />
                <span className="text-xs font-semibold text-muted-foreground">
                  {date === today
                    ? "Hoje"
                    : new Date(date + "T12:00:00").toLocaleDateString("pt-BR", {
                        weekday: "long",
                        day: "numeric",
                        month: "long",
                      })}
                </span>
                <Badge variant="outline" className="text-[10px]">
                  {items.length}
                </Badge>
              </div>
              <div className="space-y-1 rounded-xl border bg-card shadow-sm">
                {items.map((task, i) => (
                  <UpcomingTaskRow
                    key={task.id}
                    task={task}
                    onToggle={handleToggle}
                    isLast={i === items.length - 1}
                  />
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

function UpcomingTaskRow({
  task,
  onToggle,
  isLast,
}: {
  task: Task
  onToggle: (id: number) => void
  isLast: boolean
}) {
  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/30",
        !isLast && "border-b",
      )}
    >
      <button
        onClick={() => onToggle(task.id)}
        className="shrink-0 text-muted-foreground hover:text-primary transition-colors"
      >
        {task.status === "done" ? (
          <CheckCircle2 className="size-5 text-emerald-500" />
        ) : (
          <Circle className="size-5" />
        )}
      </button>
      <div className="flex-1 min-w-0">
        <p className="text-sm">{task.title}</p>
        {task.client && (
          <p className="text-xs text-muted-foreground">{task.client}</p>
        )}
      </div>
      {task.start_time && (
        <span className="shrink-0 text-xs text-muted-foreground">{task.start_time}</span>
      )}
      {task.deadline && task.deadline !== task.due_date && (
        <span className="shrink-0 text-xs text-destructive">
          prazo: {formatDate(task.deadline)}
        </span>
      )}
    </div>
  )
}
