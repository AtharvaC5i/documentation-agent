export default function HeroSection() {
  return (
    <section className="relative px-6 pt-28 pb-24 overflow-hidden">
      {/* Background grid */}
      <div
        className="absolute inset-0 pointer-events-none"
        style={{
          backgroundImage: `
            linear-gradient(rgba(0,0,0,0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(0,0,0,0.03) 1px, transparent 1px)
          `,
          backgroundSize: "48px 48px",
          maskImage:
            "radial-gradient(ellipse 80% 60% at 50% 0%, black 40%, transparent 100%)",
          WebkitMaskImage:
            "radial-gradient(ellipse 80% 60% at 50% 0%, black 40%, transparent 100%)",
        }}
      />

      {/* Teal glow */}
      <div
        className="absolute top-0 left-1/2 -translate-x-1/2 w-[700px] h-[400px] pointer-events-none"
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(13,148,136,0.07) 0%, transparent 70%)",
        }}
      />

      <div className="relative max-w-4xl mx-auto text-center">
        {/* Eyebrow */}
        <div className="inline-flex items-center gap-2 border border-gray-200 bg-gray-50 rounded-full px-4 py-1.5 mb-8 animate-fade-up">
          <span className="w-1.5 h-1.5 rounded-full bg-teal-500 animate-pulse" />
          <span className="text-xs font-medium text-gray-600 tracking-wide">
            Powered by Databricks Model Serving
          </span>
        </div>

        {/* Headline */}
        <h1 className="text-5xl md:text-6xl font-extrabold tracking-tight text-gray-900 leading-[1.08] mb-6 animate-fade-up delay-100">
          Documentation that
          <br />
          <span className="text-teal-700">writes itself.</span>
        </h1>

        {/* Subheadline */}
        <p className="text-lg text-gray-500 leading-relaxed max-w-2xl mx-auto mb-10 animate-fade-up delay-200">
          Three purpose-built AI agents that turn raw transcripts, codebases,
          and requirements into structured BRDs, technical documentation, and
          production-ready presentations — entirely on your infrastructure.
        </p>

        {/* CTAs */}
        <div className="flex items-center justify-center gap-4 animate-fade-up delay-300">
          <a
            href="#agents"
            className="inline-flex items-center gap-2 bg-teal-700 hover:bg-teal-800 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors duration-150 shadow-sm"
          >
            Explore agents
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </a>
          <a
            href="#how-it-works"
            className="inline-flex items-center gap-2 text-sm font-medium text-gray-500 hover:text-gray-800 transition-colors duration-150"
          >
            How it works
          </a>
        </div>

        {/* Feature chips */}
        <div className="flex flex-wrap items-center justify-center gap-2.5 mt-14 animate-fade-up delay-400">
          {[
            "3 Specialized Agents",
            "Databricks Model Serving",
            "Runs on your infrastructure",
            "Human-in-the-loop review",
            ".docx · .pptx export",
            "Vector search via ChromaDB",
          ].map((chip) => (
            <span
              key={chip}
              className="inline-flex items-center gap-1.5 text-xs font-medium text-gray-500 bg-gray-50 border border-gray-200 px-3 py-1.5 rounded-full"
            >
              <svg
                width="10"
                height="10"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="3"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="text-teal-500"
              >
                <path d="M20 6 9 17l-5-5" />
              </svg>
              {chip}
            </span>
          ))}
        </div>
      </div>

      <div className="absolute bottom-0 left-0 right-0 h-px bg-gray-100" />
    </section>
  );
}
