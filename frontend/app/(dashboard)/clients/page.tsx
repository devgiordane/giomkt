"use client"

import { useState } from "react"
import Link from "next/link"
import {
  Users,
  Plus,
  Search,
  ArrowRight,
  Mail,
  Phone,
} from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useClients } from "@/hooks/use-clients"
import type { Client } from "@/types/api"
import { cn } from "@/lib/utils"

export default function ClientsPage() {
  const [search, setSearch] = useState("")
  const [status, setStatus] = useState<"active" | "inactive" | undefined>("active")

  const { data: clients, loading, error } = useClients({ status })

  const filtered = clients?.filter((c) =>
    c.name.toLowerCase().includes(search.toLowerCase()) ||
    c.email?.toLowerCase().includes(search.toLowerCase()),
  )

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Clientes</h1>
          <p className="text-sm text-muted-foreground">
            {filtered?.length ?? 0} clientes
          </p>
        </div>
        <Button size="sm" asChild>
          <Link href="/clients/new">
            <Plus />
            Novo cliente
          </Link>
        </Button>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-2">
        <div className="relative">
          <Search className="absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Buscar cliente..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="h-8 w-56 pl-8"
          />
        </div>
        <div className="flex rounded-lg border">
          {([
            { value: "active", label: "Ativos" },
            { value: "inactive", label: "Inativos" },
          ] as const).map((opt) => (
            <button
              key={opt.value}
              onClick={() => setStatus(opt.value)}
              className={cn(
                "px-3 py-1 text-xs first:rounded-l-lg last:rounded-r-lg transition-colors",
                status === opt.value
                  ? "bg-primary text-primary-foreground"
                  : "text-muted-foreground hover:bg-muted",
              )}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      {/* Content */}
      {loading ? (
        <SkeletonTable rows={8} />
      ) : error ? (
        <EmptyState
          icon={<Users className="size-5" />}
          title="Erro ao carregar clientes"
          description={error}
        />
      ) : !filtered?.length ? (
        <EmptyState
          icon={<Users className="size-5" />}
          title="Nenhum cliente encontrado"
          description={
            search
              ? "Tente outro termo de busca."
              : "Adicione seu primeiro cliente para começar."
          }
          action={
            !search
              ? {
                  label: "Novo cliente",
                  onClick: () => window.location.assign("/clients/new"),
                }
              : undefined
          }
        />
      ) : (
        <ClientTable clients={filtered} />
      )}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Table
// ---------------------------------------------------------------------------

function ClientTable({ clients }: { clients: Client[] }) {
  return (
    <div className="rounded-xl border bg-card shadow-sm overflow-hidden">
      <table className="w-full text-sm">
        <thead>
          <tr className="border-b bg-muted/40">
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
              Nome
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground hidden md:table-cell">
              Contato
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground hidden lg:table-cell">
              Conta FB
            </th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-muted-foreground">
              Status
            </th>
            <th className="px-4 py-3" />
          </tr>
        </thead>
        <tbody>
          {clients.map((client, i) => (
            <tr
              key={client.id}
              className={cn(
                "transition-colors hover:bg-muted/30",
                i !== clients.length - 1 && "border-b",
              )}
            >
              <td className="px-4 py-3">
                <p className="font-medium">{client.name}</p>
              </td>
              <td className="px-4 py-3 hidden md:table-cell">
                <div className="space-y-0.5">
                  {client.email && (
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Mail className="size-3" />
                      {client.email}
                    </div>
                  )}
                  {client.phone && (
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                      <Phone className="size-3" />
                      {client.phone}
                    </div>
                  )}
                  {!client.email && !client.phone && (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </div>
              </td>
              <td className="px-4 py-3 hidden lg:table-cell">
                <span className="text-xs text-muted-foreground font-mono">
                  {client.fb_ad_account_id ?? "—"}
                </span>
              </td>
              <td className="px-4 py-3">
                <Badge variant={client.status === "active" ? "success" : "outline"}>
                  {client.status === "active" ? "Ativo" : "Inativo"}
                </Badge>
              </td>
              <td className="px-4 py-3 text-right">
                <Button size="icon-sm" variant="ghost" asChild>
                  <Link href={`/clients/${client.id}`}>
                    <ArrowRight className="size-4" />
                  </Link>
                </Button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
