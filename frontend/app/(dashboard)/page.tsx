"use client"

import Link from "next/link"
import {
  CheckSquare,
  CheckCircle2,
  Circle,
  Clock,
  ShoppingCart,
  Users,
  ArrowRight,
  CalendarClock,
  TrendingUp,
  BarChart3,
} from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { SkeletonCard, Skeleton } from "@/components/ui/skeleton"
import { EmptyState } from "@/components/ui/empty-state"
import { useDashboardKpis } from "@/hooks/use-dashboard"
import { useTasks, useToggleTask } from "@/hooks/use-tasks"
import { useSales } from "@/hooks/use-sales"
import { formatBRL, formatDate } from "@/lib/utils"
import { cn } from "@/lib/utils"
import type { Task, TaskPriority } from "@/types/api"

const PRIORITY_COLOR: Record<TaskPriority, string> = {
  1: "bg-red-500",
  2: "bg-amber-400",
  3: "bg-blue-400",
  4: "bg-muted-foreground/30",
}

export default function DashboardPage() {
  const now = new Date()
  const month = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}`
  const today = now.toISOString().slice(0, 10)

  const { data: kpis, loading: kpisLoading } = useDashboardKpis()
  const { data: tasks, loading: tasksLoading, refetch } = useTasks({ status: "pending" })
  const { data: sales, loading: salesLoading } = useSales({ month })
  const { mutate: toggle } = useToggleTask()

  async function handleToggle(id: number) {
    await toggle(id)
    refetch()
  }

  // Tarefas de hoje
  const todayTasks = (tasks ?? [])
    .filter((t) => t.due_date === today)
    .sort((a, b) => (a.start_time ?? "").localeCompare(b.start_time ?? ""))
    .slice(0, 5)

  // Próximas tarefas (sem data hoje ou sem data)
  const upcomingTasks = (tasks ?? [])
    .filter((t) => !t.due_date || t.due_date > today)
    .sort((a, b) => {
      if (!a.due_date) return 1
      if (!b.due_date) return -1
      return a.due_date.localeCompare(b.due_date)
    })
    .slice(0, 5)

  // Vendas recentes
  const recentSales = (sales?.sales ?? []).slice(0, 5)

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-xl font-semibold">Dashboard</h1>
        <p className="text-sm text-muted-foreground">
          {now.toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })}
        </p>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpisLoading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
        ) : (
          <>
            <KpiCard
              label="Clientes ativos"
              value={String(kpis?.total_clients ?? 0)}
              icon={<Users className="size-4" />}
              color="blue"
            />
            <KpiCard
              label="Tarefas pendentes"
              value={String(kpis?.pending_tasks ?? 0)}
              icon={<CheckSquare className="size-4" />}
              color="amber"
              href="/tasks"
            />
            <KpiCard
              label="Vendas no mês"
              value={String(sales?.kpis.total_qty ?? 0)}
              icon={<ShoppingCart className="size-4" />}
              color="emerald"
              href="/sales"
              loading={salesLoading}
            />
            <KpiCard
              label="Receita no mês"
              value={formatBRL(sales?.kpis.total_value ?? 0)}
              icon={<TrendingUp className="size-4" />}
              color="violet"
              href="/sales"
              loading={salesLoading}
            />
          </>
        )}
      </div>

      {/* Middle row: Hoje + Vendas */}
      <div className="grid gap-4 lg:grid-cols-2">

        {/* Tarefas de hoje */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <CalendarClock className="size-4 text-muted-foreground" />
              Tarefas de hoje
            </CardTitle>
            <Button size="xs" variant="ghost" asChild>
              <Link href="/tasks/today">Ver todas <ArrowRight className="size-3" /></Link>
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {tasksLoading ? (
              <div className="space-y-2 p-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full rounded-lg" />
                ))}
              </div>
            ) : !todayTasks.length ? (
              <EmptyState
                icon={<CalendarClock className="size-4" />}
                title="Dia livre!"
                description="Nenhuma tarefa para hoje."
                className="border-0 py-8"
              />
            ) : (
              <ul>
                {todayTasks.map((t, i) => (
                  <TaskRow
                    key={t.id}
                    task={t}
                    onToggle={handleToggle}
                    isLast={i === todayTasks.length - 1}
                    showTime
                  />
                ))}
              </ul>
            )}
          </CardContent>
        </Card>

        {/* Vendas recentes */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <ShoppingCart className="size-4 text-muted-foreground" />
              Vendas recentes
            </CardTitle>
            <Button size="xs" variant="ghost" asChild>
              <Link href="/sales">Ver todas <ArrowRight className="size-3" /></Link>
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {salesLoading ? (
              <div className="space-y-2 p-4">
                {Array.from({ length: 3 }).map((_, i) => (
                  <Skeleton key={i} className="h-10 w-full rounded-lg" />
                ))}
              </div>
            ) : !recentSales.length ? (
              <EmptyState
                icon={<ShoppingCart className="size-4" />}
                title="Sem vendas este mês"
                description="Registre vendas ou sincronize com a Eduzz."
                className="border-0 py-8"
              />
            ) : (
              <ul>
                {recentSales.map((s, i) => (
                  <li
                    key={s.id}
                    className={cn(
                      "flex items-center gap-3 px-4 py-3 text-sm hover:bg-muted/30 transition-colors",
                      i < recentSales.length - 1 && "border-b",
                    )}
                  >
                    <div className="flex-1 min-w-0">
                      <p className="truncate font-medium">{s.product}</p>
                      <p className="text-xs text-muted-foreground">{formatDate(s.date)}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <p className="font-semibold">{formatBRL(s.value)}</p>
                      <p className="text-xs text-muted-foreground">{formatBRL(s.commission_value)} comissão</p>
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Próximas tarefas */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <CheckSquare className="size-4 text-muted-foreground" />
            Próximas tarefas
          </CardTitle>
          <Button size="xs" variant="ghost" asChild>
            <Link href="/tasks">Ver todas <ArrowRight className="size-3" /></Link>
          </Button>
        </CardHeader>
        <CardContent className="p-0">
          {tasksLoading ? (
            <div className="space-y-1 p-4">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-11 w-full rounded-lg" />
              ))}
            </div>
          ) : !upcomingTasks.length ? (
            <EmptyState
              icon={<CheckSquare className="size-4" />}
              title="Sem tarefas pendentes"
              description="Ótimo trabalho! Todas as tarefas estão em dia."
              className="border-0 py-8"
            />
          ) : (
            <ul>
              {upcomingTasks.map((t, i) => (
                <TaskRow
                  key={t.id}
                  task={t}
                  onToggle={handleToggle}
                  isLast={i === upcomingTasks.length - 1}
                  showDate
                />
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Sales chart */}
      {!salesLoading && sales?.sales && sales.sales.length > 0 && (
        <SalesChart sales={sales.sales} />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// KPI Card
// ---------------------------------------------------------------------------

const colorMap = {
  blue:   "bg-blue-500/10 text-blue-600 dark:text-blue-400",
  emerald: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
  violet: "bg-violet-500/10 text-violet-600 dark:text-violet-400",
  amber:  "bg-amber-500/10 text-amber-600 dark:text-amber-400",
} as const

function KpiCard({
  label, value, icon, color, href, loading,
}: {
  label: string
  value: string
  icon: React.ReactNode
  color: keyof typeof colorMap
  href?: string
  loading?: boolean
}) {
  const content = (
    <Card className={cn("transition-colors", href && "hover:bg-muted/30 cursor-pointer")}>
      <CardContent className="p-5">
        <div className="flex items-start justify-between gap-2">
          <div className="space-y-1 min-w-0">
            <p className="text-xs text-muted-foreground">{label}</p>
            {loading ? (
              <Skeleton className="h-8 w-20" />
            ) : (
              <p className="text-2xl font-bold tracking-tight">{value}</p>
            )}
          </div>
          <div className={cn("flex size-9 shrink-0 items-center justify-center rounded-lg", colorMap[color])}>
            {icon}
          </div>
        </div>
      </CardContent>
    </Card>
  )

  if (href) return <Link href={href}>{content}</Link>
  return content
}

// ---------------------------------------------------------------------------
// Task Row
// ---------------------------------------------------------------------------

function TaskRow({
  task, onToggle, isLast, showTime, showDate,
}: {
  task: Task
  onToggle: (id: number) => void
  isLast: boolean
  showTime?: boolean
  showDate?: boolean
}) {
  return (
    <li
      className={cn(
        "flex items-center gap-3 px-4 py-2.5 hover:bg-muted/30 transition-colors",
        !isLast && "border-b",
      )}
    >
      {/* Priority dot */}
      <div className={cn("size-1.5 shrink-0 rounded-full", PRIORITY_COLOR[task.priority])} />

      {/* Toggle */}
      <button
        onClick={() => onToggle(task.id)}
        className="shrink-0 text-muted-foreground hover:text-primary transition-colors"
      >
        {task.status === "done"
          ? <CheckCircle2 className="size-4 text-emerald-500" />
          : <Circle className="size-4" />}
      </button>

      {/* Title */}
      <p className="flex-1 min-w-0 truncate text-sm">{task.title}</p>

      {/* Meta */}
      <div className="flex items-center gap-2 shrink-0">
        {showTime && task.start_time && (
          <span className="flex items-center gap-1 text-xs text-muted-foreground">
            <Clock className="size-3" />
            {task.start_time}
          </span>
        )}
        {showDate && task.due_date && (
          <Badge variant="outline" className="text-[10px]">
            {formatDate(task.due_date)}
          </Badge>
        )}
        {task.client && (
          <span className="text-xs text-muted-foreground hidden sm:inline">{task.client}</span>
        )}
      </div>
    </li>
  )
}

// ---------------------------------------------------------------------------
// Sales bar chart (receita por dia no mês)
// ---------------------------------------------------------------------------

function SalesChart({ sales }: { sales: { date: string | null; value: number; commission_value: number }[] }) {
  // Group by date — use commission_value (user's co-producer revenue)
  const byDate: Record<string, number> = {}
  for (const s of sales) {
    if (!s.date) continue
    byDate[s.date] = (byDate[s.date] ?? 0) + s.commission_value
  }

  const entries = Object.entries(byDate).sort(([a], [b]) => a.localeCompare(b))
  if (!entries.length) return null

  const max = Math.max(...entries.map(([, v]) => v), 1)

  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="flex items-center gap-2 text-sm">
          <BarChart3 className="size-4 text-muted-foreground" />
          Receita por dia — este mês
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex h-40 items-end gap-1">
          {entries.map(([date, value]) => {
            const pct = (value / max) * 100
            const label = date.slice(8) // DD
            return (
              <div
                key={date}
                className="group relative flex flex-1 flex-col items-center gap-0.5"
              >
                {/* Tooltip */}
                <div className="pointer-events-none absolute bottom-full mb-2 hidden whitespace-nowrap rounded-lg border bg-popover px-2 py-1 text-xs shadow-md group-hover:block z-10">
                  <p className="font-semibold">{formatBRL(value)}</p>
                  <p className="text-muted-foreground">{formatDate(date)}</p>
                </div>
                <div
                  className="w-full min-h-1 rounded-t-sm bg-emerald-500/70 transition-colors group-hover:bg-emerald-500"
                  style={{ height: `${Math.max(pct, 2)}%` }}
                />
                <span className="text-[9px] text-muted-foreground">{label}</span>
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
