"use client"

import { Package, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useProducts, useDeleteProduct } from "@/hooks/use-products"
import { formatBRL, formatPercent } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function ProductsPage() {
  const { data, loading, error, refetch } = useProducts()
  const { mutate: remove } = useDeleteProduct()

  async function handleDelete(id: number) {
    if (!confirm("Excluir este produto?")) return
    await remove(id)
    refetch()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Produtos</h1>
          <p className="text-sm text-muted-foreground">
            {data?.products?.length ?? 0} produtos cadastrados
          </p>
        </div>
        <Button size="sm">
          <Plus />
          Novo produto
        </Button>
      </div>

      {loading ? (
        <SkeletonTable rows={5} />
      ) : error ? (
        <EmptyState
          icon={<Package className="size-5" />}
          title="Erro ao carregar produtos"
          description={error}
        />
      ) : !data?.products?.length ? (
        <EmptyState
          icon={<Package className="size-5" />}
          title="Sem produtos cadastrados"
          description="Cadastre os produtos da Eduzz para rastrear vendas e metas."
        />
      ) : (
        <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Nome</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground hidden md:table-cell">Conta</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground">Preço</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground hidden sm:table-cell">Comissão</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Status</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {data.products.map((p, i) => (
                <tr
                  key={p.id}
                  className={cn(
                    "hover:bg-muted/30 transition-colors",
                    i !== data.products.length - 1 && "border-b",
                  )}
                >
                  <td className="px-4 py-3">
                    <p className="font-medium">{p.name}</p>
                    {p.product_id_eduzz && (
                      <p className="text-[10px] font-mono text-muted-foreground">{p.product_id_eduzz}</p>
                    )}
                  </td>
                  <td className="px-4 py-3 text-muted-foreground hidden md:table-cell">{p.account_name}</td>
                  <td className="px-4 py-3 text-right font-medium">{formatBRL(p.price)}</td>
                  <td className="px-4 py-3 text-right text-muted-foreground hidden sm:table-cell">
                    {formatPercent(p.commission_percent)}
                  </td>
                  <td className="px-4 py-3">
                    <Badge variant={p.active ? "success" : "outline"} className="text-[10px]">
                      {p.active ? "Ativo" : "Inativo"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="icon-xs"
                      variant="ghost"
                      onClick={() => handleDelete(p.id)}
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
