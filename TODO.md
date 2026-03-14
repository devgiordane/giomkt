# TODO — Migração Dash → Next.js

> Legenda: `[ ]` pendente · `[x]` concluído · `[-]` em progresso

---

## ✅ Backend Flask (concluído)

- [x] Criar `create_app()` factory em `backend/app/__init__.py`
- [x] Blueprint `dashboard.py` — `GET /api/dashboard/kpis`
- [x] Blueprint `clients.py` — CRUD completo + detalhes
- [x] Blueprint `tasks.py` — CRUD + toggle + comentários + NLP parse
- [x] Blueprint `campaigns.py` — snapshots de gasto
- [x] Blueprint `sales.py` — CRUD + sync Eduzz
- [x] Blueprint `products.py` — CRUD com filtro por conta
- [x] Blueprint `goals.py` — GET com progresso calculado + upsert
- [x] Blueprint `services.py` — CRUD + KPIs de vencimento
- [x] Blueprint `notes.py` — CRUD + filtro wiki
- [x] Blueprint `alerts.py` — alertas + regras + check
- [x] Blueprint `analytics.py` — sites CRUD + proxy Umami
- [x] Blueprint `labels.py` — CRUD de labels
- [x] Blueprint `eduzz.py` — contas + sync + OAuth2 callback
- [x] Blueprint `webhooks.py` — receivers + assinaturas + eventos
- [x] Blueprint `settings.py` — WhatsApp GET/PUT/test
- [x] Blueprint `message_flows.py` — CRUD + toggle
- [x] Blueprint `ai_assistant.py` — process + save-tasks
- [x] Refatorar `backend/app/main.py` para Flask puro
- [x] Remover `dash`, `plotly`, `dash-bootstrap-components` do `pyproject.toml`

---

## ✅ Frontend — Infraestrutura Base (concluído)

- [x] `frontend/next.config.mjs` — proxy `/api/*` → `http://localhost:8050`
- [x] `frontend/lib/api.ts` — cliente HTTP base com `ApiError`
- [x] `frontend/types/api.ts` — tipos TypeScript completos (todos os 17 domínios)
- [x] `frontend/hooks/use-fetch.ts` — hooks `useFetch` e `useMutation`
- [x] `frontend/hooks/use-dashboard.ts`
- [x] `frontend/hooks/use-clients.ts`
- [x] `frontend/hooks/use-tasks.ts`
- [x] `frontend/hooks/use-campaigns.ts`
- [x] `frontend/hooks/use-sales.ts`
- [x] `frontend/hooks/use-products.ts`
- [x] `frontend/hooks/use-goals.ts`
- [x] `frontend/hooks/use-services.ts`
- [x] `frontend/hooks/use-notes.ts`
- [x] `frontend/hooks/use-alerts.ts`
- [x] `frontend/hooks/use-analytics.ts`
- [x] `frontend/hooks/use-labels.ts`
- [x] `frontend/hooks/use-eduzz.ts`
- [x] `frontend/hooks/use-webhooks.ts`
- [x] `frontend/hooks/use-settings.ts`
- [x] `frontend/hooks/use-message-flows.ts`
- [x] `frontend/hooks/use-ai-assistant.ts`

---

## ✅ Documentação (concluído)

- [x] `openapi.yaml` — documentação OpenAPI 3.1 com todos os 47 endpoints

---

## ✅ Frontend — Layout e Componentes Compartilhados (concluído)

- [x] `frontend/app/(dashboard)/layout.tsx` — layout com sidebar + grupo de rotas
- [x] `frontend/components/sidebar.tsx` — menu lateral com todos os links e active state
- [x] `frontend/components/ui/card.tsx` — Card, CardHeader, CardTitle, CardContent, CardFooter
- [x] `frontend/components/ui/badge.tsx` — variantes: default, success, warning, info, destructive, outline
- [x] `frontend/components/ui/input.tsx` — Input estilizado
- [x] `frontend/components/ui/select.tsx` — Select nativo com chevron
- [x] `frontend/components/ui/textarea.tsx` — Textarea
- [x] `frontend/components/ui/skeleton.tsx` — Skeleton, SkeletonCard, SkeletonTable
- [x] `frontend/components/ui/spinner.tsx` — Spinner SVG animado
- [x] `frontend/components/ui/empty-state.tsx` — EmptyState com ícone, título, descrição e ação
- [x] `frontend/components/ui/separator.tsx` — Separator horizontal/vertical
- [x] `frontend/lib/utils.ts` — `cn`, `formatBRL`, `formatDate`, `formatDateTime`, `formatPercent`, `formatNumber`

