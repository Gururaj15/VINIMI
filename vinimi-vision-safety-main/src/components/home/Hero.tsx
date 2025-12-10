import { useNavigate } from "react-router-dom";
import { ArrowRight, ShieldCheck, Sparkles } from "lucide-react";
import { isAuthed } from "@/lib/auth";
import brandLogo from "@/assets/logof.png";

const Hero = () => {
  const navigate = useNavigate();
  const handleStart = () => {
    if (isAuthed()) {
      navigate("/live");
    } else {
      navigate("/login");
    }
  };

  return (
    <section className="relative overflow-hidden rounded-3xl bg-gradient-to-br from-slate-900 via-slate-900/90 to-slate-800 p-10 md:p-14 shadow-2xl border border-white/10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_20%_20%,rgba(99,102,241,0.15),transparent_35%),radial-gradient(circle_at_80%_0%,rgba(56,189,248,0.2),transparent_25%),radial-gradient(circle_at_50%_80%,rgba(168,85,247,0.12),transparent_30%)]" />
      <div className="relative grid gap-10 lg:grid-cols-[1.1fr_0.9fr] items-center">
        <div className="space-y-6">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/5 text-primary text-sm border border-primary/30">
            <Sparkles className="h-4 w-4" />
            Real-time PPE & Face Recognition
          </div>
          <h1 className="text-3xl md:text-4xl font-extrabold leading-tight text-white flex items-start gap-3">
            <img
              src={brandLogo}
              alt="VINIMI logo"
              className="h-10 w-10 rounded-lg bg-white/10 p-2"
              style={{ width: "9rem", height: "9rem" }}
            />
            <span className="space-y-1 leading-tight">
              <span className="block">VINIMI — Real-Time PPE</span>
              <span className="block">& Face Recognition for Safer Sites</span>
            </span>
          </h1>
          <p className="text-lg text-slate-200 max-w-2xl">
            Detect hard-hats, recognize authorized workers, and alert instantly—right from your CCTV or webcams.
          </p>
          <div className="flex flex-wrap gap-4">
            <button
              onClick={handleStart}
              className="inline-flex items-center gap-2 px-5 py-3 rounded-full bg-primary text-white font-semibold shadow-lg shadow-primary/40 hover:translate-y-[-1px] transition-transform"
            >
              Start Monitoring Now
              <ArrowRight className="h-4 w-4" />
            </button>
            <a
              href="mailto:hello@vinimi.ai"
              className="inline-flex items-center gap-2 px-5 py-3 rounded-full border border-white/20 text-white font-semibold hover:border-primary/60 hover:text-primary transition-colors"
            >
              Book a Demo
            </a>
          </div>
          <div className="flex items-center gap-6 text-sm text-slate-300 pt-4 flex-wrap">
            <span className="font-semibold text-white flex items-center gap-2">
              <ShieldCheck className="h-4 w-4 text-primary" /> Trusted by construction & manufacturing teams
            </span>
            <div className="flex gap-3 opacity-80">
              <div className="px-3 py-1 rounded-md bg-white/5 border border-white/10 text-xs uppercase tracking-[0.2em]">
                RTSP/IP Ready
              </div>
              <div className="px-3 py-1 rounded-md bg-white/5 border border-white/10 text-xs uppercase tracking-[0.2em]">
                On-Prem Friendly
              </div>
            </div>
          </div>
        </div>
        <div className="relative">
          <div className="rounded-2xl border border-white/10 bg-black/30 p-6 backdrop-blur">
            <div className="text-sm text-slate-300 mb-3">Live overlays</div>
            <div className="aspect-video rounded-xl bg-gradient-to-br from-primary/20 via-slate-900 to-secondary/10 flex items-center justify-center border border-white/10 shadow-inner">
              <div className="w-full h-full grid grid-cols-2 gap-2 p-4">
                <div className="rounded-lg border border-emerald-400/50 bg-emerald-400/10 text-emerald-100 text-xs p-3">
                  Recognized Worker
                  <div className="mt-2 text-lg font-semibold">Anita K.</div>
                  <div className="text-emerald-200/80 text-xs">Helmet: On</div>
                </div>
                <div className="rounded-lg border border-rose-400/60 bg-rose-400/10 text-rose-100 text-xs p-3">
                  Unknown Person
                  <div className="mt-2 text-lg font-semibold">Flagged</div>
                  <div className="text-rose-200/80 text-xs">Helmet: Missing</div>
                </div>
                <div className="rounded-lg border border-cyan-400/60 bg-cyan-400/10 text-cyan-100 text-xs p-3">
                  RTSP Camera
                  <div className="mt-2 text-lg font-semibold">Gate-02</div>
                  <div className="text-cyan-200/80 text-xs">Stream: Stable</div>
                </div>
                <div className="rounded-lg border border-yellow-400/60 bg-yellow-400/10 text-yellow-100 text-xs p-3">
                  Alerts & Logs
                  <div className="mt-2 text-lg font-semibold">SMS via Twilio</div>
                  <div className="text-yellow-200/80 text-xs">PDF exports</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};

export default Hero;
