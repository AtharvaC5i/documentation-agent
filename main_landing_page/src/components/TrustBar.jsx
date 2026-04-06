const stats = [
  {
    value: "3",
    label: "AI Agents",
    description: "BRD generation, technical documentation, and PPT creation",
  },
  {
    value: "Local",
    label: "Vector Pipeline",
    description:
      "Chunking, embedding, and ChromaDB storage run entirely on your machine",
  },
  {
    value: "RAG",
    label: "Grounded output",
    description:
      "Every generated section is traceable to actual source code chunks",
  },
  {
    value: "0.70",
    label: "Quality threshold",
    description:
      "Sections scoring below 0.70 are automatically regenerated before delivery",
  },
];

export default function TrustBar() {
  return (
    <section className="border-y border-gray-100 bg-gray-50/60">
      <div className="max-w-6xl mx-auto px-6 py-12 grid grid-cols-2 md:grid-cols-4 gap-8">
        {stats.map((stat, i) => (
          <div key={i} className="flex flex-col gap-1">
            <span className="text-2xl font-extrabold text-gray-900 tracking-tight">
              {stat.value}
            </span>
            <span className="text-sm font-semibold text-gray-700">
              {stat.label}
            </span>
            <span className="text-xs text-gray-400 leading-snug mt-0.5">
              {stat.description}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