---

## ✅ Frontend — Páginas (concluído)

### Alta prioridade

- [x] `frontend/app/(dashboard)/page.tsx` — **Dashboard** (KPIs + gráfico de barras 7 dias)
- [x] `frontend/app/(dashboard)/tasks/page.tsx` — **Tarefas** (lista agrupada, filtros, toggle, quick-create)
- [x] `frontend/app/(dashboard)/tasks/today/page.tsx` — **Hoje** (tarefas do dia com horário e duração)
- [x] `frontend/app/(dashboard)/tasks/upcoming/page.tsx` — **Próximas** (agrupadas por data)
- [x] `frontend/app/(dashboard)/clients/page.tsx` — **Clientes** (tabela com busca e filtro de status)
- [x] `frontend/app/(dashboard)/clients/[id]/page.tsx` — **Perfil do Cliente** (gastos 30d, tarefas, notas)
- [ ] `frontend/app/(dashboard)/clients/new/page.tsx` — **Formulário de Cliente** (criar/editar)

### Média prioridade

- [x] `frontend/app/(dashboard)/campaigns/page.tsx` — **Campanhas** (KPIs + gasto hoje + histórico)
- [x] `frontend/app/(dashboard)/sales/page.tsx` — **Vendas** (tabela + 4 KPIs + filtros)
- [x] `frontend/app/(dashboard)/goals/page.tsx` — **Metas** (cards com barras de progresso)
- [x] `frontend/app/(dashboard)/services/page.tsx` — **Serviços** (alertas de vencimento 7/30d)
- [x] `frontend/app/(dashboard)/notes/page.tsx` — **Notas** (lista por cliente + inline create)
- [x] `frontend/app/(dashboard)/wiki/page.tsx` — **Wiki** (edição inline, empty state ilustrado)

### Integrações e configuração

- [x] `frontend/app/(dashboard)/analytics/page.tsx` — **Analytics** (KPIs Umami + top pages)
- [x] `frontend/app/(dashboard)/alerts/page.tsx` — **Alertas** (ativos/resolvidos + regras)
- [x] `frontend/app/(dashboard)/eduzz/page.tsx` — **Contas Eduzz** (CRUD + sync + OAuth link)
- [x] `frontend/app/(dashboard)/webhooks/page.tsx` — **Webhooks** (assinaturas + eventos por sub)
- [x] `frontend/app/(dashboard)/message-flows/page.tsx` — **Fluxos de Mensagem** (toggle inline)
- [x] `frontend/app/(dashboard)/settings/page.tsx` — **Configurações WhatsApp** (form + test badge)

### Ferramentas internas

- [x] `frontend/app/(dashboard)/ai/page.tsx` — **Assistente IA** (5 ações + salvar tarefas)
- [x] `frontend/app/(dashboard)/products/page.tsx` — **Produtos** (tabela com comissão e status)
- [x] `frontend/app/(dashboard)/labels/page.tsx` — **Labels** (color picker + lista inline)
- [x] `frontend/app/(dashboard)/reports/page.tsx` — **Relatórios** (consolidado mês atual)

---

## 🔲 Frontend — Qualidade e Deploy

- [x] Criar `frontend/.env.local` com `BACKEND_URL=http://localhost:8050`
- [ ] Testar proxy Next.js → Flask em desenvolvimento
- [ ] Remover pasta `backend/app/pages/` (páginas Dash legadas)
- [ ] Remover `backend/app/layout.py` (layout Dash legado)
- [ ] Remover `backend/app/assets/` se existir
- [ ] Configurar `frontend/Dockerfile` para build de produção
- [ ] Configurar `backend/Dockerfile` para Flask em produção
- [ ] Criar `docker-compose.yml` (Flask + Next.js)
- [ ] Testar build completo (`pnpm build` no frontend)
- [ ] Verificar serialização de datas no backend (todos os endpoints)

---

## Progresso Geral

| Área | Tarefas | Concluídas | % |
|------|---------|------------|---|
| Backend Flask | 20 | 20 | 100% |
| Frontend Infra | 22 | 22 | 100% |
| Documentação | 1 | 1 | 100% |
| Layout/Componentes | 12 | 12 | 100% |
| Páginas Next.js | 23 | 22 | 96% |
| Deploy/Limpeza | 10 | 0 | 0% |
| **Total** | **88** | **77** | **~88%** |
