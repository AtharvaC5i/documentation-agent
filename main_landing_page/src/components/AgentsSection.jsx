import AgentCard from "./AgentCard";

const agents = [
  {
    id: "brd",
    number: "01",
    title: "BRD Generation Agent",
    tagline: "Requirements, extracted and structured.",
    description:
      "Ingests meeting transcripts and user stories, extracts every business requirement using AI, surfaces conflicts between competing requirements, and assembles a fully structured, review-ready Business Requirements Document — section by section.",
    features: [
      "Transcript and user story ingestion",
      "AI-powered requirement extraction",
      "Automated conflict detection and guided resolution",
      "Suggested section selection based on input content",
      "Section-level approval, editing, and regeneration",
      "Follow-up email generation for stakeholders",
      "Living BRD — update with new transcripts over time",
      "Traceability matrix generation",
      "Export as .docx with full version history",
    ],
    tech: ["FastAPI", "React", "Databricks LLM", "Port 3000"],
    url: "http://localhost:3000",
    accent: "teal",
  },
  {
    id: "techdoc",
    number: "02",
    title: "Technical Documentation Agent",
    tagline: "Point it at your codebase. Get a document.",
    description:
      "Analyses your source code, understands your stack, retrieves the most relevant code context for each section using semantic vector search, and generates high-quality technical prose grounded in actual code — not guesswork. Delivered as a .docx or .pdf.",
    features: [
      "GitHub URL or ZIP upload ingestion",
      "Automatic noise filtering — removes node_modules, build artefacts, binaries",
      "Static analysis: languages, frameworks, databases, APIs, infra signals",
      "AI-suggested documentation sections based on detected stack",
      "Local ChromaDB vector store — chunking and embedding run on CPU",
      "RAPTOR hierarchy for codebases over 50k LOC",
      "RAG generation per section via Databricks Model Serving",
      "Quality scoring — sections below 0.70 auto-regenerated",
      "Human review: approve, reject, edit, reorder sections",
      "Export as .docx, with clear and structued document",
    ],
    tech: [
      "FastAPI",
      "ChromaDB",
      "all-MiniLM-L6-v2",
      "Databricks LLM",
      "Port 5174",
    ],
    url: "http://localhost:5174",
    accent: "indigo",
  },
  {
    id: "ppt",
    number: "03",
    title: "AI Solution Architect Agent",
    tagline: "BRDs and docs become architecture and slides.",
    description:
      "Takes your BRDs and technical documentation as input and transforms them into architecture diagrams, structured presentations, and production-ready outputs — powered by Databricks Model Serving (Claude Sonnet). Submit via text or file upload.",
    features: [
      "Accepts BRD and technical documentation as input",
      "Text input or file upload via dedicated endpoints",
      "AI-driven architecture and slide structure generation",
      "Powered by Databricks Model Serving — Claude Sonnet",
      "Async pipeline orchestration via FastAPI",
      "Pydantic v2 validated request and response models",
      "POST /api/v1/generate and /api/v1/generate-file endpoints",
      "Health check endpoint for monitoring",
      "Export as .pptx for direct stakeholder delivery",
    ],
    tech: ["FastAPI", "Databricks Claude Sonnet", "Pydantic v2", "Port 5175"],
    url: "http://localhost:5175",
    accent: "violet",
  },
];

export default function AgentsSection() {
  return (
    <section id="agents" className="px-6 py-24 max-w-6xl mx-auto">
      <div className="max-w-2xl mb-16">
        <p className="text-xs font-semibold tracking-widest text-gray-400 uppercase mb-4">
          The Agents
        </p>
        <h2 className="text-3xl font-extrabold tracking-tight text-gray-900 mb-4">
          Three agents. Every document type covered.
        </h2>
        <p className="text-base text-gray-500 leading-relaxed">
          Each agent is independently deployed with its own FastAPI backend and
          React frontend. All LLM inference runs through Databricks Model
          Serving — no data leaves your infrastructure except the final
          generation prompt.
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {agents.map((agent) => (
          <AgentCard key={agent.id} agent={agent} />
        ))}
      </div>
    </section>
  );
}
