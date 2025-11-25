const testimonials = [
  {
    quote:
      "VINIMI gives us instant confidence—helmets are tracked, and unknown faces are flagged before they enter critical zones.",
    name: "Operations Lead",
    company: "Tier-1 Contractor",
  },
  {
    quote:
      "We plugged in our RTSP feeds and got alerts the same day. The PDF logs make audits painless.",
    name: "Safety Manager",
    company: "Manufacturing Plant",
  },
];

const logos = ["BuildCo", "IndusX", "SafeWorks", "MetroConstruct"];

const SocialProof = () => (
  <section className="space-y-6">
    <h2 className="text-2xl font-bold text-slate-900">Customers & Social Proof</h2>
    <div className="grid gap-4 md:grid-cols-2">
      {testimonials.map((t, idx) => (
        <div
          key={idx}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md hover:border-slate-300 transition"
        >
          <p className="text-slate-700 leading-relaxed mb-3">“{t.quote}”</p>
          <div className="text-sm text-slate-500">
            <span className="text-slate-900 font-semibold">{t.name}</span> — {t.company}
          </div>
        </div>
      ))}
    </div>
    <div className="flex flex-wrap gap-3 items-center text-sm text-slate-600">
      <span className="uppercase tracking-[0.2em] text-slate-500 text-xs">As seen in</span>
      {logos.map((logo) => (
        <div
          key={logo}
          className="px-3 py-2 rounded-lg border border-slate-200 bg-slate-50 text-slate-700 text-xs uppercase tracking-[0.2em]"
        >
          {logo}
        </div>
      ))}
    </div>
  </section>
);

export default SocialProof;
