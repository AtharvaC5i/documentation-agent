const steps = [
  {
    number: "01",
    title: "Select the right agent",
    description:
      "Choose between the BRD agent for requirements gathering, the Technical Documentation agent for codebase analysis, or the AI Solution Architect for turning documents into architecture and presentations.",
    detail: "BRD Agent · Tech Doc Agent · PPT Agent",
  },
  {
    number: "02",
    title: "Upload your source material",
    description:
      "Provide what you already have — meeting transcripts, user stories, a GitHub repository URL, a ZIP of your codebase, or a completed BRD. No reformatting or preprocessing required.",
    detail: "Transcripts · User stories · GitHub URL · ZIP · BRD docs",
  },
  {
    number: "03",
    title: "AI analyses, retrieves, and generates",
    description:
      "The agent analyses your input, builds a local vector store for semantic retrieval, and generates each section using RAG — grounding every output in your actual source material, not assumptions.",
    detail: "ChromaDB · all-MiniLM-L6-v2 · Databricks Model Serving",
  },
  {
    number: "04",
    title: "Review section by section",
    description:
      "Every generated section is presented for your approval. Edit content freely, approve, reject, or trigger a fresh regeneration pass. Sections scoring below the quality threshold are auto-regenerated before you even see them.",
    detail: "Approve · Edit · Reject · Regenerate · Reorder",
  },
  {
    number: "05",
    title: "Export and deliver",
    description:
      "Assemble the final document with a single action. The output includes a title page, auto-generated table of contents, heading hierarchy, code blocks, and tables — downloaded as .docx, .pdf.",
    detail: ".docx · .pptx",
  },
  {
    number: "06",
    title: "Keep it alive",
    description:
      "The BRD agent supports Living BRDs — upload new transcripts at any time to surface requirement changes, apply diffs, and maintain a running version history without starting from scratch.",
    detail: "Version history · Diffs · Continuous updates",
  },
];

export default function HowItWorks() {
  return (
    <section id="how-it-works" className="bg-gray-50 border-t border-gray-100">
      <div className="max-w-6xl mx-auto px-6 py-24">
        {/* Header */}
        <div className="max-w-2xl mb-16">
          <p className="text-xs font-semibold tracking-widest text-gray-400 uppercase mb-4">
            How it works
          </p>
          <h2 className="text-3xl font-extrabold tracking-tight text-gray-900 mb-4">
            From raw input to finished document.
          </h2>
          <p className="text-base text-gray-500 leading-relaxed">
            Every agent follows the same structured pipeline — ingest, analyse,
            generate, review, export. Once you have used one, the others feel
            immediately familiar.
          </p>
        </div>

        {/* Steps grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-px bg-gray-200 rounded-2xl overflow-hidden border border-gray-200">
          {steps.map((step, i) => (
            <div
              key={i}
              className="bg-gray-50 hover:bg-white p-8 flex flex-col gap-4 transition-colors duration-150"
            >
              {/* Number */}
              <span className="text-xs font-bold tracking-widest text-gray-300 uppercase">
                {step.number}
              </span>

              {/* Title */}
              <h3 className="text-base font-bold text-gray-900 leading-snug">
                {step.title}
              </h3>

              {/* Description */}
              <p className="text-sm text-gray-500 leading-relaxed">
                {step.description}
              </p>

              {/* Detail tag */}
              <div className="mt-auto pt-4 border-t border-gray-200">
                <span className="text-xs font-mono text-gray-400">
                  {step.detail}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
