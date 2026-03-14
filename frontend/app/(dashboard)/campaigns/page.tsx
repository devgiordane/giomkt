"use client"

import { Megaphone, TrendingUp } from "lucide-react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonCard, SkeletonTable } from "@/components/ui/skeleton"
import { useCampaigns } from "@/hooks/use-campaigns"
import { formatBRL, formatNumber } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function CampaignsPage() {
  const { data, loading, error } = useCampaigns()

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-xl font-semibold">Campanhas</h1>
        <p className="text-sm text-muted-foreground">Gasto em anúncios por cliente</p>
      </div>

      {/* Today summary */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        {loading ? (
          <>
            <SkeletonCard />
            <SkeletonCard />
            <SkeletonCard />
          </>
        ) : (
          <>
            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-muted-foreground">Gasto total hoje</p>
                <p className="mt-1 text-2xl font-bold">
                  {formatBRL(data?.total_spend_today ?? 0)}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-muted-foreground">Clientes ativos hoje</p>
                <p className="mt-1 text-2xl font-bold">
                  {data?.today_by_client?.length ?? 0}
                </p>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="p-5">
                <p className="text-xs text-muted-foreground">Total de snapshots</p>
                <p className="mt-1 text-2xl font-bold">
                  {data?.snapshots?.length ?? 0}
                </p>
              </CardContent>
            </Card>
          </>
        )}
      </div>

      {/* Today by client */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <TrendingUp className="size-4" />
            Gasto de hoje por cliente
          </CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4">
              <SkeletonTable rows={4} />
            </div>
          ) : !data?.today_by_client?.length ? (
            <EmptyState
              icon={<Megaphone className="size-5" />}
              title="Sem dados hoje"
              description="Nenhum snapshot registrado para hoje ainda."
              className="border-0 py-10"
            />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Cliente</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground">Gasto</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground hidden sm:table-cell">Impressões</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground hidden sm:table-cell">Cliques</th>
                </tr>
              </thead>
              <tbody>
                {data.today_by_client.map((row, i) => (
                  <tr
                    key={row.client_id}
                    className={cn(
                      "hover:bg-muted/30 transition-colors",
                      i !== data.today_by_client.length - 1 && "border-b",
                    )}
                  >
                    <td className="px-4 py-3 font-medium">{row.client_name}</td>
                    <td className="px-4 py-3 text-right font-semibold">
                      {formatBRL(row.spend)}
                    </td>
                    <td className="px-4 py-3 text-right text-muted-foreground hidden sm:table-cell">
                      {formatNumber(row.impressions)}
                    </td>
                    <td className="px-4 py-3 text-right text-muted-foreground hidden sm:table-cell">
                      {formatNumber(row.clicks)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>

      {/* Snapshot history */}
      <Card>
        <CardHeader>
          <CardTitle className="text-sm">Histórico de snapshots</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading ? (
            <div className="p-4"><SkeletonTable rows={5} /></div>
          ) : !data?.snapshots?.length ? (
            <EmptyState
              icon={<Megaphone className="size-5" />}
              title="Sem histórico"
              description="Nenhum snapshot registrado."
              className="border-0 py-10"
            />
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b bg-muted/40">
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Data</th>
                  <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">Cliente</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground">Gasto</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground hidden md:table-cell">Impressões</th>
                  <th className="px-4 py-3 text-right text-xs font-semibold text-muted-foreground hidden md:table-cell">Cliques</th>
                </tr>
              </thead>
              <tbody>
                {data.snapshots.slice(0, 50).map((s, i) => (
                  <tr
                    key={s.id}
                    className={cn(
                      "hover:bg-muted/30 transition-colors",
                      i !== Math.min(data.snapshots.length, 50) - 1 && "border-b",
                    )}
                  >
                    <td className="px-4 py-2.5 text-muted-foreground text-xs font-mono">{s.date}</td>
                    <td className="px-4 py-2.5 font-medium">{s.client_name}</td>
                    <td className="px-4 py-2.5 text-right">{formatBRL(s.spend)}</td>
                    <td className="px-4 py-2.5 text-right text-muted-foreground hidden md:table-cell">{formatNumber(s.impressions)}</td>
                    <td className="px-4 py-2.5 text-right text-muted-foreground hidden md:table-cell">{formatNumber(s.clicks)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
