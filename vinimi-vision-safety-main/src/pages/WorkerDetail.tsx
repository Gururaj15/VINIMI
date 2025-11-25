// src/pages/WorkerDetail.tsx
import { useEffect, useState } from "react";
import { useParams, Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  ArrowLeft,
  Phone,
  MapPin,
  Calendar,
  AlertTriangle,
} from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";
import { useToast } from "@/hooks/use-toast";
import {
  fetchWorker,
  fetchWorkerMedia,
  fetchWorkerViolations,
  sendTestAlertSms,
  WorkerApi,
  WorkerImage,
  WorkerViolation,
} from "@/lib/api";

const WorkerDetail = () => {
  const { id } = useParams<{ id: string }>();
  const { toast } = useToast();

  const [worker, setWorker] = useState<WorkerApi | null>(null);
  const [loading, setLoading] = useState(true);
  const [sendingTestSms, setSendingTestSms] = useState(false);

  // --- load worker from backend ---
  useEffect(() => {
    if (!id) return;

    (async () => {
      try {
        const workerId = Number(id);
        const [detail, media, violations] = await Promise.all([
          fetchWorker(workerId),
          fetchWorkerMedia(workerId),
          fetchWorkerViolations(workerId),
        ]);
        setWorker({
          ...detail,
          images: media,
          violations,
        });
      } catch (err: any) {
        console.error(err);
        toast({
          title: "Failed to load worker",
          description: err?.message || "Please try again.",
          variant: "destructive",
        });
      } finally {
        setLoading(false);
      }
    })();
  }, [id, toast]);

  const handleSendTestSms = async () => {
    if (!worker) return;
    const phone = (worker.phone || "").trim();
    if (!phone || phone.toLowerCase() === "unknown") {
      toast({
        title: "Phone number unavailable",
        description:
          "Add a valid phone number for this worker before sending SMS alerts.",
        variant: "destructive",
      });
      return;
    }

    setSendingTestSms(true);
    try {
      const message = `VINIMI Safety Alert: You violated safety helmet compliance. Wear your helmet immediately.`;
      const res = await sendTestAlertSms(phone, message, worker.id, worker.name);
      toast({
        title: "Test SMS sent",
        description: res.sid
          ? `Status: ${res.status} (SID ${res.sid})`
          : `Status: ${res.status}`,
      });
    } catch (err: any) {
      toast({
        title: "Failed to send SMS",
        description: err?.message || "Unable to send SMS. Please try again.",
        variant: "destructive",
      });
    } finally {
      setSendingTestSms(false);
    }
  };

  if (loading) {
    return (
      <DashboardLayout>
        <div className="p-6 text-muted-foreground">Loading worker…</div>
      </DashboardLayout>
    );
  }

  if (!worker) {
    return (
      <DashboardLayout>
        <div className="p-6 space-y-4">
          <Link to="/workers">
            <Button variant="ghost">
              <ArrowLeft className="h-4 w-4 mr-2" />
              Back to Workers
            </Button>
          </Link>
          <Card>
            <CardHeader>
              <CardTitle>Worker not found</CardTitle>
            </CardHeader>
          </Card>
        </div>
      </DashboardLayout>
    );
  }

  // --- derive images & violations from worker ---
  const images: WorkerImage[] = worker.images ?? [];
  const violations: WorkerViolation[] = worker.violations ?? [];
  const violationsCount = violations.length;
  const phoneValue = (worker.phone || "").trim();
  const hasDialablePhone =
    !!phoneValue && phoneValue.toLowerCase() !== "unknown";

  return (
    <DashboardLayout>
      <div className="space-y-6">
        <Link to="/workers">
          <Button variant="ghost">
            <ArrowLeft className="h-4 w-4 mr-2" />
            Back to Workers
          </Button>
        </Link>

        {/* Worker header */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div>
                <CardTitle className="text-3xl mb-2">
                  {worker.name}
                </CardTitle>
                <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
                  <div className="flex items-center gap-1">
                    <Phone className="h-4 w-4" />
                    {worker.phone || "—"}
                  </div>
                  <div className="flex items-center gap-1">
                    <MapPin className="h-4 w-4" />
                    {worker.location_name || "Unknown location"}
                  </div>
                  <div className="flex items-center gap-1">
                    <Calendar className="h-4 w-4" />
                    Joined {worker.joined_at}
                  </div>
                </div>
              </div>
              <div className="flex flex-col items-end gap-3 sm:flex-row sm:items-center">
                <Badge
                  variant={
                    violationsCount > 0 ? "destructive" : "secondary"
                  }
                >
                  {violationsCount}{" "}
                  {violationsCount === 1 ? "Violation" : "Violations"}
                </Badge>
                <Button
                  variant="outline"
                  onClick={handleSendTestSms}
                  disabled={sendingTestSms || !hasDialablePhone}
                  title={
                    hasDialablePhone
                      ? "Send a Twilio test SMS to this worker"
                      : "Add a valid phone number to enable SMS tests"
                  }
                >
                  {sendingTestSms ? "Sending..." : "Send Test SMS"}
                </Button>
              </div>
            </div>
          </CardHeader>
        </Card>

        {/* Tabs */}
        <Tabs defaultValue="images" className="space-y-4">
          <TabsList>
            <TabsTrigger value="images">Images</TabsTrigger>
            <TabsTrigger value="videos">Videos</TabsTrigger>
            <TabsTrigger value="violations">Violation History</TabsTrigger>
          </TabsList>

          {/* IMAGES TAB – real images from backend */}
          <TabsContent value="images">
            <Card>
              <CardHeader>
                <CardTitle>Face Images</CardTitle>
              </CardHeader>
              <CardContent>
                {images.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No images captured yet for this worker.
                  </p>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {images.map((image, idx) => {
                      const isViolation = image.helmet_on === false;
                      const capturedAt =
                        typeof image.captured_at === "number"
                          ? new Date(image.captured_at * 1000).toISOString()
                          : image.captured_at;
                      return (
                        <div
                          key={image.id ?? idx}
                          className={`space-y-2 rounded-lg border overflow-hidden ${
                            isViolation
                              ? "border-red-500/70 ring-1 ring-red-500/50"
                              : "border-border"
                          }`}
                        >
                          <div className="relative">
                            <img
                              src={image.url}
                              alt={`Worker image ${image.id}`}
                              className="w-full h-48 object-cover"
                            />
                            {isViolation && (
                              <div className="absolute top-2 right-2 rounded-full bg-red-600 text-white text-xs px-2 py-1 flex items-center gap-1">
                                <span className="font-semibold">✕</span>
                                <span>No Helmet</span>
                              </div>
                            )}
                          </div>
                          <div className="px-3 pb-3 text-sm">
                            <p className="font-medium">
                              {image.type || "Face Capture"}
                            </p>
                            <p className="text-muted-foreground">
                              {capturedAt}
                            </p>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* VIDEOS TAB – still placeholder for now */}
          <TabsContent value="videos">
            <Card>
              <CardHeader>
                <CardTitle>Video Records</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-muted-foreground">
                  Video records are not wired to the backend yet.
                </p>
              </CardContent>
            </Card>
          </TabsContent>

          {/* VIOLATIONS TAB – from worker.violations */}
          <TabsContent value="violations">
            <Card>
              <CardHeader>
                <CardTitle>Violation History</CardTitle>
              </CardHeader>
              <CardContent>
                {violations.length === 0 ? (
                  <p className="text-sm text-muted-foreground">
                    No violations recorded for this worker.
                  </p>
                ) : (
                  <div className="space-y-4">
                    {violations.map((violation) => (
                      <div
                        key={violation.id}
                        className="flex items-start gap-4 p-4 border rounded-lg"
                      >
                        <AlertTriangle
                          className={`h-5 w-5 mt-1 ${
                            violation.severity === "high"
                              ? "text-destructive"
                              : "text-yellow-400"
                          }`}
                        />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <h4 className="font-semibold">
                              {violation.reason}
                            </h4>
                            <Badge
                              variant={
                                violation.severity === "high"
                                  ? "destructive"
                                  : "secondary"
                              }
                            >
                              {violation.severity}
                            </Badge>
                          </div>
                          <p className="text-sm text-muted-foreground">
                            {violation.location_name || "Unknown site"} •{" "}
                            {violation.timestamp}
                          </p>
                        </div>
                        {violation.image_url && (
                          <img
                            src={violation.image_url}
                            alt="Violation frame"
                            className="w-24 h-16 object-cover rounded-md border"
                          />
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </DashboardLayout>
  );
};

export default WorkerDetail;
