"use client"

import { useState } from "react"
import { Webhook, Plus, Trash2, Send, Power } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import {
  useWebhookSubscriptions,
  useWebhookEvents,
  useSetSubscriptionStatus,
  useDeleteWebhookSubscription,
  useTestWebhook,
} from "@/hooks/use-webhooks"
import { formatDateTime } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function WebhooksPage() {
  const [selectedId, setSelectedId] = useState<number | undefined>()

  const { data, loading, refetch } = useWebhookSubscriptions()
  const { data: events, loading: eventsLoading } = useWebhookEvents(selectedId)
  const { mutate: setStatus } = useSetSubscriptionStatus()
  const { mutate: remove } = useDeleteWebhookSubscription()
  const { mutate: testHook, loading: testing } = useTestWebhook()

  async function handleToggle(id: number, current: "active" | "disabled") {
    await setStatus({ id, status: current === "active" ? "disabled" : "active" })
    refetch()
  }

  async function handleDelete(id: number) {
    if (!confirm("Excluir esta assinatura?")) return
    await remove(id)
    refetch()
  }

  async function handleTest(id: number) {
    await testHook({ id })
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Webhooks</h1>
          <p className="text-sm text-muted-foreground">Assinaturas e eventos recebidos</p>
        </div>
        <Button size="sm">
          <Plus />
          Nova assinatura
        </Button>
      </div>

      {/* Subscriptions */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">Assinaturas</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4"><SkeletonTable rows={3} /></div>
          ) : !data?.subscriptions?.length ? (
            <EmptyState
              icon={<Webhook className="size-5" />}
              title="Sem assinaturas"
              description="Crie assinaturas para receber eventos de sistemas externos."
              className="border-0 py-10"
            />
          ) : (
            <ul>
              {data.subscriptions.map((sub, i) => (
                <li
                  key={sub.id}
                  className={cn(
                    "flex items-start gap-3 px-4 py-3 transition-colors hover:bg-muted/30 cursor-pointer",
                    i !== data.subscriptions.length - 1 && "border-b",
                    selectedId === sub.id && "bg-muted/40",
                  )}
                  onClick={() => setSelectedId(sub.id === selectedId ? undefined : sub.id)}
                >
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium">{sub.name}</p>
                    <p className="text-xs text-muted-foreground font-mono truncate">{sub.url}</p>
                    <div className="mt-1 flex flex-wrap gap-1">
                      {sub.events.map((e) => (
                        <Badge key={e} variant="secondary" className="text-[10px]">{e}</Badge>
                      ))}
                    </div>
                  </div>
                  <div className="flex items-center gap-1 shrink-0">
                    <Badge
                      variant={sub.status === "active" ? "success" : "outline"}
                      className="text-[10px]"
                    >
                      {sub.status === "active" ? "Ativo" : "Inativo"}
                    </Badge>
                    <Button
                      size="icon-xs"
                      variant="ghost"
                      onClick={(e) => { e.stopPropagation(); handleTest(sub.id) }}
                      disabled={testing}
                      title="Testar"
                    >
                      <Send />
                    </Button>
                    <Button
                      size="icon-xs"
                      variant="ghost"
                      onClick={(e) => { e.stopPropagation(); handleToggle(sub.id, sub.status) }}
                      title={sub.status === "active" ? "Desativar" : "Ativar"}
                    >
                      <Power />
                    </Button>
                    <Button
                      size="icon-xs"
                      variant="ghost"
                      onClick={(e) => { e.stopPropagation(); handleDelete(sub.id) }}
                      className="text-muted-foreground hover:text-destructive"
                    >
                      <Trash2 />
                    </Button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>

      {/* Events */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-sm">
            Eventos recebidos
            {selectedId && data?.subscriptions?.find((s) => s.id === selectedId) && (
              <span className="ml-2 text-muted-foreground font-normal">
                — {data.subscriptions.find((s) => s.id === selectedId)?.name}
              </span>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {eventsLoading ? (
            <div className="p-4"><SkeletonTable rows={3} /></div>
          ) : !events?.length ? (
            <EmptyState
              icon={<Webhook className="size-4" />}
              title={selectedId ? "Sem eventos para esta assinatura" : "Selecione uma assinatura"}
              description={selectedId ? "Nenhum evento foi recebido ainda." : "Clique em uma assinatura acima para ver seus eventos."}
              className="border-0 py-10"
            />
          ) : (
            <ul>
              {events.map((ev, i) => (
                <li
                  key={ev.id}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 text-sm",
                    i !== events.length - 1 && "border-b",
                  )}
                >
                  <Badge
                    variant={ev.processed ? "success" : "warning"}
                    className="text-[10px] shrink-0"
                  >
                    {ev.processed ? "Processado" : "Pendente"}
                  </Badge>
                  <span className="font-mono text-xs text-muted-foreground">{ev.event_type}</span>
                  <span className="ml-auto text-xs text-muted-foreground shrink-0">
                    {formatDateTime(ev.received_at)}
                  </span>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
