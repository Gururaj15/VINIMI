import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { AlertTriangle, MapPin, Clock } from "lucide-react";

import DashboardLayout from "@/components/DashboardLayout";
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { fetchViolations, RecentAlert } from "@/lib/api";

const formatDate = (iso?: string | null) => {
  if (!iso) return "—";
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  return dt.toLocaleString();
};

const ViolationsPage = () => {
  const [violations, setViolations] = useState<RecentAlert[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadViolations = async () => {
      try {
        setLoading(true);
        const data = await fetchViolations();
        setViolations(data);
      } catch (err) {
        console.error("Failed to load violations:", err);
        setViolations([]);
      } finally {
        setLoading(false);
      }
    };

    loadViolations();
  }, []);

  return (
    <DashboardLayout>
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className="space-y-6"
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-white flex items-center gap-3">
              <AlertTriangle className="h-7 w-7 text-amber-400" />
              Helmet Violations
            </h1>
            <p className="text-sm text-muted-foreground mt-1">
              Stream of helmet-off detections captured by live monitoring.
            </p>
          </div>
          <Button
            variant="outline"
            className="border-white/20 text-white hover:bg-white/10"
            onClick={() => window.location.reload()}
          >
            Refresh
          </Button>
        </div>

        <Card className="border-white/10 bg-slate-950/70">
          <CardHeader>
            <CardTitle className="text-white">Recent events</CardTitle>
          </CardHeader>
          <CardContent>
            {loading ? (
              <p className="text-sm text-muted-foreground">Loading…</p>
            ) : violations.length === 0 ? (
              <div className="rounded-2xl border border-dashed border-white/15 p-8 text-center text-sm text-muted-foreground">
                No helmet-off events recorded yet.
              </div>
            ) : (
              <div className="space-y-4">
                {violations.map((violation, index) => (
                  <motion.div
                    key={violation.id}
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ delay: index * 0.02 }}
                    className="rounded-2xl border border-white/10 bg-white/5 p-4 backdrop-blur flex flex-col gap-2"
                  >
                    <div className="flex items-center justify-between">
                      <div className="text-white font-semibold text-lg">
                        {violation.worker_name || "Unknown worker"}
                      </div>
                      <div className="flex gap-2 items-center">
                        <Badge variant="destructive">Helmet Off</Badge>
                        <Badge variant="outline">
                          {(violation.sms_status || "pending").replace(/_/g, " ")}
                        </Badge>
                      </div>
                    </div>
                    <div className="flex flex-wrap items-center gap-4 text-xs text-slate-300">
                      <span className="inline-flex items-center gap-1">
                        <MapPin className="h-3 w-3" />
                        {violation.location_name || "Unknown location"}
                      </span>
                      <span className="inline-flex items-center gap-1">
                        <Clock className="h-3 w-3" />
                        {formatDate(violation.timestamp)}
                      </span>
                    </div>
                    {violation.phone && (
                      <div className="text-[11px] text-slate-400">
                        Phone: {violation.phone}
                      </div>
                    )}
                  </motion.div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </DashboardLayout>
  );
};

export default ViolationsPage;
