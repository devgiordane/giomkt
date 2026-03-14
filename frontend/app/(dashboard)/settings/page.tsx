"use client"

import { useState, useEffect } from "react"
import { Settings, CheckCircle2, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import {
  useWhatsAppSettings,
  useSaveWhatsAppSettings,
  useTestWhatsAppConnection,
} from "@/hooks/use-settings"

export default function SettingsPage() {
  const { data: settings, loading } = useWhatsAppSettings()
  const { mutate: save, loading: saving } = useSaveWhatsAppSettings()
  const { mutate: test, loading: testing } = useTestWhatsAppConnection()

  const [baseUrl, setBaseUrl] = useState("")
  const [instanceName, setInstanceName] = useState("")
  const [apiKey, setApiKey] = useState("")
  const [testResult, setTestResult] = useState<{ ok: boolean; status: number } | null>(null)

  useEffect(() => {
    if (settings) {
      setBaseUrl(settings.base_url)
      setInstanceName(settings.instance_name)
    }
  }, [settings])

  async function handleSave() {
    await save({ base_url: baseUrl, instance_name: instanceName, api_key: apiKey || undefined })
    setApiKey("")
  }

  async function handleTest() {
    const result = await test(undefined)
    if (result) setTestResult(result)
  }

  return (
    <div className="space-y-5 max-w-xl">
      <div>
        <h1 className="text-xl font-semibold">Configurações</h1>
        <p className="text-sm text-muted-foreground">Integração com WhatsApp (EvolutionAPI)</p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-sm">
            <Settings className="size-4" />
            WhatsApp / EvolutionAPI
          </CardTitle>
          <CardDescription>
            Configure a instância do WhatsApp para envio de mensagens automáticas.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {loading ? (
            <div className="space-y-3">
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
              <Skeleton className="h-8 w-full" />
            </div>
          ) : (
            <>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">URL Base</label>
                <Input
                  placeholder="https://api.evolution.example.com"
                  value={baseUrl}
                  onChange={(e) => setBaseUrl(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">Nome da Instância</label>
                <Input
                  placeholder="minha-instancia"
                  value={instanceName}
                  onChange={(e) => setInstanceName(e.target.value)}
                />
              </div>
              <div className="space-y-1.5">
                <label className="text-xs font-medium text-muted-foreground">
                  API Key{" "}
                  <span className="text-muted-foreground/60">(deixe em branco para manter)</span>
                </label>
                <Input
                  type="password"
                  placeholder="••••••••"
                  value={apiKey}
                  onChange={(e) => setApiKey(e.target.value)}
                />
              </div>

              <div className="flex items-center gap-2 pt-2">
                <Button size="sm" onClick={handleSave} disabled={saving}>
                  {saving ? "Salvando..." : "Salvar configurações"}
                </Button>
                <Button size="sm" variant="outline" onClick={handleTest} disabled={testing}>
                  {testing ? "Testando..." : "Testar conexão"}
                </Button>
              </div>

              {testResult && (
                <div className="flex items-center gap-2 rounded-lg border p-3 text-sm">
                  {testResult.ok ? (
                    <>
                      <CheckCircle2 className="size-4 text-emerald-500" />
                      <span>Conexão OK — status {testResult.status}</span>
                      <Badge variant="success" className="ml-auto">Online</Badge>
                    </>
                  ) : (
                    <>
                      <XCircle className="size-4 text-destructive" />
                      <span>Falha na conexão — status {testResult.status}</span>
                      <Badge variant="destructive" className="ml-auto">Offline</Badge>
                    </>
                  )}
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
