const features = [
  {
    icon: "/vinimi-icons/hardhat_compliance.svg",
    title: "Hard-Hat Compliance",
    body: "Automatic helmet checks with red/green overlays and clear status badges.",
  },
  {
    icon: "/vinimi-icons/face_recognition.svg",
    title: "Face Recognition",
    body: "Identify registered workers from embeddings; keep unknowns contained.",
  },
  {
    icon: "/vinimi-icons/manager_portal.svg",
    title: "Manager Portal",
    body: "Company-scoped access; manage rosters and permissions.",
  },
  {
    icon: "/vinimi-icons/alerts_reports.svg",
    title: "Alerts & Reports",
    body: "Twilio SMS alerts; export incidents and activity logs as PDF.",
  },
  {
    icon: "/vinimi-icons/bring_your_cameras.svg",
    title: "Bring Your Cameras",
    body: "Works with RTSP/IP cameras or browser webcams.",
  },
  {
    icon: "/vinimi-icons/private_flexible.svg",
    title: "Private & Flexible",
    body: "Local inference; MySQL storage; on-prem or cloud.",
  },
];

const Features = () => {
  return (
    <section className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-2xl font-bold text-slate-900">Product Value</h2>
      </div>
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {features.map((f) => (
          <div
            key={f.title}
            className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md hover:border-slate-300 transition"
          >
            <div className="flex items-start gap-3 mb-3">
              <img src={f.icon} alt={f.title} className="h-8 w-8 opacity-90" />
              <h3 className="text-lg font-semibold text-slate-900">{f.title}</h3>
            </div>
            <p className="text-sm text-slate-700 leading-relaxed">{f.body}</p>
          </div>
        ))}
      </div>
    </section>
  );
};

export default Features;
