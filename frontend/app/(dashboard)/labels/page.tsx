"use client"

import { useState } from "react"
import { Tag, Plus, Trash2, Pencil } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useLabels, useCreateLabel, useDeleteLabel } from "@/hooks/use-labels"
import { cn } from "@/lib/utils"

const PRESET_COLORS = [
  "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
  "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16",
]

export default function LabelsPage() {
  const { data: labels, loading, error, refetch } = useLabels()
  const { mutate: create, loading: creating } = useCreateLabel()
  const { mutate: remove } = useDeleteLabel()

  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState("")
  const [color, setColor] = useState(PRESET_COLORS[0])

  async function handleCreate() {
    if (!name.trim()) return
    await create({ name, color })
    setName("")
    setColor(PRESET_COLORS[0])
    setShowForm(false)
    refetch()
  }

  async function handleDelete(id: number) {
    if (!confirm("Excluir esta label?")) return
    await remove(id)
    refetch()
  }

  return (
    <div className="space-y-5 max-w-lg">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Labels</h1>
          <p className="text-sm text-muted-foreground">Etiquetas para organizar tarefas</p>
        </div>
        <Button size="sm" onClick={() => setShowForm(true)}>
          <Plus />
          Nova label
        </Button>
      </div>

      {/* Create form */}
      {showForm && (
        <div className="rounded-xl border bg-card p-4 shadow-sm space-y-3">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Nome</label>
            <Input
              autoFocus
              placeholder="Ex: Urgente, Reunião, Proposta..."
              value={name}
              onChange={(e) => setName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreate()}
            />
          </div>
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Cor</label>
            <div className="flex items-center gap-2">
              {PRESET_COLORS.map((c) => (
                <button
                  key={c}
                  onClick={() => setColor(c)}
                  className={cn(
                    "size-6 rounded-full transition-transform hover:scale-110",
                    color === c && "ring-2 ring-offset-2 ring-ring",
                  )}
                  style={{ backgroundColor: c }}
                />
              ))}
              <input
                type="color"
                value={color}
                onChange={(e) => setColor(e.target.value)}
                className="size-6 cursor-pointer rounded-full border-0 p-0"
              />
            </div>
          </div>
          <div className="flex gap-2">
            <Button size="sm" onClick={handleCreate} disabled={creating || !name.trim()}>
              {creating ? "Salvando..." : "Criar label"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => { setShowForm(false); setName("") }}>
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {/* List */}
      {loading ? (
        <SkeletonTable rows={4} />
      ) : error ? (
        <EmptyState
          icon={<Tag className="size-5" />}
          title="Erro ao carregar labels"
          description={error}
        />
      ) : !labels?.length ? (
        <EmptyState
          icon={<Tag className="size-5" />}
          title="Sem labels criadas"
          description="Crie labels para organizar e filtrar suas tarefas."
          action={{ label: "Criar label", onClick: () => setShowForm(true) }}
        />
      ) : (
        <div className="rounded-xl border bg-card shadow-sm divide-y overflow-hidden">
          {labels.map((label) => (
            <div key={label.id} className="flex items-center gap-3 px-4 py-3 hover:bg-muted/30 transition-colors">
              <div
                className="size-3.5 shrink-0 rounded-full"
                style={{ backgroundColor: label.color }}
              />
              <span
                className="inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-xs font-medium"
                style={{ backgroundColor: label.color + "25", color: label.color }}
              >
                {label.name}
              </span>
              <span className="ml-auto flex items-center gap-1">
                <Button
                  size="icon-xs"
                  variant="ghost"
                  className="text-muted-foreground"
                >
                  <Pencil />
                </Button>
                <Button
                  size="icon-xs"
                  variant="ghost"
                  onClick={() => handleDelete(label.id)}
                  className="text-muted-foreground hover:text-destructive"
                >
                  <Trash2 />
                </Button>
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
