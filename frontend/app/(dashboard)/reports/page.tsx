"use client"

import { BarChart2 } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { useDashboardKpis } from "@/hooks/use-dashboard"
import { useSales } from "@/hooks/use-sales"
import { useGoals } from "@/hooks/use-goals"
import { SkeletonCard } from "@/components/ui/skeleton"
import { formatBRL, formatPercent } from "@/lib/utils"

export default function ReportsPage() {
  const now = new Date()
  const month = now.getMonth() + 1
  const year = now.getFullYear()

  const { data: kpis, loading: kpisLoading } = useDashboardKpis()
  const { data: sales, loading: salesLoading } = useSales({
    month: `${year}-${String(month).padStart(2, "0")}`,
  })
  const { data: goals, loading: goalsLoading } = useGoals({ month, year })

  const loading = kpisLoading || salesLoading || goalsLoading

  const avgGoalPct =
    goals?.length
      ? goals.reduce((acc, g) => acc + g.sales_pct, 0) / goals.length
      : 0

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold">Relatórios</h1>
        <p className="text-sm text-muted-foreground">
          Visão consolidada do mês de {now.toLocaleDateString("pt-BR", { month: "long", year: "numeric" })}
        </p>
      </div>

      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {loading ? (
          Array.from({ length: 6 }).map((_, i) => <SkeletonCard key={i} />)
        ) : (
          <>
            <MetricCard
              title="Clientes ativos"
              value={String(kpis?.total_clients ?? 0)}
              subtitle="total cadastrado"
            />
            <MetricCard
              title="Gasto em anúncios hoje"
              value={formatBRL(kpis?.spend_today ?? 0)}
              subtitle="Facebook Ads"
            />
            <MetricCard
              title="Campanhas ativas"
              value={String(kpis?.active_campaigns ?? 0)}
              subtitle="com gasto hoje"
            />
            <MetricCard
              title="Vendas no mês"
              value={String(sales?.kpis.total_qty ?? 0)}
              subtitle={formatBRL(sales?.kpis.total_value ?? 0)}
            />
            <MetricCard
              title="Comissões no mês"
              value={formatBRL(sales?.kpis.total_commission ?? 0)}
              subtitle={`ticket médio: ${formatBRL(sales?.kpis.avg_ticket ?? 0)}`}
            />
            <MetricCard
              title="Meta de vendas (média)"
              value={formatPercent(avgGoalPct, 1)}
              subtitle={`${goals?.length ?? 0} produtos com meta`}
              highlight={avgGoalPct >= 80}
            />
          </>
        )}
      </div>

      {/* Goals breakdown */}
      {!goalsLoading && goals?.length ? (
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">Metas por produto</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {goals.map((g) => (
              <div key={g.id} className="space-y-1">
                <div className="flex justify-between text-xs">
                  <span className="font-medium">{g.product_name}</span>
                  <span className="text-muted-foreground">
                    {g.actual_sales}/{g.sales_target} vendas ({formatPercent(g.sales_pct)})
                  </span>
                </div>
                <div className="h-1.5 w-full overflow-hidden rounded-full bg-muted">
                  <div
                    className={`h-full rounded-full transition-all ${g.sales_pct >= 100 ? "bg-emerald-500" : "bg-primary"}`}
                    style={{ width: `${Math.min(g.sales_pct, 100)}%` }}
                  />
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}
    </div>
  )
}

function MetricCard({
  title,
  value,
  subtitle,
  highlight,
}: {
  title: string
  value: string
  subtitle?: string
  highlight?: boolean
}) {
  return (
    <Card className={highlight ? "border-emerald-500/40 bg-emerald-500/5" : undefined}>
      <CardContent className="p-5">
        <p className="text-xs text-muted-foreground">{title}</p>
        <p className="mt-1 text-2xl font-bold">{value}</p>
        {subtitle && (
          <p className="mt-0.5 text-xs text-muted-foreground">{subtitle}</p>
        )}
      </CardContent>
    </Card>
  )
}
