// =============================================================================
// GioMkt API — TypeScript types
// Gerado a partir dos blueprints Flask em backend/app/api/
// =============================================================================

// ---------------------------------------------------------------------------
// Shared primitives
// ---------------------------------------------------------------------------

export type ISODate = string        // "YYYY-MM-DD"
export type ISODateTime = string    // "YYYY-MM-DDTHH:MM:SS"
export type HexColor = string       // "#RRGGBB"

// ---------------------------------------------------------------------------
// Health
// ---------------------------------------------------------------------------

export interface HealthResponse {
  status: "ok"
  service: string
}

// ---------------------------------------------------------------------------
// Dashboard
// ---------------------------------------------------------------------------

export interface SpendChartPoint {
  date: ISODate
  label: string   // "DD/MM"
  spend: number
}

export interface DashboardKpis {
  total_clients: number
  spend_today: number
  active_campaigns: number
  pending_tasks: number
  spend_chart_7d: SpendChartPoint[]
}

// ---------------------------------------------------------------------------
// Clients
// ---------------------------------------------------------------------------

export interface Client {
  id: number
  name: string
  email: string | null
  phone: string | null
  status: "active" | "inactive"
  fb_ad_account_id: string | null
  created_at: ISODate | null
}

export interface ClientDetail extends Client {
  budget_config: BudgetConfig | null
  spend_history_30d: { date: ISODate; spend: number }[]
  recent_tasks: { id: number; title: string; status: TaskStatus; created_at: ISODate | null }[]
  recent_notes: { id: number; content: string; created_at: ISODateTime | null }[]
}

export interface BudgetConfig {
  daily_limit: number
  monthly_limit: number
  alert_threshold_pct: number
}

export interface CreateClientBody {
  name: string
  email?: string
  phone?: string
  status?: "active" | "inactive"
  fb_ad_account_id?: string
  fb_token?: string
}

export type UpdateClientBody = Partial<CreateClientBody>

// ---------------------------------------------------------------------------
// Tasks
// ---------------------------------------------------------------------------

export type TaskStatus = "pending" | "done"
export type TaskPriority = 1 | 2 | 3 | 4

export interface TaskLabel {
  id: number
  name: string
  color: HexColor
}

export interface Task {
  id: number
  title: string
  description: string | null
  status: TaskStatus
  source: "manual" | "whatsapp"
  priority: TaskPriority
  section: string
  due_date: ISODate | null
  deadline: ISODate | null
  start_time: string | null   // "HH:MM"
  duration_minutes: number | null
  client_id: number | null
  client: string | null
  recurrence: string
  recurrence_end: ISODate | null
  parent_id: number | null
  subtasks: Task[]
  subtask_count: number
  labels: TaskLabel[]
  created_at: ISODateTime | null
  completed_at: ISODateTime | null
}

export interface TaskDetail extends Task {
  comments: TaskComment[]
}

export interface TaskComment {
  id: number
  content: string
  created_at: ISODateTime | null
}

export interface CreateTaskBody {
  title: string
  description?: string
  section?: string
  priority?: TaskPriority
  due_date?: ISODate
  deadline?: ISODate
  start_time?: string
  duration_minutes?: number
  client_id?: number
  parent_id?: number
  recurrence?: string
  recurrence_end?: ISODate
  label_ids?: number[]
}

export type UpdateTaskBody = Partial<CreateTaskBody>

export interface NlpParseResult {
  title: string
  due_date: ISODate | null
  priority: TaskPriority
  start_time: string | null
  duration_minutes: number | null
}

export interface TaskOptions {
  clients: { id: number; name: string }[]
  parents: { id: number; title: string }[]
  labels: TaskLabel[]
}

// ---------------------------------------------------------------------------
// Campaigns (Ad spend snapshots)
// ---------------------------------------------------------------------------

export interface Snapshot {
  id: number
  client_id: number
  client_name: string
  date: ISODate
  spend: number
  impressions: number
  clicks: number
}

export interface CampaignsResponse {
  snapshots: Snapshot[]
  today_by_client: Omit<Snapshot, "id" | "date">[]
  total_spend_today: number
}

// ---------------------------------------------------------------------------
// Sales
// ---------------------------------------------------------------------------

