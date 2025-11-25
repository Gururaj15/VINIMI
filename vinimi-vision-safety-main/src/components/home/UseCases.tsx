const cases = [
  {
    title: "Construction Sites",
    body: "Monitor entrances, scaffolding, and zones for helmet compliance.",
  },
  {
    title: "Warehouses",
    body: "Verify authorized staff in loading bays and restricted areas.",
  },
  {
    title: "Manufacturing",
    body: "Detect PPE and known operators around machinery and lines.",
  },
];

const UseCases = () => (
  <section className="space-y-4">
    <h2 className="text-2xl font-bold text-slate-900">Industry Use-Cases</h2>
    <div className="grid gap-4 md:grid-cols-3">
      {cases.map((c) => (
        <div
          key={c.title}
          className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm hover:shadow-md hover:border-slate-300 transition"
        >
          <h3 className="text-lg font-semibold text-slate-900 mb-2">{c.title}</h3>
          <p className="text-sm text-slate-700 leading-relaxed">{c.body}</p>
        </div>
      ))}
    </div>
  </section>
);

export default UseCases;
