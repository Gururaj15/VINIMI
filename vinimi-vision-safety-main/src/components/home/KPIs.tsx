import { Bolt, CheckCircle2, MessageSquare, MonitorSmartphone } from "lucide-react";

const items = [
  { icon: Bolt, label: "<50ms Inference on-device" },
  { icon: CheckCircle2, label: ">95% Helmet Detection on curated sets" },
  { icon: MessageSquare, label: "SMS Alerts via Twilio" },
  { icon: MonitorSmartphone, label: "Works with IP cameras & RTSP" },
];

const KPIs = () => {
  return (
    <section className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {items.map((item) => (
        <div
          key={item.label}
          className="rounded-2xl border border-slate-200 bg-white p-4 flex items-start gap-3 shadow-sm hover:shadow-md transition"
        >
          <div className="p-2 rounded-lg bg-blue-50 text-blue-700">
            <item.icon className="h-5 w-5" />
          </div>
          <p className="text-sm text-slate-800 leading-snug">{item.label}</p>
        </div>
      ))}
    </section>
  );
};

export default KPIs;
