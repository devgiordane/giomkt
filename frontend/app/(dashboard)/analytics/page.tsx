"use client"

import { useState } from "react"
import { BarChart2, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonCard, SkeletonTable } from "@/components/ui/skeleton"
import { useAnalyticsSites, useAnalyticsStats, useDeleteSite } from "@/hooks/use-analytics"
import { formatNumber, formatPercent } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function AnalyticsPage() {
  const [selectedSiteId, setSelectedSiteId] = useState<number | undefined>()
  const [period, setPeriod] = useState<7 | 30 | 90>(7)

  const { data: sitesData, loading: sitesLoading, refetch } = useAnalyticsSites()
  const { data: stats, loading: statsLoading } = useAnalyticsStats(
    selectedSiteId ?? null,
    period,
  )
  const { mutate: remove } = useDeleteSite()

  async function handleDelete(id: number) {
    if (!confirm("Excluir este site?")) return
    await remove(id)
    refetch()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Analytics</h1>
          <p className="text-sm text-muted-foreground">Estatísticas de sites via Umami</p>
        </div>
        <Button size="sm">
          <Plus />
          Adicionar site
        </Button>
      </div>

      {/* Site selector */}
      <div className="flex flex-wrap gap-2">
        <Select
          value={selectedSiteId ?? ""}
          onChange={(e) => setSelectedSiteId(e.target.value ? Number(e.target.value) : undefined)}
          className="h-8 w-56"
        >
          <option value="">Selecionar site...</option>
          {sitesData?.sites?.map((s) => (
            <option key={s.id} value={s.id}>{s.name} — {s.domain}</option>
          ))}
        </Select>
        {selectedSiteId && (
          <div className="flex rounded-lg border overflow-hidden">
            {([7, 30, 90] as const).map((p) => (
              <button
                key={p}
                onClick={() => setPeriod(p)}
                className={cn(
                  "px-3 py-1 text-xs transition-colors",
                  period === p ? "bg-primary text-primary-foreground" : "text-muted-foreground hover:bg-muted",
                )}
              >
                {p}d
              </button>
            ))}
          </div>
        )}
      </div>

      {/* Stats */}
      {selectedSiteId ? (
        <>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            {statsLoading ? (
              Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
            ) : (
              <>
                <Card>
                  <CardContent className="p-5">
                    <p className="text-xs text-muted-foreground">Pageviews</p>
                    <p className="mt-1 text-2xl font-bold">
                      {formatNumber(stats?.kpis.pageviews ?? 0)}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-5">
                    <p className="text-xs text-muted-foreground">Visitantes</p>
                    <p className="mt-1 text-2xl font-bold">
                      {formatNumber(stats?.kpis.visitors ?? 0)}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-5">
                    <p className="text-xs text-muted-foreground">Taxa de rejeição</p>
                    <p className="mt-1 text-2xl font-bold">
                      {formatPercent(stats?.kpis.bounce_rate ?? 0, 1)}
                    </p>
                  </CardContent>
                </Card>
                <Card>
                  <CardContent className="p-5">
                    <p className="text-xs text-muted-foreground">Tempo médio</p>
                    <p className="mt-1 text-2xl font-bold">
                      {Math.round((stats?.kpis.avg_time_seconds ?? 0) / 60)}min
                    </p>
                  </CardContent>
                </Card>
              </>
            )}
          </div>

          {/* Top pages */}
          {stats?.top_pages?.length ? (
            <Card>
              <CardHeader><CardTitle className="text-sm">Páginas mais acessadas</CardTitle></CardHeader>
              <CardContent className="p-0">
                <ul>
                  {stats.top_pages.map((p, i) => (
                    <li key={i} className={cn("flex items-center gap-3 px-4 py-2.5 text-sm", i < stats.top_pages.length - 1 && "border-b")}>
                      <span className="font-mono text-xs text-muted-foreground w-4">{i + 1}</span>
                      <span className="flex-1 truncate font-mono text-xs">{p.x}</span>
                      <span className="shrink-0 font-medium">{formatNumber(p.y)}</span>
                    </li>
                  ))}
                </ul>
              </CardContent>
            </Card>
          ) : null}
        </>
      ) : (
        <EmptyState
          icon={<BarChart2 className="size-5" />}
          title="Selecione um site"
          description="Escolha um site acima para visualizar suas estatísticas."
          className="min-h-70"
        />
      )}

      {/* Sites list */}
      <Card>
        <CardHeader><CardTitle className="text-sm">Sites cadastrados</CardTitle></CardHeader>
        <CardContent className="p-0">
          {sitesLoading ? (
            <div className="p-4"><SkeletonTable rows={3} /></div>
          ) : !sitesData?.sites?.length ? (
            <EmptyState
              icon={<BarChart2 className="size-4" />}
              title="Sem sites cadastrados"
              className="border-0 py-8"
            />
          ) : (
            <ul>
              {sitesData.sites.map((site, i) => (
                <li
                  key={site.id}
                  className={cn(
                    "flex items-center gap-3 px-4 py-3 text-sm hover:bg-muted/30 transition-colors",
                    i < sitesData.sites.length - 1 && "border-b",
                  )}
                >
                  <div className="flex-1 min-w-0">
                    <p className="font-medium">{site.name}</p>
                    <p className="text-xs text-muted-foreground font-mono">{site.domain}</p>
                  </div>
                  {site.client_name && (
                    <span className="text-xs text-muted-foreground shrink-0">{site.client_name}</span>
                  )}
                  <Button
                    size="icon-xs"
                    variant="ghost"
                    onClick={() => handleDelete(site.id)}
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
