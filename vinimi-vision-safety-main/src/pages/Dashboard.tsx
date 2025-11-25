import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  Users,
  AlertTriangle,
  Video,
  Upload,
  Search,
  Shield,
} from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";

const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

type RecentAlert = {
  id: string;
  worker_name: string;
  worker_id: number | null;
  location_name: string;
  timestamp: string | null;
};

const formatTimeAgo = (iso: string) => {
  const d = new Date(iso);
  const now = new Date();
  const diffMs = now.getTime() - d.getTime();

  if (Number.isNaN(diffMs)) return "";

  const mins = Math.round(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins} min${mins !== 1 ? "s" : ""} ago`;

  const hours = Math.round(mins / 60);
  if (hours < 24) return `${hours} hour${hours !== 1 ? "s" : ""} ago`;

  const days = Math.round(hours / 24);
  return `${days} day${days !== 1 ? "s" : ""} ago`;
};

const Dashboard = () => {
  const navigate = useNavigate();
  const [searchQuery, setSearchQuery] = useState("");

  // stats still mocked – you can wire these to APIs later
  const stats = {
    totalWorkers: 47,
    totalViolations: 23,
    activeAlerts: 3,
  };

  const [recentAlerts, setRecentAlerts] = useState<RecentAlert[]>([]);
  const [loadingAlerts, setLoadingAlerts] = useState(false);

  useEffect(() => {
    const fetchRecentAlerts = async () => {
      try {
        setLoadingAlerts(true);
        const res = await fetch(`${API_BASE}/api/live/recent-alerts`);
        if (!res.ok) {
          throw new Error(`HTTP ${res.status}`);
        }
        const data: RecentAlert[] = await res.json();
        setRecentAlerts(data);
      } catch (err) {
        console.error("Failed to fetch recent alerts:", err);
        setRecentAlerts([]);
      } finally {
        setLoadingAlerts(false);
      }
    };

    fetchRecentAlerts();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // later: navigate to workers page with query or call backend search
    // navigate(`/workers?search=${encodeURIComponent(searchQuery)}`);
  };

  const heroHighlights = [
    {
      label: "Helmet compliance",
      value: "94%",
      delta: "+3.2% vs last week",
    },
    {
      label: "Unknown detections",
      value: "6",
      delta: "2 resolved in the last hour",
    },
    {
      label: "Average response time",
      value: "2m 14s",
      delta: "Acknowledged alerts",
    },
    {
      label: "Critical locations",
      value: "3",
      delta: "Need supervisor follow-up",
    },
  ];

  const healthMetrics = [
    {
      title: "Live cameras",
      value: "08 / 10 online",
      detail: "All helmet zones covered",
    },
    {
      title: "Worker gallery",
      value: "312 embeddings",
      detail: "Last sync 4 minutes ago",
    },
    {
      title: "Edge services",
      value: "5 nodes healthy",
      detail: "Rajahmundry, Guntur, Navi Mumbai, Pune, Chennai",
    },
  ];

  const complianceBreakdown = [
    { label: "Helmet ON", value: 78, color: "bg-emerald-500" },
    { label: "No helmet", value: 16, color: "bg-rose-500" },
    { label: "Unknown", value: 6, color: "bg-amber-400" },
  ];

  const statCards = [
    {
      title: "Total Workers",
      value: stats.totalWorkers,
      icon: Users,
      textClass: "text-sky-400",
      iconClass: "text-sky-400",
      onClick: () => navigate("/workers"),
      delay: 0.2,
      subtitle: "Active on site",
    },
    {
      title: "Total Violations",
      value: stats.totalViolations,
      icon: AlertTriangle,
      textClass: "text-amber-400",
      iconClass: "text-amber-400",
      onClick: () => navigate("/violations"),
      delay: 0.3,
      subtitle: "Last 24 hours",
    },
    {
      title: "Active Alerts",
      value: stats.activeAlerts,
      icon: Shield,
      textClass: "text-red-400",
      iconClass: "text-red-400",
      onClick: () => navigate("/workers"), // or /alerts later
      delay: 0.4,
      subtitle: "Requires attention",
    },
  ];

  const quickActions = [
    {
      path: "/live-monitoring",
      icon: Video,
      title: "Live Monitoring",
      description: "Real-time video monitoring with AI detection",
      gradient: "from-sky-400 to-cyan-400",
      delay: 0.5,
    },
    {
      path: "/ask-vlm",
      icon: Upload,
      title: "Upload & Ask VINIMI",
      description: "Upload images/videos for AI analysis",
      gradient: "from-purple-400 to-blue-400",
      delay: 0.6,
    },
  ];

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-8"
      >
        {/* Hero */}
        <motion.section
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="grid gap-6 xl:grid-cols-[2.1fr,1fr]"
        >
          <div className="relative overflow-hidden rounded-3xl border border-slate-200 bg-gradient-to-br from-white via-[#eef2f7] to-[#f8fafc] shadow-lg">
            <div className="relative flex flex-col gap-8 p-8">
              <div className="flex flex-col gap-4 lg:flex-row lg:items-end lg:justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.4em] text-slate-500">
                    VINIMI CONTROL ROOM
                  </p>
                  <h1 className="text-4xl font-semibold text-slate-900 mt-1">
                    Live visibility across every site
                  </h1>
                  <p className="text-sm text-slate-700 max-w-xl mt-2">
                    All events, cameras, and worker telemetry flow into a single
                    command center so you can respond before incidents escalate.
                  </p>
                </div>
                <form
                  onSubmit={handleSearchSubmit}
                  className="flex w-full gap-2 rounded-2xl border border-slate-200 bg-white p-2 shadow-sm lg:w-[360px]"
                >
                  <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 h-4 w-4 text-slate-400" />
                    <Input
                      placeholder="Search worker or location…"
                      value={searchQuery}
                      onChange={(e) => setSearchQuery(e.target.value)}
                      className="border-none bg-transparent pl-9 text-sm text-slate-900 placeholder:text-slate-400 focus-visible:ring-0"
                    />
                  </div>
                  <Button type="submit" className="bg-blue-600 hover:bg-blue-700 text-white">
                    Search
                  </Button>
                </form>
              </div>

              <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
                {heroHighlights.map((item) => (
                  <div
                    key={item.label}
                    className="rounded-2xl border border-slate-200 bg-white p-4 shadow-sm hover:shadow-md transition"
                  >
                    <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
                      {item.label}
                    </p>
                    <div className="flex items-baseline gap-2">
                      <span className="text-3xl font-semibold text-slate-900">
                        {item.value}
                      </span>
                      <span className="text-xs text-emerald-600">{item.delta}</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <Card className="bg-white border border-slate-200 shadow-sm">
            <CardHeader className="pb-3">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-xs uppercase tracking-[0.4em] text-slate-500">
                    System health
                  </p>
                  <CardTitle className="text-xl text-slate-900">Edge & camera status</CardTitle>
                </div>
                <Badge variant="outline" className="text-emerald-700 border-emerald-200 bg-emerald-50">
                  Operational
                </Badge>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {healthMetrics.map((metric) => (
                <div
                  key={metric.title}
                  className="rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3 shadow-[0_1px_2px_rgba(2,6,23,0.06)]"
                >
                  <p className="text-xs uppercase tracking-[0.3em] text-slate-500">
                    {metric.title}
                  </p>
                  <p className="text-lg font-semibold text-slate-900">{metric.value}</p>
                  <p className="text-xs text-slate-600">{metric.detail}</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </motion.section>

        {/* Stats cards */}
        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-4">
          {statCards.map((stat) => (
            <motion.div
              key={stat.title}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: stat.delay }}
            >
              <Card
                className="group cursor-pointer overflow-hidden border border-slate-200 bg-white shadow-sm hover:shadow-md transition"
                onClick={stat.onClick}
              >
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-sm font-medium text-slate-800">
                    {stat.title}
                  </CardTitle>
                  <div className="rounded-full bg-blue-50 p-2 text-blue-700 shadow-inner group-hover:scale-110 transition">
                    <stat.icon className={`h-4 w-4 ${stat.iconClass.replace("text-", "text-")}`} />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-semibold text-slate-900">
                    {stat.value}
                  </div>
                  <p className="text-xs text-slate-600">
                    {stat.subtitle}
                  </p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
          <motion.div
            initial={{ y: 20, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.45 }}
          >
            <Card className="border border-slate-200 bg-white shadow-sm">
              <CardHeader className="pb-2">
                <CardTitle className="text-sm text-slate-800">
                  Compliance mix
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="flex h-3 overflow-hidden rounded-full bg-slate-100">
                  {complianceBreakdown.map((segment) => (
                    <div
                      key={segment.label}
                      style={{ width: `${segment.value}%` }}
                      className={`${segment.color}`}
                    />
                  ))}
                </div>
                <div className="grid grid-cols-3 gap-3 text-xs">
                  {complianceBreakdown.map((segment) => (
                    <div key={segment.label}>
                      <p className="text-slate-600">{segment.label}</p>
                      <p className="text-sm font-semibold text-slate-900">
                        {segment.value}%
                      </p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>


        {/* Quick actions */}
        <div className="grid gap-4 md:grid-cols-2">
          {quickActions.map((action) => (
            <motion.div
              key={action.path}
              initial={{ y: 20, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              transition={{ delay: action.delay }}
            >
              <Card className="overflow-hidden border border-slate-200 bg-white shadow-sm hover:shadow-md transition">
                <Link to={action.path} className="block h-full">
                  <div className="flex h-full flex-col gap-4 p-6">
                    <div
                      className={`inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700`}
                    >
                      <action.icon className="h-4 w-4" />
                      {action.title}
                    </div>
                    <p className="text-sm text-slate-700">{action.description}</p>
                    <div
                      className={`mt-auto h-1 w-24 rounded-full bg-gradient-to-r ${action.gradient}`}
                    />
                  </div>
                </Link>
              </Card>
            </motion.div>
          ))}
        </div>

        {/* Recent Alerts fetched from API */}
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          transition={{ delay: 0.7 }}
        >
          <Card className="border border-slate-200 bg-white shadow-sm">
            <CardHeader className="flex flex-row items-center justify-between">
              <div>
                <CardTitle className="flex items-center gap-2 text-slate-900">
                  <AlertTriangle className="h-5 w-5 text-amber-400 animate-pulse" />
                  Recent alerts
                </CardTitle>
                <p className="text-xs text-slate-600">
                  Live stream of helmet-off violations and unknown entrants
                </p>
              </div>
              <Button
                variant="outline"
                size="sm"
                className="border-slate-300 text-slate-700 hover:bg-slate-50"
                onClick={() => navigate("/live-monitoring")}
              >
                Open monitor
              </Button>
            </CardHeader>
            <CardContent>
              <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-600 bg-slate-50">
                No alerts to display yet.
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </DashboardLayout>
  );
};

export default Dashboard;
