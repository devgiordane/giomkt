"use client"

import { useState } from "react"
import { Zap, Plus, Trash2, RefreshCw, ExternalLink } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useEduzzAccounts, useDeleteEduzzAccount } from "@/hooks/use-eduzz"
import { api } from "@/lib/api"
import { formatDate } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function EduzzPage() {
  const { data: accounts, loading, error, refetch } = useEduzzAccounts()
  const { mutate: remove } = useDeleteEduzzAccount()
  const [syncingId, setSyncingId] = useState<number | null>(null)

  async function handleDelete(id: number) {
    if (!confirm("Excluir esta conta?")) return
    await remove(id)
    refetch()
  }

  async function handleSync(id: number) {
    setSyncingId(id)
    try {
      await api.post(`/eduzz/accounts/${id}/sync`, {})
      refetch()
    } finally {
      setSyncingId(null)
    }
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Contas Eduzz</h1>
          <p className="text-sm text-muted-foreground">
            Gerencie as integrações com a plataforma Eduzz
          </p>
        </div>
        <Button size="sm">
          <Plus />
          Adicionar conta
        </Button>
      </div>

      {loading ? (
        <SkeletonTable rows={3} />
      ) : error ? (
        <EmptyState
          icon={<Zap className="size-5" />}
          title="Erro ao carregar contas"
          description={error}
        />
      ) : !accounts?.length ? (
        <EmptyState
          icon={<Zap className="size-5" />}
          title="Sem contas Eduzz"
          description="Conecte uma conta Eduzz para sincronizar vendas automaticamente."
          className="min-h-75"
        />
      ) : (
        <div className="rounded-xl border bg-card shadow-sm divide-y overflow-hidden">
          {accounts.map((account) => (
            <div key={account.id} className="flex items-center gap-4 px-4 py-4 hover:bg-muted/30 transition-colors">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <p className="font-medium">{account.name}</p>
                  <Badge
                    variant={account.connected ? "success" : "destructive"}
                    className="text-[10px]"
                  >
                    {account.connected ? "Conectado" : "Desconectado"}
                  </Badge>
                  {!account.active && (
                    <Badge variant="outline" className="text-[10px]">Inativo</Badge>
                  )}
                </div>
                {account.email && (
                  <p className="text-xs text-muted-foreground mt-0.5">{account.email}</p>
                )}
                {account.created_at && (
                  <p className="text-xs text-muted-foreground/60 mt-0.5">
                    Criado em {formatDate(account.created_at)}
                  </p>
                )}
              </div>

              <div className="flex items-center gap-1 shrink-0">
                {!account.connected && (
                  <Button size="xs" variant="outline" asChild>
                    <a href={account.auth_url} target="_blank" rel="noreferrer">
                      <ExternalLink className="size-3" />
                      Conectar
                    </a>
                  </Button>
                )}
                {account.connected && (
                  <Button
                    size="xs"
                    variant="outline"
                    onClick={() => handleSync(account.id)}
                    disabled={syncingId === account.id}
                  >
                    <RefreshCw className={cn("size-3", syncingId === account.id && "animate-spin")} />
                    Sincronizar
                  </Button>
                )}
                <Button
                  size="icon-xs"
                  variant="ghost"
                  onClick={() => handleDelete(account.id)}
                  className="text-muted-foreground hover:text-destructive"
                >
                  <Trash2 />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
