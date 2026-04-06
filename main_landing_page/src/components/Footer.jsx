const agents = [
  {
    name: "BRD Generation Agent",
    port: "localhost:3000",
    url: "http://localhost:3000",
  },
  {
    name: "Technical Documentation Agent",
    port: "localhost:5174",
    url: "http://localhost:5174",
  },
  {
    name: "AI Solution Architect Agent",
    port: "localhost:5175",
    url: "http://localhost:5175",
  },
];

export default function Footer() {
  return (
    <footer className="border-t border-gray-100 bg-white">
      <div className="max-w-6xl mx-auto px-6 py-12">
        <div className="flex flex-col md:flex-row items-start justify-between gap-10">
          {/* Brand */}
          <div className="flex flex-col gap-3 max-w-xs">
            <div className="flex items-center gap-2.5">
              <svg
                width="22"
                height="22"
                viewBox="0 0 24 24"
                fill="none"
                aria-label="DocuFlow logo"
              >
                <rect
                  x="3"
                  y="3"
                  width="18"
                  height="18"
                  rx="4"
                  fill="#0d9488"
                  opacity="0.12"
                />
                <path
                  d="M7 8h5M7 12h10M7 16h8"
                  stroke="#0d9488"
                  strokeWidth="1.75"
                  strokeLinecap="round"
                />
              </svg>
              <span className="text-sm font-bold text-gray-900 tracking-tight">
                DocuFlow
              </span>
            </div>
            <p className="text-xs text-gray-400 leading-relaxed">
              AI documentation platform running entirely on your infrastructure.
              LLM inference via Databricks Model Serving.
            </p>
          </div>

          {/* Agents */}
          <div className="flex flex-col gap-3">
            <p className="text-xs font-semibold tracking-widest text-gray-400 uppercase">
              Agents
            </p>
            <ul className="flex flex-col gap-2.5">
              {agents.map((agent) => (
                <li key={agent.name} className="flex items-center gap-3">
                  <a
                    href={agent.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm text-gray-600 hover:text-gray-900 transition-colors duration-150"
                  >
                    {agent.name}
                  </a>
                  <span className="text-xs font-mono text-gray-300">
                    {agent.port}
                  </span>
                </li>
              ))}
            </ul>
          </div>

          {/* Stack */}
          <div className="flex flex-col gap-3">
            <p className="text-xs font-semibold tracking-widest text-gray-400 uppercase">
              Stack
            </p>
            <ul className="flex flex-col gap-2">
              {[
                "FastAPI · Uvicorn · Python",
                "React · Vite · Tailwind CSS",
                "ChromaDB · all-MiniLM-L6-v2",
                "Databricks Model Serving",
                ".docx · .pdf · .pptx export",
              ].map((item) => (
                <li key={item} className="text-xs text-gray-400">
                  {item}
                </li>
              ))}
            </ul>
          </div>
        </div>

        {/* Bottom */}
        <div className="mt-10 pt-6 border-t border-gray-100 flex flex-col md:flex-row items-start md:items-center justify-between gap-2">
          <p className="text-xs text-gray-300">
            Internal development platform · Running on localhost
          </p>
          <p className="text-xs text-gray-300">FastAPI · React · Databricks</p>
        </div>
      </div>
    </footer>
  );
}
