"use client"

import { useState } from "react"
import { MessageSquare, Plus, Trash2, Power } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import {
  useMessageFlows,
  useToggleMessageFlow,
  useDeleteMessageFlow,
} from "@/hooks/use-message-flows"
import { cn } from "@/lib/utils"
import type { SaleStatus } from "@/types/api"

const STATUS_LABEL: Record<SaleStatus, string> = {
  waitingPayment: "Aguardando pagto.",
  paid: "Pago",
  canceled: "Cancelado",
  recovering: "Em recuperação",
  refunded: "Reembolsado",
  expired: "Expirado",
}

const STATUS_VARIANT: Record<SaleStatus, "info" | "success" | "destructive" | "warning" | "outline"> = {
  waitingPayment: "info",
  paid: "success",
  canceled: "destructive",
  recovering: "warning",
  refunded: "outline",
  expired: "outline",
}

export default function MessageFlowsPage() {
  const [productId, setProductId] = useState<number | undefined>()

  const { data, loading, error, refetch } = useMessageFlows(productId)
  const { mutate: toggle } = useToggleMessageFlow()
  const { mutate: remove } = useDeleteMessageFlow()

  async function handleToggle(id: number) {
    await toggle(id)
    refetch()
  }

  async function handleDelete(id: number) {
    if (!confirm("Excluir este fluxo?")) return
    await remove(id)
    refetch()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Fluxos de Mensagem</h1>
          <p className="text-sm text-muted-foreground">
            Mensagens automáticas disparadas por eventos de venda
          </p>
        </div>
        <Button size="sm">
          <Plus />
          Novo fluxo
        </Button>
      </div>

      {/* Filter */}
      <Select
        value={productId ?? ""}
        onChange={(e) => setProductId(e.target.value ? Number(e.target.value) : undefined)}
        className="h-8 w-48"
      >
        <option value="">Todos os produtos</option>
        {data?.product_options?.map((p) => (
          <option key={p.id} value={p.id}>{p.name}</option>
        ))}
      </Select>

      {/* Content */}
      {loading ? (
        <SkeletonTable rows={5} />
      ) : error ? (
        <EmptyState
          icon={<MessageSquare className="size-5" />}
          title="Erro ao carregar fluxos"
          description={error}
        />
      ) : !data?.flows?.length ? (
        <EmptyState
          icon={<MessageSquare className="size-5" />}
          title="Sem fluxos configurados"
          description="Crie fluxos para enviar mensagens automáticas ao WhatsApp quando uma venda mudar de status."
          action={{ label: "Criar fluxo", onClick: () => {} }}
        />
      ) : (
        <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Produto</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Gatilho</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground hidden md:table-cell">Template</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground hidden sm:table-cell">Delay</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {data.flows.map((flow, i) => (
                <tr
                  key={flow.id}
                  className={cn(
                    "hover:bg-muted/30 transition-colors",
                    i !== data.flows.length - 1 && "border-b",
                  )}
                >
                  <td className="px-4 py-3 font-medium">{flow.product_name}</td>
                  <td className="px-4 py-3">
                    <Badge variant={STATUS_VARIANT[flow.status]} className="text-[10px]">
                      {STATUS_LABEL[flow.status]}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">
                    <p className="truncate max-w-xs text-xs">{flow.template}</p>
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground text-xs hidden sm:table-cell">
                    {flow.delay_minutes ? `${flow.delay_minutes}min` : "Imediato"}
                  </td>
                  <td className="px-4 py-3">
                    <button
                      onClick={() => handleToggle(flow.id)}
                      className={cn(
                        "flex items-center gap-1.5 rounded-full px-2 py-0.5 text-xs transition-colors",
                        flow.active
                          ? "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400"
                          : "bg-muted text-muted-foreground",
                      )}
                    >
                      <Power className="size-3" />
                      {flow.active ? "Ativo" : "Inativo"}
                    </button>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="icon-xs"
                      variant="ghost"
                      onClick={() => handleDelete(flow.id)}
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
