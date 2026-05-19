"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart2,
  BookOpen,
  ChevronLeft,
  ChevronRight,
  FlaskConical,
  LayoutDashboard,
  LineChart,
  Settings,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/store/ui";
import { Button } from "@/components/ui/button";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const navItems = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/markets", label: "Markets", icon: BarChart2 },
  { href: "/portfolio", label: "Portfolio", icon: LineChart },
  { href: "/backtesting", label: "Backtesting", icon: FlaskConical },
  { href: "/research", label: "Research", icon: BookOpen },
  { href: "/settings", label: "Settings", icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { sidebarCollapsed, toggleSidebar } = useUIStore();

  return (
    <TooltipProvider delay={0}>
      <aside
        className={cn(
          "border-border bg-sidebar relative flex h-full flex-col border-r transition-all duration-200",
          sidebarCollapsed ? "w-16" : "w-60"
        )}
      >
        {/* Logo */}
        <div
          className={cn(
            "border-border flex h-14 items-center border-b px-4",
            sidebarCollapsed && "justify-center px-0"
          )}
        >
          {sidebarCollapsed ? (
            <span className="text-primary text-lg font-bold">Q</span>
          ) : (
            <span className="text-lg font-bold tracking-tight">quant-os</span>
          )}
        </div>

        {/* Nav */}
        <nav className="flex-1 space-y-1 p-2">
          {navItems.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
            const linkClass = cn(
              "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
              "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground",
              active
                ? "bg-sidebar-accent text-sidebar-accent-foreground"
                : "text-sidebar-foreground",
              sidebarCollapsed && "justify-center px-2"
            );
            return (
              <Tooltip key={href}>
                <TooltipTrigger render={<Link href={href} className={linkClass} />}>
                  <Icon className="size-4 shrink-0" />
                  {!sidebarCollapsed && <span>{label}</span>}
                </TooltipTrigger>
                {sidebarCollapsed && <TooltipContent side="right">{label}</TooltipContent>}
              </Tooltip>
            );
          })}
        </nav>

        {/* Collapse toggle */}
        <div className="border-border border-t p-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className={cn(
              "text-sidebar-foreground hover:bg-sidebar-accent w-full",
              sidebarCollapsed ? "justify-center" : "justify-end"
            )}
            aria-label={sidebarCollapsed ? "Expand sidebar" : "Collapse sidebar"}
          >
            {sidebarCollapsed ? (
              <ChevronRight className="size-4" />
            ) : (
              <ChevronLeft className="size-4" />
            )}
          </Button>
        </div>
      </aside>
    </TooltipProvider>
  );
}