export interface Sale {
  id: number
  product_id: number
  product: string
  date: ISODate | null
  value: number
  commission_value: number
  quantity: number
  source: "manual" | "eduzz_api"
  external_id: string | null
}

export interface SalesKpis {
  total_qty: number
  total_value: number
  total_commission: number
  avg_ticket: number
}

export interface SalesResponse {
  sales: Sale[]
  kpis: SalesKpis
  month_options: string[]             // ["2025-01", ...]
  product_options: { id: number; name: string }[]
}

export interface CreateSaleBody {
  product_id: number
  date?: ISODate
  value: number
  commission_value?: number
  quantity?: number
}

// ---------------------------------------------------------------------------
// Products
// ---------------------------------------------------------------------------

export interface Product {
  id: number
  name: string
  account_id: number
  account_name: string
  product_id_eduzz: string
  price: number
  commission_percent: number
  active: boolean
}

export interface ProductsResponse {
  products: Product[]
  account_options: { id: number; name: string }[]
}

export interface CreateProductBody {
  name: string
  account_id: number
  product_id_eduzz?: string
  price?: number
  commission_percent?: number
}

export type UpdateProductBody = Partial<CreateProductBody & { active: boolean }>

// ---------------------------------------------------------------------------
// Goals
// ---------------------------------------------------------------------------

export interface Goal {
  id: number
  product_id: number
  product_name: string
  month: number
  year: number
  sales_target: number
  revenue_target: number
  commission_target: number
  actual_sales: number
  actual_revenue: number
  actual_commission: number
  avg_revenue_3m: number
  avg_commission_3m: number
  sales_pct: number
  val_pct: number
  target_val: number
  actual_val: number
  avg_val: number
}

export interface UpsertGoalBody {
  product_id: number
  month?: number
  year?: number
  sales_target?: number
  revenue_target?: number
  commission_target?: number
}

// ---------------------------------------------------------------------------
// Services / Subscriptions
// ---------------------------------------------------------------------------

export type ServiceType = "dominio" | "hospedagem" | "servidor" | "api" | "software"
export type BillingCycle = "monthly" | "annual"

export interface Service {
  id: number
  name: string
  type: ServiceType
  type_label: string
  client_id: number | null
  client_name: string
  value: number
  billing_cycle: BillingCycle
  due_date: ISODate | null
  notes: string | null
}

export interface ServicesKpis {
  expiring_7d: number
  expiring_30d: number
  monthly_total: number
  annual_total: number
}

export interface ServicesResponse {
  services: Service[]
  kpis: ServicesKpis
  costs_by_type: Record<string, number>
  client_options: { id: number; name: string }[]
}

export interface CreateServiceBody {
  name: string
  type: ServiceType
  client_id?: number
  value?: number
  billing_cycle?: BillingCycle
  due_date?: ISODate
  notes?: string
}

export type UpdateServiceBody = Partial<CreateServiceBody>

// ---------------------------------------------------------------------------
// Notes
// ---------------------------------------------------------------------------

export interface Note {
  id: number
  content: string
  client_id: number | null
  client_name: string | null
  created_at: ISODateTime | null
}

export interface NotesResponse {
  notes: Note[]
  client_options: { id: number; name: string }[]
}

export interface CreateNoteBody {
  content: string
  client_id?: number
}

// ---------------------------------------------------------------------------
// Alerts
// ---------------------------------------------------------------------------

export interface Alert {
  id: number
  client_id: number
  client_name: string
  rule_id: number
  message: string
  triggered_at: ISODateTime | null
  resolved: boolean
}

export type AlertRuleType = "daily_budget" | "monthly_budget"

export interface AlertRule {
  id: number
  client_id: number
  client_name: string
  rule_type: AlertRuleType
  threshold: number
  notify_whatsapp: boolean
  active: boolean
}

export interface AlertRulesResponse {
  rules: AlertRule[]
  client_options: { id: number; name: string }[]
}

export interface CreateAlertRuleBody {
  client_id: number
  rule_type?: AlertRuleType
  threshold: number
  notify_whatsapp?: boolean
  active?: boolean
}

export interface CheckAlertsResponse {
  triggered_count: number
  alerts: unknown[]
}

// ---------------------------------------------------------------------------
// Analytics (Umami)
// ---------------------------------------------------------------------------

