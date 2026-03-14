"use client"

import { useState } from "react"
import { FileText, Plus, Trash2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Select } from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useNotes, useCreateNote, useDeleteNote } from "@/hooks/use-notes"
import { formatDateTime } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function NotesPage() {
  const [clientId, setClientId] = useState<number | undefined>()
  const [showCreate, setShowCreate] = useState(false)
  const [newContent, setNewContent] = useState("")

  const { data, loading, error, refetch } = useNotes({ client_id: clientId })
  const { mutate: createNote, loading: creating } = useCreateNote()
  const { mutate: deleteNote } = useDeleteNote()

  async function handleCreate() {
    if (!newContent.trim()) return
    await createNote({ content: newContent, client_id: clientId })
    setNewContent("")
    setShowCreate(false)
    refetch()
  }

  async function handleDelete(id: number) {
    if (!confirm("Excluir esta nota?")) return
    await deleteNote(id)
    refetch()
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Notas</h1>
          <p className="text-sm text-muted-foreground">
            {data?.notes?.length ?? 0} notas
          </p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus />
          Nova nota
        </Button>
      </div>

      {/* Filter */}
      <Select
        value={clientId ?? ""}
        onChange={(e) => setClientId(e.target.value ? Number(e.target.value) : undefined)}
        className="h-8 w-48"
      >
        <option value="">Todos os clientes</option>
        {data?.client_options?.map((c) => (
          <option key={c.id} value={c.id}>{c.name}</option>
        ))}
      </Select>

      {/* Create form */}
      {showCreate && (
        <div className="rounded-xl border bg-card p-4 shadow-sm space-y-3">
          <Textarea
            autoFocus
            placeholder="Conteúdo da nota..."
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            className="min-h-[100px]"
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleCreate} disabled={creating || !newContent.trim()}>
              {creating ? "Salvando..." : "Salvar nota"}
            </Button>
            <Button size="sm" variant="ghost" onClick={() => { setShowCreate(false); setNewContent("") }}>
              Cancelar
            </Button>
          </div>
        </div>
      )}

      {/* Content */}
      {loading ? (
        <SkeletonTable rows={4} />
      ) : error ? (
        <EmptyState
          icon={<FileText className="size-5" />}
          title="Erro ao carregar notas"
          description={error}
        />
      ) : !data?.notes?.length ? (
        <EmptyState
          icon={<FileText className="size-5" />}
          title="Sem notas"
          description="Registre observações importantes sobre clientes e projetos."
          action={{ label: "Nova nota", onClick: () => setShowCreate(true) }}
        />
      ) : (
        <div className="space-y-3">
          {data.notes.map((note) => (
            <div key={note.id} className="group rounded-xl border bg-card p-4 shadow-sm">
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <p className="whitespace-pre-wrap text-sm">{note.content}</p>
                  <div className="mt-2 flex items-center gap-3 text-xs text-muted-foreground">
                    {note.client_name && (
                      <span className="font-medium">{note.client_name}</span>
                    )}
                    <span>{formatDateTime(note.created_at)}</span>
                  </div>
                </div>
                <Button
                  size="icon-xs"
                  variant="ghost"
                  onClick={() => handleDelete(note.id)}
                  className={cn(
                    "shrink-0 text-muted-foreground hover:text-destructive",
                    "opacity-0 group-hover:opacity-100 transition-opacity",
                  )}
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
