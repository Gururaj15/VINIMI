import { Link } from "react-router-dom";
import { ArrowRight, Headset } from "lucide-react";

const FinalCTA = () => (
  <section className="rounded-3xl border border-slate-200 bg-gradient-to-r from-[#f8fafc] via-white to-[#e0ecfe] p-8 md:p-10 shadow-lg flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
    <div className="space-y-2">
      <h3 className="text-2xl font-bold text-slate-900">Ready to see VINIMI in action?</h3>
      <p className="text-slate-700">
        Start monitoring now or talk to us about your cameras, locations, and safety requirements.
      </p>
    </div>
    <div className="flex flex-wrap gap-3">
      <Link
        to="/live"
        className="inline-flex items-center gap-2 px-5 py-3 rounded-full bg-blue-600 hover:bg-blue-700 text-white font-semibold shadow-md hover:translate-y-[-1px] transition-transform"
      >
        Start Monitoring Now <ArrowRight className="h-4 w-4" />
      </Link>
      <a
        href="mailto:hello@vinimi.ai"
        className="inline-flex items-center gap-2 px-5 py-3 rounded-full border border-slate-300 text-slate-800 font-semibold hover:border-blue-500 hover:text-blue-700 transition-colors bg-white shadow-sm"
      >
        <Headset className="h-4 w-4" /> Talk to Us
      </a>
    </div>
  </section>
);

export default FinalCTA;
