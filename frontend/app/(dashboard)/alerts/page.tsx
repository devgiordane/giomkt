"use client"

import { Bell, CheckCheck, Plus, Trash2, RefreshCw } from "lucide-react"
import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import {
  useAlerts,
  useResolveAlert,
  useCheckAlerts,
  useAlertRules,
  useDeleteAlertRule,
} from "@/hooks/use-alerts"
import { formatDateTime } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function AlertsPage() {
  const [showResolved, setShowResolved] = useState(false)

  const { data: alerts, loading, refetch } = useAlerts(showResolved)
  const { data: rulesData, loading: rulesLoading, refetch: refetchRules } = useAlertRules()
  const { mutate: resolve } = useResolveAlert()
  const { mutate: check, loading: checking } = useCheckAlerts()
  const { mutate: deleteRule } = useDeleteAlertRule()

  async function handleResolve(id: number) {
    await resolve(id)
    refetch()
  }

  async function handleCheck() {
    const res = await check(undefined)
    if (res) refetch()
  }

  async function handleDeleteRule(id: number) {
    if (!confirm("Excluir esta regra?")) return
    await deleteRule(id)
    refetchRules()
  }

  const RULE_TYPE_LABEL: Record<string, string> = {
    daily_budget: "Orçamento diário",
    monthly_budget: "Orçamento mensal",
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Alertas</h1>
          <p className="text-sm text-muted-foreground">Monitoramento de orçamentos</p>
        </div>
        <div className="flex gap-2">
          <Button size="sm" variant="outline" onClick={handleCheck} disabled={checking}>
            <RefreshCw className={cn("size-4", checking && "animate-spin")} />
            Verificar agora
          </Button>
          <Button size="sm">
            <Plus />
            Nova regra
          </Button>
        </div>
      </div>

      {/* Alerts */}
      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-3">
          <CardTitle className="flex items-center gap-2 text-sm">
            <Bell className="size-4" />
            Alertas disparados
          </CardTitle>
          <div className="flex rounded-lg border text-xs overflow-hidden">
            <button
              onClick={() => setShowResolved(false)}
              className={cn(
                "px-3 py-1 transition-colors",
                !showResolved ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
              )}
            >
              Ativos
            </button>
            <button
              onClick={() => setShowResolved(true)}
              className={cn(
                "px-3 py-1 transition-colors",
                showResolved ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
              )}
            >
              Resolvidos
            </button>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4"><SkeletonTable rows={3} /></div>
          ) : !alerts?.length ? (
            <EmptyState
              icon={<Bell className="size-5" />}
              title={showResolved ? "Sem alertas resolvidos" : "Nenhum alerta ativo"}
              description={showResolved ? "" : "Todos os orçamentos estão dentro do limite."}
              className="border-0 py-10"
            />
          ) : (
            <ul>
              {alerts.map((alert, i) => (
                <li
                  key={alert.id}
                  className={cn(
                    "flex items-start gap-3 px-4 py-3 transition-colors hover:bg-muted/30",
                    i !== alerts.length - 1 && "border-b",
                  )}
                >
                  <div className="mt-0.5 size-2 shrink-0 rounded-full bg-amber-400" />
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{alert.client_name}</p>
                    <p className="text-xs text-muted-foreground">{alert.message}</p>
                    <p className="text-[10px] text-muted-foreground/60 mt-0.5">
                      {formatDateTime(alert.triggered_at)}
                    </p>
                  </div>
                  {!alert.resolved && (
                    <Button
                      size="xs"
                      variant="outline"
                      onClick={() => handleResolve(alert.id)}
                    >
                      <CheckCheck className="size-3" />
                      Resolver
                    </Button>
                  )}
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Rules */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Regras de alerta</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {rulesLoading ? (
            <div className="p-4"><SkeletonTable rows={3} /></div>
          ) : !rulesData?.rules?.length ? (
            <EmptyState
              icon={<Bell className="size-4" />}
              title="Sem regras configuradas"
              description="Crie regras para receber alertas quando orçamentos forem atingidos."
              className="border-0 py-10"
            />
          ) : (
            <ul>
              {rulesData.rules.map((rule, i) => (
                <li
                  key={rule.id}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 transition-colors hover:bg-muted/30",
                    i !== rulesData.rules.length - 1 && "border-b",
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{rule.client_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {RULE_TYPE_LABEL[rule.rule_type]} — {rule.threshold}%
                    </p>
                  </div>
                  <Badge variant={rule.active ? "success" : "outline"} className="text-[10px] shrink-0">
                    {rule.active ? "Ativa" : "Inativa"}
                  </Badge>
                  <Button
                    size="icon-xs"
                    variant="ghost"
                    onClick={() => handleDeleteRule(rule.id)}
                    className="text-muted-foreground hover:text-destructive"
                  >
                    <Trash2 />
                  </Button>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
