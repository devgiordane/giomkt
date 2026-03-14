"use client"

import { useState } from "react"
import { ShoppingCart, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonCard, SkeletonTable } from "@/components/ui/skeleton"
import { useSales, useDeleteSale } from "@/hooks/use-sales"
import { formatBRL, formatDate } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function SalesPage() {
  const [month, setMonth] = useState<string | undefined>()
  const [productId, setProductId] = useState<number | undefined>()

  const { data, loading, error, refetch } = useSales({ month, product_id: productId })
  const { mutate: deleteSale } = useDeleteSale()

  async function handleDelete(id: number) {
    if (!confirm("Excluir esta venda?")) return
    await deleteSale(id)
    refetch()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Vendas</h1>
          <p className="text-sm text-muted-foreground">
            {data?.sales?.length ?? 0} vendas registradas
          </p>
        </div>
        <Button size="sm">
          <Plus />
          Registrar venda
        </Button>
      </div>

      {/* KPIs */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {loading ? (
          Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
        ) : (
          <>
            <KpiCard label="Qtd. de vendas" value={String(data?.kpis.total_qty ?? 0)} />
            <KpiCard label="Receita total" value={formatBRL(data?.kpis.total_value ?? 0)} />
            <KpiCard label="Total comissão" value={formatBRL(data?.kpis.total_commission ?? 0)} />
            <KpiCard label="Ticket médio" value={formatBRL(data?.kpis.avg_ticket ?? 0)} />
          </>
        )}
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <Select
          value={month ?? ""}
          onChange={(e) => setMonth(e.target.value || undefined)}
          className="h-8 w-36"
        >
          <option value="">Todos os meses</option>
          {data?.month_options?.map((m) => (
            <option key={m} value={m}>{m}</option>
          ))}
        </Select>
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
      </div>

      {/* Table */}
      {loading ? (
        <SkeletonTable rows={6} />
      ) : error ? (
        <EmptyState
          icon={<ShoppingCart className="size-5" />}
          title="Erro ao carregar vendas"
          description={error}
        />
      ) : !data?.sales?.length ? (
        <EmptyState
          icon={<ShoppingCart className="size-5" />}
          title="Sem vendas registradas"
          description="Registre uma venda manualmente ou sincronize com a Eduzz."
        />
      ) : (
        <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b bg-muted/40">
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Data</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Produto</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground">Valor</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground hidden md:table-cell">Comissão</th>
                <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground hidden sm:table-cell">Qtd.</th>
                <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground hidden lg:table-cell">Origem</th>
                <th className="px-4 py-3" />
              </tr>
            </thead>
            <tbody>
              {data.sales.map((sale, i) => (
                <tr
                  key={sale.id}
                  className={cn(
                    "hover:bg-muted/30 transition-colors",
                    i !== data.sales.length - 1 && "border-b",
                  )}
                >
                  <td className="px-4 py-3 text-muted-foreground text-xs">{formatDate(sale.date)}</td>
                  <td className="px-4 py-3 font-medium">{sale.product}</td>
                  <td className="px-4 py-3 text-right font-semibold">{formatBRL(sale.value)}</td>
                  <td className="px-4 py-3 text-right text-muted-foreground hidden md:table-cell">
                    {formatBRL(sale.commission_value)}
                  </td>
                  <td className="px-4 py-3 text-right text-muted-foreground hidden sm:table-cell">
                    {sale.quantity}
                  </td>
                  <td className="px-4 py-3 hidden lg:table-cell">
                    <Badge variant={sale.source === "eduzz_api" ? "info" : "outline"} className="text-[10px]">
                      {sale.source === "eduzz_api" ? "Eduzz" : "Manual"}
                    </Badge>
                  </td>
                  <td className="px-4 py-3 text-right">
                    <Button
                      size="icon-xs"
                      variant="ghost"
                      onClick={() => handleDelete(sale.id)}
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

function KpiCard({ label, value }: { label: string; value: string }) {
  return (
    <Card>
      <CardContent className="p-5">
        <p className="text-xs text-muted-foreground">{label}</p>
        <p className="mt-1 text-xl font-bold">{value}</p>
      </CardContent>
    </Card>
  )
}
