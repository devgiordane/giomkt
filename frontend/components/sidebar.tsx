"use client"

import Link from "next/link"
import { usePathname } from "next/navigation"
import {
  LayoutDashboard,
  CheckSquare,
  Users,
  Megaphone,
  ShoppingCart,
  Target,
  Server,
  FileText,
  BookOpen,
  BarChart2,
  Bell,
  Zap,
  Webhook,
  MessageSquare,
  Settings,
  Bot,
  Package,
  Tag,
  CalendarClock,
  CalendarDays,
} from "lucide-react"
import { cn } from "@/lib/utils"

const navGroups = [
  {
    label: "Principal",
    items: [
      { href: "/", icon: LayoutDashboard, label: "Dashboard" },
      { href: "/tasks", icon: CheckSquare, label: "Tarefas" },
      { href: "/tasks/today", icon: CalendarClock, label: "Hoje" },
      { href: "/tasks/upcoming", icon: CalendarDays, label: "Próximas" },
    ],
  },
  {
    label: "Clientes",
    items: [
      { href: "/clients", icon: Users, label: "Clientes" },
      { href: "/campaigns", icon: Megaphone, label: "Campanhas" },
      { href: "/notes", icon: FileText, label: "Notas" },
    ],
  },
  {
    label: "Vendas",
    items: [
      { href: "/sales", icon: ShoppingCart, label: "Vendas" },
      { href: "/goals", icon: Target, label: "Metas" },
      { href: "/products", icon: Package, label: "Produtos" },
      { href: "/eduzz", icon: Zap, label: "Eduzz" },
    ],
  },
  {
    label: "Operações",
    items: [
      { href: "/services", icon: Server, label: "Serviços" },
      { href: "/analytics", icon: BarChart2, label: "Analytics" },
      { href: "/alerts", icon: Bell, label: "Alertas" },
      { href: "/reports", icon: BarChart2, label: "Relatórios" },
    ],
  },
  {
    label: "Automação",
    items: [
      { href: "/message-flows", icon: MessageSquare, label: "Fluxos" },
      { href: "/webhooks", icon: Webhook, label: "Webhooks" },
      { href: "/ai", icon: Bot, label: "Assistente IA" },
    ],
  },
  {
    label: "Config.",
    items: [
      { href: "/wiki", icon: BookOpen, label: "Wiki" },
      { href: "/labels", icon: Tag, label: "Labels" },
      { href: "/settings", icon: Settings, label: "Configurações" },
    ],
  },
]

export function Sidebar() {
  const pathname = usePathname()

  function isActive(href: string) {
    if (href === "/") return pathname === "/"
    return pathname === href || pathname.startsWith(href + "/")
  }

  return (
    <aside className="flex h-full w-56 flex-col border-r bg-sidebar">
      {/* Logo */}
      <div className="flex h-14 shrink-0 items-center border-b px-4">
        <span className="text-base font-bold tracking-tight text-sidebar-foreground">
          Gio<span className="text-sidebar-primary">Mkt</span>
        </span>
      </div>

      {/* Nav */}
      <nav className="flex-1 overflow-y-auto py-3">
        {navGroups.map((group) => (
          <div key={group.label} className="mb-3">
            <p className="mb-1 px-4 text-[10px] font-semibold uppercase tracking-widest text-muted-foreground">
              {group.label}
            </p>
            <ul className="space-y-0.5 px-2">
              {group.items.map((item) => (
                <li key={item.href}>
                  <Link
                    href={item.href}
                    className={cn(
                      "flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-sm transition-colors",
                      isActive(item.href)
                        ? "bg-sidebar-accent text-sidebar-accent-foreground font-medium"
                        : "text-sidebar-foreground hover:bg-sidebar-accent/50 hover:text-sidebar-accent-foreground",
                    )}
                  >
                    <item.icon className="size-4 shrink-0" />
                    {item.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </nav>
    </aside>
  )
}
