import { ReactNode } from "react";
import { Button } from "@/components/ui/button";
import { Menu, X, User } from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { clearManager, getManager } from "@/lib/auth";
import { useNavigate } from "react-router-dom";

interface AppBarProps {
  open: boolean;
  onToggle: () => void;
  title?: string;
  actions?: ReactNode;
}

const AppBar = ({ open, onToggle, title, actions }: AppBarProps) => {
  const mgr = getManager();
  const navigate = useNavigate();

  const handleSignOut = () => {
    clearManager();
    navigate("/");
  };

  return (
    <header className="sticky top-0 z-40 backdrop-blur border-b border-slate-200 bg-white/80 text-slate-800">
      <div className="flex items-center justify-between px-4 py-3">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={onToggle}>
            {open ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </Button>
          {title && <h1 className="text-lg font-semibold">{title}</h1>}
        </div>
        <div className="flex items-center gap-3">
          {actions}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="flex items-center gap-2 text-slate-700">
                <User className="h-4 w-4" />
                <span className="hidden sm:inline">{mgr?.email || "Profile"}</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuLabel>Account</DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate("/account")}>Profile</DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate("/account")}>Account Settings</DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={handleSignOut}>Sign Out</DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>
    </header>
  );
};

export default AppBar;
