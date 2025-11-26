import { useEffect } from "react";
import { Link, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import {
  Home,
  LayoutDashboard,
  Users,
  Video,
  AlertTriangle,
  Upload,
  X,
  User,
  CircleHelp,
} from "lucide-react";
import * as Tooltip from "@radix-ui/react-tooltip";
import brandLogo from "@/assets/logo1.png";
import { useToast } from "@/hooks/use-toast";

type NavItem = {
  path?: string;
  label: string;
  icon: React.ComponentType<{ className?: string }>;
  onClick?: () => void;
};

interface SidebarProps {
  open: boolean;
  onToggle: () => void;
  onClose?: () => void;
}

const Sidebar = ({ open, onToggle, onClose }: SidebarProps) => {
  const location = useLocation();
  const isMobile = typeof window !== "undefined" ? window.innerWidth < 1024 : false;
  const { toast } = useToast();

  const navItems: NavItem[] = [
    { path: "/", label: "Home", icon: Home },
    { path: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
    { path: "/workers", label: "Workers", icon: Users },
    { path: "/live", label: "Live Monitoring", icon: Video },
    { path: "/recent-alerts", label: "Recent Alerts", icon: AlertTriangle },
    { path: "/ask-vlm", label: "Ask VINIMI", icon: Upload },
    { path: "/account", label: "Profile", icon: User },
    {
      label: "Help",
      icon: CircleHelp,
      onClick: () =>
        toast({
          title: "Help & Support",
          description: "Email hello@vinimi.ai — help center coming soon.",
        }),
    },
  ];

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open && isMobile) {
        onClose?.();
      }
    };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [open, isMobile, onClose]);

  return (
    <div className={`relative ${isMobile ? "z-50" : ""}`}>
      {isMobile && open && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm"
          onClick={onClose}
          aria-hidden="true"
        />
      )}
      <aside
        className={`${
          isMobile
            ? `fixed top-0 left-0 h-full ${open ? "translate-x-0" : "-translate-x-full"}`
            : ""
        } transition-transform duration-200 ease-in-out`}
      >
        <div
          className={`h-full flex flex-col gap-4 border-r border-slate-200 bg-white/95 backdrop-blur ${
            open ? "w-64" : "w-16"
          } transition-[width] duration-200 ease-in-out shadow-sm`}
        >
          <div className="flex items-center justify-between px-3 pt-4">
            <div className="flex items-center gap-[0.1rem]">
              <img src={brandLogo} alt="VINIMI" className="h-14 w-14 rounded-lg p-0" />
              {open && (
                <div className="leading-tight">
                  <div className="text-lg font-bold tracking-tight text-slate-900">VINIMI</div>
                  <div className="text-[11px] uppercase tracking-[0.25em] text-slate-500">
                    Safety
                  </div>
                </div>
              )}
            </div>
            {isMobile && (
              <Button size="icon" variant="ghost" onClick={onClose}>
                <X className="h-5 w-5" />
              </Button>
            )}
          </div>
          <nav className="flex-1 space-y-1 px-2">
            <Tooltip.Provider delayDuration={200}>
              {navItems.map((item) => {
                const isActive =
                  Boolean(item.path) &&
                  (location.pathname === item.path ||
                    (item.path === "/live" && location.pathname === "/live-monitoring"));
                const glow = isActive
                  ? "border-l-2 border-blue-600 bg-blue-50 text-blue-700"
                  : "border-l-2 border-transparent text-slate-600 hover:bg-slate-50 hover:text-slate-900";
                const content = (
                  <div
                    className={`flex items-center gap-3 px-3 py-2 rounded-xl transition-all ${glow}`}
                  >
                    <item.icon
                      className={`h-5 w-5 shrink-0 ${
                        isActive ? "text-blue-700" : "text-slate-500"
                      }`}
                    />
                    {open && (
                      <span className="text-sm font-medium">
                        {item.label}
                      </span>
                    )}
                  </div>
                );
                const wrapped = item.path ? (
                  <Link to={item.path} className="block" onClick={onClose}>
                    {content}
                  </Link>
                ) : (
                  <button
                    type="button"
                    onClick={item.onClick}
                    className="w-full text-left"
                  >
                    {content}
                  </button>
                );
                return open ? (
                  <div key={item.path || item.label}>{wrapped}</div>
                ) : (
                  <Tooltip.Root key={item.path || item.label}>
                    <Tooltip.Trigger asChild>{wrapped}</Tooltip.Trigger>
                    <Tooltip.Portal>
                      <Tooltip.Content
                        side="right"
                        className="rounded-md bg-slate-800 text-white text-xs px-2 py-1 shadow-lg"
                      >
                        {item.label}
                      </Tooltip.Content>
                    </Tooltip.Portal>
                  </Tooltip.Root>
                );
              })}
            </Tooltip.Provider>
          </nav>
          <div className="px-3 pb-4">
            <Button
              variant="ghost"
              className="w-full justify-center text-slate-700 hover:text-slate-900 border border-slate-200 bg-white hover:bg-slate-50"
              onClick={onToggle}
            >
              {open ? "Collapse" : "Expand"}
            </Button>
          </div>
        </div>
      </aside>
    </div>
  );
};

export default Sidebar;
