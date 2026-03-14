"use client"

import { useState } from "react"
import { Target } from "lucide-react"
import { Select } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonCard } from "@/components/ui/skeleton"
import { useGoals } from "@/hooks/use-goals"
import { formatBRL, formatPercent } from "@/lib/utils"
import { cn } from "@/lib/utils"
import type { Goal } from "@/types/api"

const MONTHS = [
  "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
  "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro",
]

export default function GoalsPage() {
  const now = new Date()
  const [month, setMonth] = useState(now.getMonth() + 1)
  const [year, setYear] = useState(now.getFullYear())

  const { data: goals, loading, error } = useGoals({ month, year })

  const years = Array.from({ length: 3 }, (_, i) => now.getFullYear() - 1 + i)

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Metas</h1>
          <p className="text-sm text-muted-foreground">
            Progresso de vendas por produto
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Select
            value={month}
            onChange={(e) => setMonth(Number(e.target.value))}
            className="h-8 w-36"
          >
            {MONTHS.map((m, i) => (
              <option key={i} value={i + 1}>{m}</option>
            ))}
          </Select>
          <Select
            value={year}
            onChange={(e) => setYear(Number(e.target.value))}
            className="h-8 w-24"
          >
            {years.map((y) => (
              <option key={y} value={y}>{y}</option>
            ))}
          </Select>
        </div>
      </div>

      {loading ? (
        <div className="grid gap-4 md:grid-cols-2">
          {Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : error ? (
        <EmptyState
          icon={<Target className="size-5" />}
          title="Erro ao carregar metas"
          description={error}
        />
      ) : !goals?.length ? (
        <EmptyState
          icon={<Target className="size-5" />}
          title="Sem metas para este período"
          description="Configure metas por produto para acompanhar o progresso."
          className="min-h-[300px]"
        />
      ) : (
        <div className="grid gap-4 md:grid-cols-2">
          {goals.map((goal) => <GoalCard key={goal.id} goal={goal} />)}
        </div>
      )}
    </div>
  )
}

function GoalCard({ goal }: { goal: Goal }) {
  const salesPct = Math.min(goal.sales_pct, 100)
  const valPct = Math.min(goal.val_pct, 100)

  return (
    <Card>
      <CardContent className="p-5 space-y-4">
        <div className="flex items-start justify-between">
          <div>
            <p className="font-semibold">{goal.product_name}</p>
            <p className="text-xs text-muted-foreground">
              Meta: {goal.sales_target} vendas · {formatBRL(goal.revenue_target)}
            </p>
          </div>
        </div>

        {/* Sales progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Vendas</span>
            <span className="font-medium">
              {goal.actual_sales} / {goal.sales_target} ({formatPercent(salesPct)})
            </span>
          </div>
          <ProgressBar value={salesPct} />
        </div>

        {/* Revenue progress */}
        <div className="space-y-1">
          <div className="flex justify-between text-xs">
            <span className="text-muted-foreground">Receita</span>
            <span className="font-medium">
              {formatBRL(goal.actual_revenue)} / {formatBRL(goal.revenue_target)} ({formatPercent(valPct)})
            </span>
          </div>
          <ProgressBar value={valPct} color="emerald" />
        </div>

        {/* Averages */}
        <div className="flex gap-4 pt-1 border-t text-xs">
          <div>
            <p className="text-muted-foreground">Média 3m</p>
            <p className="font-medium">{formatBRL(goal.avg_revenue_3m)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Comissão</p>
            <p className="font-medium">{formatBRL(goal.actual_commission)}</p>
          </div>
          <div>
            <p className="text-muted-foreground">Meta comissão</p>
            <p className="font-medium">{formatBRL(goal.commission_target)}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function ProgressBar({ value, color = "blue" }: { value: number; color?: "blue" | "emerald" }) {
  return (
    <div className="h-2 w-full overflow-hidden rounded-full bg-muted">
      <div
        className={cn(
          "h-full rounded-full transition-all",
          color === "emerald" ? "bg-emerald-500" : "bg-primary",
          value >= 100 && "bg-emerald-500",
        )}
        style={{ width: `${value}%` }}
      />
    </div>
  )
}
