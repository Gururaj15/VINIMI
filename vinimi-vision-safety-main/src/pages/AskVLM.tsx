import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Upload, AlertCircle, Sparkles } from "lucide-react";
import DashboardLayout from "@/components/DashboardLayout";
import { useToast } from "@/hooks/use-toast";

const LIVE_API_BASE =
  import.meta.env.VITE_LIVE_API_URL || "http://localhost:8001";
const DETECT_ENDPOINT = `${LIVE_API_BASE}/api/detect/frame`;

type DetectResponse = {
  person?: {
    name?: string;
    worker_id?: number | null;
    company?: string | null;
    location?: string | null;
  };
  ppe?: {
    helmet_on?: boolean;
  };
  faces?: Array<{
    name?: string;
    ppe?: { helmet_on?: boolean };
    x?: number;
    y?: number;
    w?: number;
    h?: number;
  }>;
};

interface FaceResult {
  id: string;
  label: string;
  helmetOn: boolean;
}

interface AnalysisResult {
  workerName: string;
  workerId: number | null;
  helmetOn: boolean;
  reasoning: string;
  imageUrl: string;
  faces: FaceResult[];
}

const AskVLM = () => {
  const { toast } = useToast();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [question, setQuestion] = useState("");

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setSelectedFile(file);
      setPreviewUrl(URL.createObjectURL(file));
      setResult(null);
    }
  };

  const handleAnalyze = async () => {
    if (!selectedFile) return;

    if (!selectedFile.type.startsWith("image/")) {
      toast({
        title: "Unsupported media",
        description: "Image uploads are required for analysis right now.",
        variant: "destructive",
      });
      return;
    }

    setIsAnalyzing(true);

    try {
      const formData = new FormData();
      formData.append("frame", selectedFile);

      const res = await fetch(DETECT_ENDPOINT, {
        method: "POST",
        body: formData,
      });

      if (!res.ok) {
        const text = await res.text();
        throw new Error(text || `HTTP ${res.status}`);
      }

      const data: DetectResponse = await res.json();
      const personName = data.person?.name || "Unknown";
      const workerId = data.person?.worker_id ?? null;
      const helmetFlag = Boolean(data.ppe?.helmet_on);

      const faces: FaceResult[] = (data.faces || []).map((face, idx) => ({
        id: `face-${idx}`,
        label: face?.name && face.name !== "Unknown"
          ? face.name
          : `Person ${idx + 1}`,
        helmetOn: face?.ppe?.helmet_on ?? helmetFlag,
      }));

      const reasoningParts: string[] = [];
      reasoningParts.push(
        personName === "Unknown"
          ? "No registered worker matched this face."
          : `Face recognition matched ${personName}.`
      );
      reasoningParts.push(
        helmetFlag
          ? "Helmet presence detected in the uploaded frame."
          : "Helmet appears to be missing or not detected."
      );
      if (faces.length > 1) {
        reasoningParts.push(`Multiple faces (${faces.length}) were detected.`);
      }
      if (question.trim()) {
        reasoningParts.push(
          `Question asked: "${question.trim()}". Analysis is based on this media.`
        );
      }

      const newResult: AnalysisResult = {
        workerName: personName,
        workerId,
        helmetOn: helmetFlag,
        reasoning: reasoningParts.join(" "),
        imageUrl: previewUrl || "",
        faces,
      };

      setResult(newResult);

      toast({
        title: "Analysis complete",
        description: helmetFlag
          ? "Helmet detected in the uploaded frame."
          : "Helmet appears to be missing.",
      });
    } catch (err: any) {
      console.error(err);
      toast({
        title: "Analysis failed",
        description: err?.message || "Could not analyze this file.",
        variant: "destructive",
      });
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <DashboardLayout>
      <motion.div 
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="space-y-6"
      >
        <div className="flex items-center gap-3">
          <Sparkles className="h-8 w-8 text-primary animate-pulse-glow" />
          <div>
            <h1 className="text-3xl font-bold bg-gradient-to-r from-primary to-secondary bg-clip-text text-transparent">Ask VINIMI</h1>
            <p className="text-muted-foreground">Upload images or videos for AI-powered analysis</p>
          </div>
        </div>

        <div className="grid gap-6 lg:grid-cols-2">
          {/* Upload Section */}
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.1 }}
          >
            <Card className="glass-card hover-lift border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Upload className="h-5 w-5 text-primary" />
                  Upload Media
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="border-2 border-dashed border-primary/30 rounded-lg p-8 text-center hover:border-primary/60 transition-colors bg-primary/5">
                  <input
                    type="file"
                    id="file-upload"
                    className="hidden"
                    accept="image/*,video/*"
                    onChange={handleFileSelect}
                  />
                  <label htmlFor="file-upload" className="cursor-pointer">
                    <Upload className="h-12 w-12 mx-auto mb-4 text-primary animate-float" />
                    <p className="text-sm font-medium mb-1">Click to upload</p>
                    <p className="text-xs text-muted-foreground">
                      Supports images (JPG, PNG) and videos (MP4, AVI)
                    </p>
                  </label>
                </div>

                {previewUrl && (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="space-y-4"
                  >
                    <Label>Preview</Label>
                    {selectedFile?.type.startsWith('image/') ? (
                      <img
                        src={previewUrl}
                        alt="Preview"
                        className="w-full h-64 object-cover rounded-lg border border-white/20 shadow-lg"
                      />
                    ) : (
                      <video
                        src={previewUrl}
                        controls
                        className="w-full h-64 rounded-lg border border-white/20 shadow-lg"
                      />
                    )}
                    
                    <div className="space-y-2">
                      <Label>Ask a question about this media</Label>
                      <Textarea
                        placeholder="e.g., Is the worker wearing proper safety equipment?"
                        value={question}
                        onChange={(e) => setQuestion(e.target.value)}
                        className="glass-input resize-none"
                        rows={3}
                      />
                    </div>

                    <Button
                      className="w-full neon-glow group"
                      onClick={handleAnalyze}
                      disabled={isAnalyzing}
                    >
                      <Sparkles className="h-4 w-4 mr-2 group-hover:animate-spin" />
                      {isAnalyzing ? "Analyzing..." : "Analyze with VINIMI"}
                    </Button>
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>

          {/* Results Section */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.2 }}
          >
            <Card className="glass-card border-white/10">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-accent" />
                  Analysis Results
                </CardTitle>
              </CardHeader>
              <CardContent>
                {!result ? (
                  <div className="flex flex-col items-center justify-center h-64 text-center">
                    <AlertCircle className="h-12 w-12 text-muted-foreground mb-4 animate-pulse" />
                    <p className="text-muted-foreground">
                      Upload an image or video to see analysis results
                    </p>
                  </div>
                ) : (
                  <motion.div 
                    initial={{ opacity: 0, y: 10 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="space-y-4"
                  >
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-lg bg-primary/10 border border-primary/20">
                        <Label className="text-muted-foreground text-xs">Worker Name</Label>
                        <p className="text-lg font-semibold text-primary">{result.workerName}</p>
                      </div>
                      <div className="p-4 rounded-lg bg-accent/10 border border-accent/20">
                        <Label className="text-muted-foreground text-xs">Worker ID</Label>
                        <p className="text-lg font-semibold text-accent">
                          {result.workerId || "N/A"}
                        </p>
                      </div>
                    </div>

                    <div className="p-4 rounded-lg bg-muted/50 border border-white/10">
                      <Label className="text-muted-foreground text-xs">Helmet Status</Label>
                      <div className="mt-2">
                        <Badge
                          variant={result.helmetOn ? "outline" : "destructive"}
                          className={result.helmetOn ? "bg-success/20 text-success border-success/50 neon-glow" : "neon-glow"}
                        >
                          {result.helmetOn ? "✓ Helmet On" : "✗ Helmet Off"}
                        </Badge>
                      </div>
                    </div>

                    {result.faces.length > 0 && (
                      <div className="rounded-lg border border-white/10 bg-muted/30 p-4 space-y-3">
                        <Label className="text-muted-foreground text-xs">
                          Detected people
                        </Label>
                        <div className="grid gap-3 sm:grid-cols-2">
                          {result.faces.map((face) => (
                            <div
                              key={face.id}
                              className="rounded-lg border border-white/10 bg-background/40 px-3 py-2"
                            >
                              <p className="text-sm font-semibold text-white">
                                {face.label}
                              </p>
                              <Badge
                                variant={face.helmetOn ? "outline" : "destructive"}
                                className="mt-2"
                              >
                                {face.helmetOn ? "Helmet On" : "Helmet Off"}
                              </Badge>
                            </div>
                          ))}
                        </div>
                      </div>
                    )}

                    <div className="p-4 rounded-lg bg-muted/30 border border-white/10">
                      <Label className="text-muted-foreground text-xs flex items-center gap-2">
                        <Sparkles className="h-3 w-3" />
                        Vinimi Reasoning
                      </Label>
                      <p className="text-sm mt-2 leading-relaxed">
                        {result.reasoning}
                      </p>
                    </div>

                    {result.imageUrl && (
                      <div>
                        <Label className="text-muted-foreground text-xs">Snapshot</Label>
                        <img
                          src={result.imageUrl}
                          alt="Analysis snapshot"
                          className="w-full h-48 object-cover rounded-lg border border-white/20 mt-2 shadow-lg"
                        />
                      </div>
                    )}
                  </motion.div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </motion.div>
    </DashboardLayout>
  );
};

export default AskVLM;