export interface AnalyticsSite {
  id: number
  name: string
  domain: string
  umami_site_id: string
  client_id: number | null
  client_name: string
}

export interface AnalyticsSitesResponse {
  sites: AnalyticsSite[]
  client_options: { id: number; name: string }[]
}

export interface AnalyticsKpis {
  pageviews: number
  visitors: number
  bounce_rate: number
  avg_time_seconds: number
}

export interface AnalyticsStatsResponse {
  kpis: AnalyticsKpis
  pageviews_by_day: { x: string; y: number }[]
  top_pages: { x: string; y: number }[]
}

export interface CreateSiteBody {
  name: string
  domain: string
  umami_site_id?: string
  client_id?: number
}

// ---------------------------------------------------------------------------
// Labels
// ---------------------------------------------------------------------------

export interface Label {
  id: number
  name: string
  color: HexColor
}

export interface CreateLabelBody {
  name: string
  color?: HexColor
}

export type UpdateLabelBody = Partial<CreateLabelBody>

// ---------------------------------------------------------------------------
// Eduzz Accounts
// ---------------------------------------------------------------------------

export interface EduzzAccount {
  id: number
  name: string
  email: string | null
  active: boolean
  connected: boolean
  auth_url: string
  created_at: ISODate | null
}

export interface CreateEduzzAccountBody {
  name: string
}

export interface SyncSalesBody {
  start_date?: ISODate
  end_date?: ISODate
}

// ---------------------------------------------------------------------------
// Webhooks
// ---------------------------------------------------------------------------

export interface WebhookSubscription {
  id: number
  account_id: number
  account_name: string
  eduzz_subscription_id: string | null
  name: string
  url: string
  status: "active" | "disabled"
  events: string[]
  created_at: ISODate | null
}

export interface WebhookSubscriptionsResponse {
  subscriptions: WebhookSubscription[]
  account_options: { id: number; name: string }[]
}

export interface WebhookEvent {
  id: number
  subscription_id: number | null
  event_type: string
  processed: boolean
  received_at: ISODateTime | null
  payload_preview: string
}

export interface CreateWebhookBody {
  account_id: number
  name: string
  url: string
  events?: string[]
}

// ---------------------------------------------------------------------------
// Settings (WhatsApp)
// ---------------------------------------------------------------------------

export interface WhatsAppSettings {
  base_url: string
  api_key: string   // "***" when reading
  instance_name: string
}

export interface UpdateWhatsAppSettingsBody {
  base_url: string
  instance_name: string
  api_key?: string
}

// ---------------------------------------------------------------------------
// Message Flows
// ---------------------------------------------------------------------------

export type SaleStatus =
  | "waitingPayment"
  | "paid"
  | "canceled"
  | "recovering"
  | "refunded"
  | "expired"

export interface MessageFlow {
  id: number
  product_id: number
  product_name: string
  status: SaleStatus
  template: string
  active: boolean
  delay_minutes: number
}

export interface MessageFlowsResponse {
  flows: MessageFlow[]
  product_options: { id: number; name: string; eduzz_id: string | null }[]
}

export interface CreateMessageFlowBody {
  product_id: number
  status?: SaleStatus
  template: string
  active?: boolean
  delay_minutes?: number
}

// ---------------------------------------------------------------------------
// AI Assistant
// ---------------------------------------------------------------------------

export type AiAction =
  | "create_tasks"
  | "generate_message"
  | "summarize"
  | "extract_data"
  | "analyze_campaign"

export interface AiTaskResult {
  tasks: { title: string; priority: TaskPriority; due_date: ISODate | null }[]
}

export interface AiMessageResult {
  message: string
  subject?: string
}

export interface AiSummaryResult {
  summary: string
  key_points: string[]
}

export interface AiDataResult {
  data: { field: string; value: string }[]
}

export interface AiCampaignResult {
  analysis: string
  recommendations: string[]
  metrics: { cpa?: number; ctr?: number; roas?: number }
}

export type AiProcessResult =
  | AiTaskResult
  | AiMessageResult
  | AiSummaryResult
  | AiDataResult
  | AiCampaignResult

export interface SaveTasksBody {
  tasks: { title: string; priority?: TaskPriority; due_date?: ISODate }[]
}

export interface SaveTasksResponse {
  saved_count: number
  ids: number[]
}
