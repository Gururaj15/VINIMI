const steps = [
  {
    icon: "/vinimi-icons/step1_connect_camera.svg",
    title: "Connect a Camera",
    body: "Point VINIMI at RTSP/IP feeds or a simple browser webcam.",
  },
  {
    icon: "/vinimi-icons/step2_detect_recognize.svg",
    title: "Detect & Recognize",
    body: "Helmet detection plus face recognition with red/green overlays.",
  },
  {
    icon: "/vinimi-icons/step3_alert_act.svg",
    title: "Alert & Act",
    body: "Notify workers, review logs, export reports—right away.",
  },
];

const HowItWorks = () => (
  <section className="space-y-4">
    <h2 className="text-2xl font-bold text-slate-900">How It Works</h2>
    <div className="grid gap-4 md:grid-cols-3">
      {steps.map((step, idx) => (
        <div
          key={step.title}
          className="rounded-2xl border border-slate-200 bg-white p-5 flex flex-col gap-3 shadow-sm hover:shadow-md hover:border-slate-300 transition"
        >
          <div className="flex items-center gap-3">
            <span className="px-3 py-1 text-xs rounded-full bg-blue-50 text-blue-700 border border-blue-200">
              Step {idx + 1}
            </span>
          </div>
          <div className="flex items-start gap-3">
            <img src={step.icon} alt={step.title} className="h-8 w-8 opacity-90" />
            <div>
              <h3 className="text-lg font-semibold text-slate-900">{step.title}</h3>
              <p className="text-sm text-slate-700 leading-relaxed">{step.body}</p>
            </div>
          </div>
        </div>
      ))}
    </div>
  </section>
);

export default HowItWorks;
