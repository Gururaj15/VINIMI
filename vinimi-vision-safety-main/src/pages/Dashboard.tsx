import { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { motion } from "framer-motion";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Users, AlertTriangle, Video, Upload, Search, Shield } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";
import { fetchRecentAlerts, RecentAlert } from "@/lib/api";

const formatTimeAgo = (iso?: string | null) => {
  if (!iso) return "";
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

  const stats = {
    totalWorkers: 47,
    totalViolations: 23,
    activeAlerts: 3,
  };

  const [recentAlerts, setRecentAlerts] = useState<RecentAlert[]>([]);
  const [loadingAlerts, setLoadingAlerts] = useState(false);

  useEffect(() => {
    const loadRecentAlerts = async () => {
      try {
        setLoadingAlerts(true);
        const data = await fetchRecentAlerts(5);
        setRecentAlerts(data);
      } catch (err) {
        console.error("Failed to fetch recent alerts:", err);
        setRecentAlerts([]);
      } finally {
        setLoadingAlerts(false);
      }
    };

    loadRecentAlerts();
  }, []);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
  };

  const statCards = [
    {
      title: "Total Workers",
      value: stats.totalWorkers,
      icon: Users,
      onClick: () => navigate("/workers"),
      delay: 0.2,
      subtitle: "Currently present in monitored EHS zones",
    },
    {
      title: "Total Violations",
      value: stats.totalViolations,
      icon: AlertTriangle,
      onClick: () => navigate("/violations"),
      delay: 0.3,
      subtitle: "Last 24 hours (PPE & safety rules)",
    },
    {
      title: "Active Safety Alerts",
      value: stats.activeAlerts,
      icon: Shield,
      onClick: () => navigate("/workers"),
      delay: 0.4,
      subtitle: "Requires attention",
    },
    {
      title: "EHS Security Breach – Unknown Individual",
      value: 2,
      icon: Shield,
      onClick: () => navigate("/violations"),
      delay: 0.5,
      subtitle: "Unknown individuals detected today",
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
        {/* Hero (text + search) */}
        <motion.section
          initial={{ y: 30, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="grid gap-6"
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
            </div>
          </div>
        </motion.section>

        {/* Stats cards */}
        <div className="grid gap-4 md:grid-cols-3">
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
                    <stat.icon className="h-4 w-4" />
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="text-4xl font-semibold text-slate-900">
                    {stat.value}
                  </div>
                  <p className="text-xs text-slate-600">{stat.subtitle}</p>
                </CardContent>
              </Card>
            </motion.div>
          ))}
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
                    <div className="inline-flex items-center gap-2 rounded-full border border-blue-100 bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-700">
                      <action.icon className="h-4 w-4" />
                      {action.title}
                    </div>
                    <p className="text-sm text-slate-700">
                      {action.description}
                    </p>
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
              {loadingAlerts ? (
                <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-600 bg-slate-50">
                  Loading recent alerts…
                </div>
              ) : recentAlerts.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-200 p-6 text-center text-sm text-slate-600 bg-slate-50">
                  No alerts to display yet.
                </div>
              ) : (
                <div className="space-y-3">
                  {recentAlerts.map((alert) => (
                    <div
                      key={alert.id}
                      className="flex items-start justify-between gap-4 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3"
                    >
                      <div className="flex items-center gap-3">
                        <div className="h-9 w-9 rounded-full bg-amber-100 text-amber-700 flex items-center justify-center">
                          <AlertTriangle className="h-4 w-4" />
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900">
                            {alert.worker_name || "Unknown worker"}
                          </div>
                          <div className="text-xs text-slate-600">
                            {alert.location_name || "Unknown location"}
                          </div>
                        </div>
                      </div>
                      <div className="text-right space-y-1">
                        <div className="text-xs text-slate-500">
                          {formatTimeAgo(alert.timestamp)}
                        </div>
                        <div className="flex justify-end gap-2">
                          <Badge variant="destructive">Helmet Off</Badge>
                          <Badge variant="outline">
                            {alert.sms_status || "pending"}
                          </Badge>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>
      </motion.div>
    </DashboardLayout>
  );
};

export default Dashboard;
