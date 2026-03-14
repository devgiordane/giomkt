"use client"

import { useState } from "react"
import { Bot, Send, Save, CheckCircle2 } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Select } from "@/components/ui/select"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { EmptyState } from "@/components/ui/empty-state"
import { Spinner } from "@/components/ui/spinner"
import { useAiProcess, useSaveAiTasks } from "@/hooks/use-ai-assistant"
import type { AiAction, AiTaskResult } from "@/types/api"

const ACTIONS: { value: AiAction; label: string; description: string }[] = [
  { value: "create_tasks", label: "Criar tarefas", description: "Extrair tarefas do texto" },
  { value: "generate_message", label: "Gerar mensagem", description: "Criar mensagem de marketing" },
  { value: "summarize", label: "Resumir", description: "Resumir conteúdo longo" },
  { value: "extract_data", label: "Extrair dados", description: "Identificar dados estruturados" },
  { value: "analyze_campaign", label: "Analisar campanha", description: "Insights de campanha" },
]

export default function AiPage() {
  const [action, setAction] = useState<AiAction>("create_tasks")
  const [content, setContent] = useState("")
  const [result, setResult] = useState<Record<string, unknown> | null>(null)
  const [saved, setSaved] = useState(false)

  const { mutate: process, loading } = useAiProcess()
  const { mutate: saveTasks, loading: saving } = useSaveAiTasks()

  async function handleProcess() {
    if (!content.trim()) return
    setSaved(false)
    const res = await process({ action, content })
    if (res) setResult(res as Record<string, unknown>)
  }

  async function handleSaveTasks() {
    if (!result || !("tasks" in result)) return
    const tasks = (result as AiTaskResult).tasks
    await saveTasks({ tasks })
    setSaved(true)
  }

  const hasTasks = result && "tasks" in result

  return (
    <div className="space-y-5 max-w-2xl">
      <div>
        <h1 className="text-xl font-semibold">Assistente IA</h1>
        <p className="text-sm text-muted-foreground">
          Processe texto com inteligência artificial
        </p>
      </div>

      <Card>
        <CardContent className="p-5 space-y-4">
          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Ação</label>
            <Select
              value={action}
              onChange={(e) => { setAction(e.target.value as AiAction); setResult(null) }}
              className="h-8 w-56"
            >
              {ACTIONS.map((a) => (
                <option key={a.value} value={a.value}>{a.label} — {a.description}</option>
              ))}
            </Select>
          </div>

          <div className="space-y-1.5">
            <label className="text-xs font-medium text-muted-foreground">Conteúdo</label>
            <Textarea
              placeholder="Cole aqui o texto para processar..."
              value={content}
              onChange={(e) => setContent(e.target.value)}
              className="min-h-[140px]"
            />
          </div>

          <Button
            size="sm"
            onClick={handleProcess}
            disabled={loading || !content.trim()}
          >
            {loading ? <Spinner className="size-4" /> : <Send className="size-4" />}
            {loading ? "Processando..." : "Processar"}
          </Button>
        </CardContent>
      </Card>

      {/* Result */}
      {result && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="flex items-center gap-2 text-sm">
              <Bot className="size-4" />
              Resultado
            </CardTitle>
            {hasTasks && (
              saved ? (
                <Badge variant="success" className="gap-1">
                  <CheckCircle2 className="size-3" />
                  Tarefas salvas
                </Badge>
              ) : (
                <Button size="sm" variant="outline" onClick={handleSaveTasks} disabled={saving}>
                  <Save className="size-4" />
                  {saving ? "Salvando..." : "Salvar tarefas"}
                </Button>
              )
            )}
          </CardHeader>
          <CardContent>
            <AiResult action={action} result={result} />
          </CardContent>
        </Card>
      )}

      {!result && !loading && (
        <EmptyState
          icon={<Bot className="size-5" />}
          title="Aguardando processamento"
          description="Digite um texto e selecione uma ação para começar."
          className="min-h-[180px]"
        />
      )}
    </div>
  )
}

function AiResult({ action, result }: { action: AiAction; result: Record<string, unknown> }) {
  if (action === "create_tasks" && "tasks" in result) {
    const tasks = (result as AiTaskResult).tasks
    return (
      <ul className="space-y-2">
        {tasks.map((t, i) => (
          <li key={i} className="flex items-center gap-3 rounded-lg border px-3 py-2 text-sm">
            <Badge variant={
              t.priority === 1 ? "destructive" : t.priority === 2 ? "warning" : "info"
            } className="text-[10px] shrink-0">
              P{t.priority}
            </Badge>
            <span className="flex-1">{t.title}</span>
            {t.due_date && (
              <span className="text-xs text-muted-foreground shrink-0">{t.due_date}</span>
            )}
          </li>
        ))}
      </ul>
    )
  }

  if ("message" in result) {
    return (
      <div className="space-y-2">
        {"subject" in result && (
          <p className="text-sm font-medium">Assunto: {String(result.subject)}</p>
        )}
        <p className="whitespace-pre-wrap text-sm text-muted-foreground">{String(result.message)}</p>
      </div>
    )
  }

  if ("summary" in result) {
    return (
      <div className="space-y-3">
        <p className="text-sm">{String(result.summary)}</p>
        {Array.isArray(result.key_points) && result.key_points.length > 0 && (
          <ul className="space-y-1">
            {(result.key_points as string[]).map((p, i) => (
              <li key={i} className="flex items-start gap-2 text-sm text-muted-foreground">
                <span className="mt-1.5 size-1.5 shrink-0 rounded-full bg-primary" />
                {p}
              </li>
            ))}
          </ul>
        )}
      </div>
    )
  }

  // Fallback: raw JSON
  return (
    <pre className="overflow-auto rounded-lg bg-muted p-3 text-xs">
      {JSON.stringify(result, null, 2)}
    </pre>
  )
}
