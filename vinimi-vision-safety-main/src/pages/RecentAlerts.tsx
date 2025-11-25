import { useEffect, useMemo, useState } from "react";
import DashboardLayout from "@/components/DashboardLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { AlertTriangle, Loader2, RefreshCw } from "lucide-react";
import { fetchRecentAlerts, RecentAlert } from "@/lib/api";

const formatTimestamp = (timestamp?: string | null) => {
  if (!timestamp) return "Unknown time";
  const dt = new Date(timestamp);
  if (Number.isNaN(dt.getTime())) {
    return timestamp;
  }
  const absolute = dt.toLocaleString();
  const relativeFormatter = new Intl.RelativeTimeFormat(undefined, {
    numeric: "auto",
  });
  const diffMs = dt.getTime() - Date.now();
  const diffMinutes = Math.round(diffMs / (1000 * 60));
  const relative =
    Math.abs(diffMinutes) < 60
      ? relativeFormatter.format(diffMinutes, "minute")
      : relativeFormatter.format(Math.round(diffMinutes / 60), "hour");
  return `${absolute} (${relative})`;
};

const getStatusVariant = (status?: string | null) => {
  const normalized = (status || "").toLowerCase();
  if (!normalized) return "outline" as const;
  if (["sent", "delivered", "queued"].includes(normalized)) return "secondary" as const;
  if (["rate_limited", "no_phone", "disabled"].includes(normalized)) return "outline" as const;
  if (["twilio_error", "error", "failed"].includes(normalized)) return "destructive" as const;
  return "default" as const;
};

const getStatusLabel = (status?: string | null) => {
  if (!status) return "Unknown";
  switch (status.toLowerCase()) {
    case "sent":
      return "Sent";
    case "delivered":
      return "Delivered";
    case "queued":
      return "Queued";
    case "rate_limited":
      return "Rate limited";
    case "no_phone":
      return "No phone";
    case "disabled":
      return "Alerts disabled";
    case "twilio_error":
      return "Twilio error";
    default:
      return status;
  }
};

const RecentAlerts = () => {
  const [alerts, setAlerts] = useState<RecentAlert[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = async () => {
    setLoading(true);
    try {
      const data = await fetchRecentAlerts();
      setAlerts(data);
      setError(null);
    } catch (err: any) {
      console.error(err);
      setError(err?.message || "Failed to load alerts");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    refresh();
    const id = setInterval(refresh, 15000);
    return () => clearInterval(id);
  }, []);

  const emptyState = useMemo(() => !loading && alerts.length === 0, [loading, alerts]);

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <div className="flex flex-wrap items-center justify-between gap-4">
          <div>
            <h1 className="text-3xl font-semibold">Recent Alerts</h1>
            <p className="text-muted-foreground">
              Helmet-off detections sent as SMS alerts.
            </p>
          </div>
          <Button variant="outline" onClick={refresh} disabled={loading}>
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Refreshing…
              </>
            ) : (
              <>
                <RefreshCw className="h-4 w-4 mr-2" />
                Refresh
              </>
            )}
          </Button>
        </div>

        <Card className="glass-card border-white/10">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
            <CardTitle className="text-xl font-semibold flex items-center gap-2">
              <AlertTriangle className="h-5 w-5 text-destructive" />
              Total Alerts
            </CardTitle>
            <Badge variant="destructive">{alerts.length}</Badge>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="text-sm text-destructive rounded-md border border-destructive/40 bg-destructive/10 p-3">
                {error}
              </div>
            )}
            {emptyState && (
              <div className="text-muted-foreground text-sm py-6 text-center">
                No recent helmet violations logged.
              </div>
            )}
            {!emptyState && (
              <div className="space-y-3">
                {alerts.map((alert) => (
                  <div
                    key={alert.id}
                    className="flex flex-wrap items-center justify-between gap-4 border border-white/10 rounded-lg p-4 bg-background/60"
                  >
                    <div className="flex items-center gap-3">
                      <div className="h-10 w-10 rounded-full bg-destructive/10 text-destructive flex items-center justify-center">
                        <AlertTriangle className="h-5 w-5" />
                      </div>
                      <div>
                        <p className="font-semibold">
                          {alert.worker_name || "Unknown worker"}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {formatTimestamp(alert.timestamp)}
                        </p>
                        <p className="text-xs text-muted-foreground/80 mt-1">
                          SMS to {alert.phone || "unknown phone"}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Badge variant="destructive">Helmet Off</Badge>
                        <Badge variant={getStatusVariant(alert.sms_status)}>
                          {getStatusLabel(alert.sms_status)}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mt-1">
                        {alert.location_name || "Unknown location"}
                      </p>
                      {alert.sms_sid && (
                        <p className="text-xs text-muted-foreground/70 mt-1">
                          SID: {alert.sms_sid}
                        </p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </DashboardLayout>
  );
};

export default RecentAlerts;
