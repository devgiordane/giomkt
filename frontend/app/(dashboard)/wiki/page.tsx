"use client"

import { useState } from "react"
import { BookOpen, Plus, Trash2, Pencil, Check, X } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { EmptyState } from "@/components/ui/empty-state"
import { SkeletonTable } from "@/components/ui/skeleton"
import { useNotes, useCreateNote, useUpdateNote, useDeleteNote } from "@/hooks/use-notes"
import { formatDateTime } from "@/lib/utils"
import { cn } from "@/lib/utils"

export default function WikiPage() {
  const { data, loading, error, refetch } = useNotes({ wiki: true })
  const { mutate: create, loading: creating } = useCreateNote()
  const { mutate: update, loading: updating } = useUpdateNote()
  const { mutate: remove } = useDeleteNote()

  const [showCreate, setShowCreate] = useState(false)
  const [newContent, setNewContent] = useState("")
  const [editingId, setEditingId] = useState<number | null>(null)
  const [editContent, setEditContent] = useState("")

  async function handleCreate() {
    if (!newContent.trim()) return
    await create({ content: newContent })
    setNewContent("")
    setShowCreate(false)
    refetch()
  }

  function startEdit(id: number, content: string) {
    setEditingId(id)
    setEditContent(content)
  }

  async function handleUpdate(id: number) {
    if (!editContent.trim()) return
    await update({ id, content: editContent })
    setEditingId(null)
    refetch()
  }

  async function handleDelete(id: number) {
    if (!confirm("Excluir esta nota da wiki?")) return
    await remove(id)
    refetch()
  }

  return (
    <div className="space-y-5 max-w-2xl">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Wiki</h1>
          <p className="text-sm text-muted-foreground">Base de conhecimento interna</p>
        </div>
        <Button size="sm" onClick={() => setShowCreate(true)}>
          <Plus />
          Nova entrada
        </Button>
      </div>

      {/* Create */}
      {showCreate && (
        <div className="rounded-xl border bg-card p-4 shadow-sm space-y-3">
          <Textarea
            autoFocus
            placeholder="Escreva sua nota wiki aqui..."
            value={newContent}
            onChange={(e) => setNewContent(e.target.value)}
            className="min-h-[120px]"
          />
          <div className="flex gap-2">
            <Button size="sm" onClick={handleCreate} disabled={creating || !newContent.trim()}>
              {creating ? "Salvando..." : "Salvar"}
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
          icon={<BookOpen className="size-5" />}
          title="Erro ao carregar wiki"
          description={error}
        />
      ) : !data?.notes?.length ? (
        <EmptyState
          icon={<BookOpen className="size-5" />}
          title="Wiki vazia"
          description="Registre processos, roteiros e conhecimentos importantes da equipe."
          action={{ label: "Nova entrada", onClick: () => setShowCreate(true) }}
          className="min-h-[300px]"
        />
      ) : (
        <div className="space-y-3">
          {data.notes.map((note) => (
            <div key={note.id} className="group rounded-xl border bg-card shadow-sm">
              {editingId === note.id ? (
                <div className="p-4 space-y-3">
                  <Textarea
                    autoFocus
                    value={editContent}
                    onChange={(e) => setEditContent(e.target.value)}
                    className="min-h-[100px]"
                  />
                  <div className="flex gap-2">
                    <Button size="sm" onClick={() => handleUpdate(note.id)} disabled={updating}>
                      <Check className="size-3.5" />
                      Salvar
                    </Button>
                    <Button size="sm" variant="ghost" onClick={() => setEditingId(null)}>
                      <X className="size-3.5" />
                      Cancelar
                    </Button>
                  </div>
                </div>
              ) : (
                <div className="p-4">
                  <div className="flex items-start gap-2">
                    <p className="flex-1 whitespace-pre-wrap text-sm">{note.content}</p>
                    <div className={cn(
                      "flex items-center gap-1 shrink-0",
                      "opacity-0 group-hover:opacity-100 transition-opacity",
                    )}>
                      <Button
                        size="icon-xs"
                        variant="ghost"
                        onClick={() => startEdit(note.id, note.content)}
                        className="text-muted-foreground"
                      >
                        <Pencil />
                      </Button>
                      <Button
                        size="icon-xs"
                        variant="ghost"
                        onClick={() => handleDelete(note.id)}
                        className="text-muted-foreground hover:text-destructive"
                      >
                        <Trash2 />
                      </Button>
                    </div>
                  </div>
                  <p className="mt-2 text-[10px] text-muted-foreground/60">
                    {formatDateTime(note.created_at)}
                  </p>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
