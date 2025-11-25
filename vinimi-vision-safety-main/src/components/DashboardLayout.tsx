import { ReactNode } from "react";
import Sidebar from "@/components/Sidebar";
import AppBar from "@/components/AppBar";
import { useSidebar } from "@/hooks/useSidebar";

interface DashboardLayoutProps {
  children: ReactNode;
  title?: string;
}

const DashboardLayout = ({ children, title }: DashboardLayoutProps) => {
  const { open, toggle, setOpen } = useSidebar();

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="flex">
        <Sidebar open={open} onToggle={toggle} onClose={() => setOpen(false)} />
        <div className="flex-1 min-h-screen flex flex-col">
          <AppBar open={open} onToggle={toggle} title={title} />
          <main className="flex-1 p-6 bg-slate-100">{children}</main>
        </div>
      </div>
    </div>
  );
};

export default DashboardLayout;
