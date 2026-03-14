"use client"

import { use } from "react"
import Link from "next/link"
import {
  ArrowLeft,
  Mail,
  Phone,
  Building2,
  CheckSquare,
  FileText,
  TrendingUp,
  Edit,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { Skeleton } from "@/components/ui/skeleton"
import { useClientDetail } from "@/hooks/use-clients"
import { formatDate, formatBRL } from "@/lib/utils"

export default function ClientDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: client, loading, error } = useClientDetail(Number(id))

  if (loading) {
    return (
      <div className="space-y-5">
        <Skeleton className="h-8 w-48" />
        <div className="grid gap-4 md:grid-cols-3">
          <Skeleton className="h-32 rounded-xl" />
          <Skeleton className="h-32 rounded-xl" />
          <Skeleton className="h-32 rounded-xl" />
        </div>
        <Skeleton className="h-48 rounded-xl" />
      </div>
    )
  }

  if (error || !client) {
    return (
      <EmptyState
        icon={<Building2 className="size-5" />}
        title="Cliente não encontrado"
        description={error ?? "O cliente solicitado não existe."}
        action={{ label: "Voltar", onClick: () => history.back() }}
        className="min-h-[400px]"
      />
    )
  }

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-start gap-3">
        <Button size="icon-sm" variant="ghost" asChild>
          <Link href="/clients">
            <ArrowLeft />
          </Link>
        </Button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-semibold">{client.name}</h1>
            <Badge variant={client.status === "active" ? "success" : "outline"}>
              {client.status === "active" ? "Ativo" : "Inativo"}
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground">
            Desde {formatDate(client.created_at)}
          </p>
        </div>
        <Button size="sm" variant="outline" asChild>
          <Link href={`/clients/${id}/edit`}>
            <Edit />
            Editar
          </Link>
        </Button>
      </div>

      {/* Info cards */}
      <div className="grid gap-4 md:grid-cols-3">
        {/* Contato */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Contato</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {client.email ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Mail className="size-3.5 shrink-0" />
                {client.email}
              </div>
            ) : null}
            {client.phone ? (
              <div className="flex items-center gap-2 text-muted-foreground">
                <Phone className="size-3.5 shrink-0" />
                {client.phone}
              </div>
            ) : null}
            {!client.email && !client.phone && (
              <p className="text-muted-foreground">Sem contato cadastrado</p>
            )}
          </CardContent>
        </Card>

        {/* Orçamento */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Orçamento</CardTitle>
          </CardHeader>
          <CardContent className="space-y-1 text-sm">
            {client.budget_config ? (
              <>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Diário</span>
                  <span className="font-medium">{formatBRL(client.budget_config.daily_limit)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Mensal</span>
                  <span className="font-medium">{formatBRL(client.budget_config.monthly_limit)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-muted-foreground">Alerta</span>
                  <span className="font-medium">{client.budget_config.alert_threshold_pct}%</span>
                </div>
              </>
            ) : (
              <p className="text-muted-foreground">Sem limite configurado</p>
            )}
          </CardContent>
        </Card>

        {/* Conta FB */}
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm">Conta de Anúncios</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            {client.fb_ad_account_id ? (
              <p className="font-mono text-xs text-muted-foreground">{client.fb_ad_account_id}</p>
            ) : (
              <p className="text-muted-foreground">Não configurada</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Gasto 30d */}
      {client.spend_history_30d?.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-sm">
              <TrendingUp className="size-4" />
              Gasto nos últimos 30 dias
            </CardTitle>
          </CardHeader>
          <CardContent>
            <MiniSpendChart points={client.spend_history_30d} />
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 md:grid-cols-2">
        {/* Tarefas recentes */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <CheckSquare className="size-4" />
              Tarefas recentes
            </CardTitle>
            <Button size="xs" variant="ghost" asChild>
              <Link href={`/tasks?client_id=${id}`}>Ver todas</Link>
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {client.recent_tasks?.length ? (
              <ul>
                {client.recent_tasks.map((t, i) => (
                  <li
                    key={t.id}
                    className={`flex items-center gap-3 px-4 py-2.5 text-sm ${i !== client.recent_tasks.length - 1 ? "border-b" : ""}`}
                  >
                    <Badge
                      variant={t.status === "done" ? "success" : "outline"}
                      className="shrink-0 text-[10px]"
                    >
                      {t.status === "done" ? "Feito" : "Pendente"}
                    </Badge>
                    <span className="truncate">{t.title}</span>
                    <span className="ml-auto shrink-0 text-xs text-muted-foreground">
                      {formatDate(t.created_at)}
                    </span>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                icon={<CheckSquare className="size-4" />}
                title="Sem tarefas"
                className="border-0 py-8"
              />
            )}
          </CardContent>
        </Card>

        {/* Notas recentes */}
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="flex items-center gap-2 text-sm">
              <FileText className="size-4" />
              Notas recentes
            </CardTitle>
            <Button size="xs" variant="ghost" asChild>
              <Link href={`/notes?client_id=${id}`}>Ver todas</Link>
            </Button>
          </CardHeader>
          <CardContent className="p-0">
            {client.recent_notes?.length ? (
              <ul>
                {client.recent_notes.map((n, i) => (
                  <li
                    key={n.id}
                    className={`px-4 py-2.5 text-sm ${i !== client.recent_notes.length - 1 ? "border-b" : ""}`}
                  >
                    <p className="line-clamp-2 text-muted-foreground">{n.content}</p>
                    <p className="mt-0.5 text-xs text-muted-foreground/60">
                      {formatDate(n.created_at)}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState
                icon={<FileText className="size-4" />}
                title="Sem notas"
                className="border-0 py-8"
              />
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

// ---------------------------------------------------------------------------
// Mini spend chart
// ---------------------------------------------------------------------------

function MiniSpendChart({ points }: { points: { date: string; spend: number }[] }) {
  const max = Math.max(...points.map((p) => p.spend), 1)
  return (
    <div className="flex h-20 items-end gap-0.5">
      {points.map((p) => (
        <div
          key={p.date}
          className="group relative flex-1"
          title={`${formatDate(p.date)}: ${formatBRL(p.spend)}`}
        >
          <div
            className="w-full rounded-sm bg-primary/60 transition-all group-hover:bg-primary"
            style={{ height: `${Math.max((p.spend / max) * 100, 4)}%` }}
          />
        </div>
      ))}
    </div>
  )
}
