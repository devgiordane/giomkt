"use client"

import { Server, AlertTriangle, Plus, Trash2 } from "lucide-react"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonCard, SkeletonTable } from "@/components/ui/skeleton"
import { useServices, useDeleteService } from "@/hooks/use-services"
import { formatBRL, formatDate } from "@/lib/utils"
import { cn } from "@/lib/utils"
import type { Service } from "@/types/api"

const TYPE_LABEL: Record<string, string> = {
  dominio: "Domínio",
  hospedagem: "Hospedagem",
  servidor: "Servidor",
  api: "API",
  software: "Software",
}

export default function ServicesPage() {
  const { data, loading, error, refetch } = useServices()
  const { mutate: deleteService } = useDeleteService()

  async function handleDelete(id: number) {
    if (!confirm("Excluir este serviço?")) return
    await deleteService(id)
    refetch()
  }

  const today = new Date().toISOString().slice(0, 10)
  const in7d = new Date(Date.now() + 7 * 864e5).toISOString().slice(0, 10)
  const in30d = new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10)

  function expiryBadge(service: Service) {
    if (!service.due_date) return null
    if (service.due_date <= today) return <Badge variant="destructive">Vencido</Badge>
    if (service.due_date <= in7d) return <Badge variant="warning">Vence em 7d</Badge>
    if (service.due_date <= in30d) return <Badge variant="info">Vence em 30d</Badge>
    return null
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Serviços</h1>
          <p className="text-sm text-muted-foreground">Assinaturas e serviços contratados</p>
        </div>
        <Button size="sm">
          <Plus />
          Novo serviço
        </Button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
        ) : (
          <>
            <Card>
              <CardContent className="p-5">
                <div className="flex items-center gap-1.5 text-xs text-amber-600 dark:text-amber-400">
                  <AlertTriangle className="size-3.5" />
                  Vencem em 7 dias
                </div>
                <p className="mt-1 text-2xl font-bold">{data?.kpis.expiring_7d ?? 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-muted-foreground">Vencem em 30 dias</p>
                <p className="mt-1 text-2xl font-bold">{data?.kpis.expiring_30d ?? 0}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-muted-foreground">Total mensal</p>
                <p className="mt-1 text-2xl font-bold">{formatBRL(data?.kpis.monthly_total ?? 0)}</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-muted-foreground">Total anual</p>
                <p className="mt-1 text-2xl font-bold">{formatBRL(data?.kpis.annual_total ?? 0)}</p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Table */}
      {loading ? (
        <SkeletonTable rows={6} />
      ) : error ? (
        <EmptyState
          icon={<Server className="size-5" />}
          title="Erro ao carregar serviços"
          description={error}
        />
      ) : !data?.services?.length ? (
        <EmptyState
          icon={<Server className="size-5" />}
          title="Sem serviços cadastrados"
          description="Adicione domínios, hospedagens e outras assinaturas para monitorar vencimentos."
        />
      ) : (
        <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Nome</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Tipo</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground hidden md:table-cell">Cliente</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground">Valor</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground hidden sm:table-cell">Vencimento</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {data.services.map((s, i) => (
                <tr
                  key={s.id}
                  className={cn(
                    "hover:bg-muted/30 transition-colors",
                    i !== data.services.length - 1 && "border-b",
                  )}
                >
                  <td className="px-4 py-3 font-medium">{s.name}</td>
                  <td className="px-4 py-3">
                    <Badge variant="secondary" className="text-[10px]">
                      {TYPE_LABEL[s.type] ?? s.type}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">
                    {s.client_name || "—"}
                  </td>
                  <td className="px-4 py-3 text-right">
                    <span className="font-medium">{formatBRL(s.value)}</span>
                    <span className="ml-1 text-xs text-muted-foreground">
                      /{s.billing_cycle === "monthly" ? "mês" : "ano"}
                    </span>
                  </td>
                  <td className="px-4 py-3 hidden sm:table-cell">
                    <div className="flex items-center gap-2">
                      <span className="text-muted-foreground text-xs">{formatDate(s.due_date)}</span>
                      {expiryBadge(s)}
                    </div>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="icon-xs"
                      variant="ghost"
                      onClick={() => handleDelete(s.id)}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 />
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
