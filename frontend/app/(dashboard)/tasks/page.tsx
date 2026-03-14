"use client"

import { useState } from "react"
import {
  CheckSquare,
  Plus,
  Circle,
  CheckCircle2,
  ChevronDown,
  Tag,
  Calendar,
  Clock,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useTasks, useToggleTask, useCreateTask } from "@/hooks/use-tasks"
import { formatDate } from "@/lib/utils"
import { cn } from "@/lib/utils"
import type { Task, TaskPriority } from "@/types/api"

const PRIORITY_LABEL: Record<TaskPriority, string> = {
  1: "Urgente",
  2: "Alta",
  3: "Normal",
  4: "Baixa",
}

const PRIORITY_VARIANT: Record<TaskPriority, "destructive" | "warning" | "info" | "outline"> = {
  1: "destructive",
  2: "warning",
  3: "info",
  4: "outline",
}

export default function TasksPage() {
  const [status, setStatus] = useState<"pending" | "done" | undefined>("pending")
  const [search, setSearch] = useState("")
  const [showCreate, setShowCreate] = useState(false)

  const { data: tasks, loading, error, refetch } = useTasks({ status })
  const { mutate: toggle } = useToggleTask()
  const { mutate: create, loading: creating } = useCreateTask()

  const filtered = tasks?.filter((t) =>
    t.title.toLowerCase().includes(search.toLowerCase()),
  )

  async function handleToggle(id: number) {
    await toggle(id)
    refetch()
  }

  async function handleCreate(title: string) {
    if (!title.trim()) return
    await create({ title })
    setShowCreate(false)
    refetch()
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Tarefas</h1>
          <p className="text-sm text-muted-foreground">
            {tasks?.length ?? 0} {status === "done" ? "concluídas" : "pendentes"}
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus />
          Nova tarefa
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <Input
          placeholder="Buscar..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="h-8 w-48"
        />
        <div className="flex rounded-lg border">
          {(["pending", "done"] as const).map((s) => (
            <button
              key={s}
              onClick={() => setStatus(s)}
              className={cn(
                "px-3 py-1 text-xs first:rounded-l-lg last:rounded-r-lg transition-colors",
                status === s
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              {s === "pending" ? "Pendentes" : "Concluídas"}
            </button>
          ))}
        </div>
      </div>

      {/* Quick create */}
      {showCreate && (
        <QuickCreateTask
          loading={creating}
          onSubmit={handleCreate}
          onCancel={() => setShowCreate(false)}
        />
      )}

      {/* Content */}
      {loading ? (
        <SkeletonTable rows={6} />
      ) : error ? (
        <EmptyState
          icon={<CheckSquare className="size-5" />}
          title="Erro ao carregar tarefas"
          description={error}
        />
      ) : !filtered?.length ? (
        <EmptyState
          icon={<CheckSquare className="size-5" />}
          title="Nenhuma tarefa encontrada"
          description={
            search
              ? "Tente outro termo de busca."
              : status === "done"
                ? "Nenhuma tarefa concluída ainda."
                : "Crie sua primeira tarefa para começar."
          }
          action={
            !search && status === "pending"
              ? { label: "Nova tarefa", onClick: () => setShowCreate(true) }
              : undefined
          }
        />
      ) : (
        <TaskList tasks={filtered} onToggle={handleToggle} />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Task List grouped by section
// ---------------------------------------------------------------------------

function TaskList({ tasks, onToggle }: { tasks: Task[]; onToggle: (id: number) => void }) {
  const grouped = tasks.reduce<Record<string, Task[]>>((acc, t) => {
    const sec = t.section || "Geral"
    acc[sec] = acc[sec] ?? []
    acc[sec].push(t)
    return acc
  }, {})

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([section, items]) => (
        <div key={section}>
          <div className="mb-2 flex items-center gap-2">
            <ChevronDown className="size-3.5 text-muted-foreground" />
            <span className="text-xs font-semibold uppercase tracking-wider text-muted-foreground">
              {section}
            </span>
            <span className="text-xs text-muted-foreground">({items.length})</span>
          </div>
          <div className="space-y-1 rounded-xl border bg-card shadow-sm">
            {items.map((task, i) => (
              <TaskRow
                key={task.id}
                task={task}
                onToggle={onToggle}
                isLast={i === items.length - 1}
              />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Task Row
// ---------------------------------------------------------------------------

function TaskRow({
  task,
  onToggle,
  isLast,
}: {
  task: Task
  onToggle: (id: number) => void
  isLast: boolean
}) {
  const done = task.status === "done"

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/40",
        !isLast && "border-b",
      )}
    >
      {/* Toggle */}
      <button
        onClick={() => onToggle(task.id)}
        className="shrink-0 text-muted-foreground transition-colors hover:text-primary"
        aria-label={done ? "Reabrir tarefa" : "Concluir tarefa"}
      >
        {done ? (
          <CheckCircle2 className="size-5 text-emerald-500" />
        ) : (
          <Circle className="size-5" />
        )}
      </button>

      {/* Content */}
      <div className="min-w-0 flex-1">
        <p className={cn("text-sm", done && "text-muted-foreground line-through")}>
          {task.title}
        </p>
        <div className="mt-0.5 flex flex-wrap items-center gap-2">
          {task.client && (
            <span className="text-xs text-muted-foreground">{task.client}</span>
          )}
          {task.due_date && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="size-3" />
              {formatDate(task.due_date)}
            </span>
          )}
          {task.start_time && (
            <span className="flex items-center gap-1 text-xs text-muted-foreground">
              <Clock className="size-3" />
              {task.start_time}
            </span>
          )}
          {task.labels.map((l) => (
            <span
              key={l.id}
              className="inline-flex items-center gap-1 rounded-md px-1.5 py-0.5 text-[10px] font-medium"
              style={{ backgroundColor: l.color + "25", color: l.color }}
            >
              <Tag className="size-2.5" />
              {l.name}
            </span>
          ))}
        </div>
      </div>

      {/* Priority */}
      <Badge variant={PRIORITY_VARIANT[task.priority]} className="shrink-0 text-[10px]">
        {PRIORITY_LABEL[task.priority]}
      </Badge>

      {/* Subtask count */}
      {task.subtask_count > 0 && (
        <span className="shrink-0 text-xs text-muted-foreground">
          {task.subtask_count} sub
        </span>
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Quick Create Task
// ---------------------------------------------------------------------------

function QuickCreateTask({
  loading,
  onSubmit,
  onCancel,
}: {
  loading: boolean
  onSubmit: (title: string) => void
  onCancel: () => void
}) {
  const [title, setTitle] = useState("")

  function handleKey(e: React.KeyboardEvent) {
    if (e.key === "Enter") onSubmit(title)
    if (e.key === "Escape") onCancel()
  }

  return (
    <div className="flex items-center gap-2 rounded-xl border bg-card p-3 shadow-sm">
      <Plus className="size-4 shrink-0 text-muted-foreground" />
      <Input
        autoFocus
        placeholder="Nome da tarefa... (Enter para salvar, Esc para cancelar)"
        value={title}
        onChange={(e) => setTitle(e.target.value)}
        onKeyDown={handleKey}
        disabled={loading}
        className="border-none shadow-none focus-visible:ring-0"
      />
      <Button size="sm" onClick={() => onSubmit(title)} disabled={loading || !title.trim()}>
        {loading ? "Salvando..." : "Salvar"}
      </Button>
      <Button size="sm" variant="ghost" onClick={onCancel}>
        Cancelar
      </Button>
    </div>
  )
}
