import { useState, useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { buildContext } from "../api/endpoints";
import Notice from "../components/ui/Notice";
import Spinner from "../components/ui/Spinner";

// ─── Step definitions (YOUR original logic, untouched) ────────────────────────
const FLAT_STEPS = [
  {
    key: "filter",
    label: "Loading filtered files",
    detail: "Reading file list from project state",
  },
  {
    key: "chunk",
    label: "Chunking source files",
    detail: "500-token chunks with 50-token overlap",
  },
  {
    key: "embed",
    label: "Embedding with all-MiniLM-L6-v2",
    detail: "Running locally on CPU — no data leaves your machine",
  },
  {
    key: "store",
    label: "Persisting to ChromaDB",
    detail: "Cosine-similarity vector store",
  },
  {
    key: "done",
    label: "Context database ready",
    detail: "All chunks indexed and searchable",
  },
];

const RAPTOR_STEPS = [
  {
    key: "filter",
    label: "Loading filtered files",
    detail: "Reading file list from project state",
  },
  {
    key: "chunk",
    label: "Chunking source files",
    detail: "500-token chunks with 50-token overlap",
  },
  {
    key: "raptor1",
    label: "RAPTOR Level 1 — File summaries",
    detail: "Per-file 3–5 sentence summaries via Groq",
  },
  {
    key: "raptor2",
    label: "RAPTOR Level 2 — Directory summaries",
    detail: "Grouping files into directory-level context",
  },
  {
    key: "raptor3",
    label: "RAPTOR Level 3 — System overview",
    detail: "Single high-level codebase summary",
  },
  {
    key: "embed",
    label: "Embedding all levels",
    detail: "Running all-MiniLM-L6-v2 locally on CPU",
  },
  {
    key: "store",
    label: "Persisting to ChromaDB",
    detail: "Multi-level cosine-similarity vector store",
  },
  {
    key: "done",
    label: "Context database ready",
    detail: "All chunks indexed and searchable",
  },
];

// ─── BuildProgress (UI-only upgrade, identical step logic) ───────────────────
function BuildProgress({ steps, currentStep, done }) {
  const pct = done ? 100 : Math.round(((currentStep + 1) / steps.length) * 100);

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden">
      {/* Progress bar header */}
      <div className="px-5 pt-4 pb-3 border-b border-gray-100">
        <div className="flex items-center justify-between mb-2">
          <div className="flex items-center gap-2">
            {done ? (
              <span
                className="w-4 h-4 rounded-full bg-green-500 flex items-center
                               justify-center flex-shrink-0"
              >
                <svg
                  width="8"
                  height="8"
                  viewBox="0 0 10 10"
                  fill="none"
                  stroke="white"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                >
                  <polyline points="1.5 5 4 7.5 8.5 2.5" />
                </svg>
              </span>
            ) : (
              <Spinner size="sm" className="text-primary" />
            )}
            <span className="text-xs font-semibold text-gray-700">
              {done ? "Build complete" : steps[currentStep]?.label + "…"}
            </span>
          </div>
          <span className="text-xs font-bold tabular-nums text-gray-400">
            {pct}%
          </span>
        </div>
        {/* Thin progress bar */}
        <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-700 ease-out"
            style={{
              width: `${pct}%`,
              backgroundColor: done
                ? "#22c55e"
                : "var(--color-primary, #01696f)",
            }}
          />
        </div>
      </div>

      {/* Step list */}
      <div className="divide-y divide-gray-50">
        {steps.map((step, idx) => {
          const isActive = idx === currentStep && !done;
          const isComplete = idx < currentStep || done;
          const isPending = idx > currentStep && !done;

          return (
            <div
              key={step.key}
              className={`flex items-center gap-3 px-5 py-3 transition-all duration-300
                ${isActive ? "bg-blue-50/60" : ""}
                ${isComplete ? "bg-green-50/40" : ""}
                ${isPending ? "opacity-35" : ""}
              `}
            >
              {/* Step dot */}
              <div
                className={`w-5 h-5 rounded-full flex items-center justify-center
                               flex-shrink-0 transition-all duration-300
                ${isActive ? "bg-primary" : ""}
                ${isComplete ? "bg-green-500" : ""}
                ${isPending ? "bg-gray-100 border border-gray-200" : ""}
              `}
              >
                {isComplete && (
                  <svg
                    width="8"
                    height="8"
                    viewBox="0 0 10 10"
                    fill="none"
                    stroke="white"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                  >
                    <polyline points="1.5 5 4 7.5 8.5 2.5" />
                  </svg>
                )}
                {isActive && (
                  <span className="w-1.5 h-1.5 rounded-full bg-white block" />
                )}
                {isPending && (
                  <span className="w-1.5 h-1.5 rounded-full bg-gray-300 block" />
                )}
              </div>

              {/* Text */}
              <div className="min-w-0 flex-1">
                <div
                  className={`text-xs font-semibold leading-tight
                  ${isActive ? "text-primary" : ""}
                  ${isComplete ? "text-green-700" : ""}
                  ${isPending ? "text-gray-400" : ""}
                `}
                >
                  {step.label}
                </div>
                {(isActive || isComplete) && (
                  <div className="text-[10px] text-gray-400 mt-0.5 leading-relaxed">
                    {step.detail}
                  </div>
                )}
              </div>

              {/* Right: step number or check */}
              <div className="flex-shrink-0">
                {isComplete ? (
                  <span className="text-[10px] font-bold text-green-400">
                    done
                  </span>
                ) : isActive ? (
                  <Spinner size="sm" className="text-primary" />
                ) : (
                  <span className="text-[10px] text-gray-200 tabular-nums">
                    {String(idx + 1).padStart(2, "0")}
                  </span>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ─── MetricStrip ──────────────────────────────────────────────────────────────
function MetricStrip({ strategy, chunks, dbSize }) {
  const metrics = [
    { label: "Strategy", value: strategy?.toUpperCase() ?? "—" },
    {
      label: "Chunks Stored",
      value: chunks != null ? Number(chunks).toLocaleString() : "—",
    },
    { label: "DB Size", value: dbSize != null ? `${dbSize} MB` : "—" },
  ];

  return (
    <div
      className="grid grid-cols-3 bg-white border border-gray-200
                    rounded-xl overflow-hidden mb-5"
    >
      {metrics.map((m, i) => (
        <div
          key={m.label}
          className={`py-4 px-4 text-center
               ${i < metrics.length - 1 ? "border-r border-gray-100" : ""}`}
        >
          <div
            className="text-lg font-bold tabular-nums text-gray-900
                          leading-none tracking-tight"
          >
            {m.value}
          </div>
          <div
            className="text-[10px] font-semibold uppercase tracking-widest
                          text-gray-400 mt-1.5"
          >
            {m.label}
          </div>
        </div>
      ))}
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function ContextPage() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  const { id: projectId } = useParams();

  // ── YOUR original derived values, untouched ──
  const analysis = state.analysis;
  const loc = analysis?.total_loc ?? 0;
  const isRaptor = loc > 50000;
  const steps = isRaptor ? RAPTOR_STEPS : FLAT_STEPS;

  // ── YOUR original state, untouched ──
  const [building, setBuilding] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [buildDone, setBuildDone] = useState(false);
  const [error, setError] = useState(null);
  const stepTimerRef = useRef(null);

  // ── YOUR original guard, untouched ──
  useEffect(() => {
    if (!projectId) navigate("/ingest");
    if (!state.confirmedSections?.length)
      navigate(`/project/${projectId}/sections`);
  }, []);

  // ── YOUR original animation logic, untouched ──
  const startStepAnimation = () => {
    let step = 0;
    const totalSteps = steps.length - 1;
    const interval = isRaptor ? 45_000 : 20_000;
    const stepDuration = Math.floor(interval / totalSteps);

    stepTimerRef.current = setInterval(() => {
      step += 1;
      if (step < totalSteps) {
        setCurrentStep(step);
      } else {
        clearInterval(stepTimerRef.current);
      }
    }, stepDuration);
  };

  // ── YOUR original handleBuild, untouched ──
  const handleBuild = async () => {
    setBuilding(true);
    setError(null);
    setCurrentStep(0);
    setBuildDone(false);
    startStepAnimation();

    try {
      const { data } = await buildContext(projectId);
      clearInterval(stepTimerRef.current);
      setCurrentStep(steps.length - 1);
      setBuildDone(true);
      dispatch({ type: "SET_CONTEXT_RESULT", payload: data });
    } catch (e) {
      clearInterval(stepTimerRef.current);
      setError(e.response?.data?.detail ?? e.message);
    } finally {
      setBuilding(false);
    }
  };

  // ── YOUR original cleanup, untouched ──
  useEffect(() => () => clearInterval(stepTimerRef.current), []);

  const result = state.contextResult;
  const alreadyDone = !!result;

  // ─────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex gap-10">
      {/* ── Left: main content ── */}
      <div className="flex-[6] min-w-0">
        {/* Page heading */}
        <div className="mb-5">
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
            Context Building
          </h1>
          <p className="text-sm text-gray-500 mt-1 leading-relaxed">
            Source files are chunked, embedded with{" "}
            <code
              className="font-mono text-xs text-gray-600 bg-gray-100
                             px-1 py-0.5 rounded"
            >
              all-MiniLM-L6-v2
            </code>{" "}
            entirely on your CPU, and stored in ChromaDB. Nothing leaves your
            machine.
          </p>
        </div>

        {/* Privacy notice */}
        <div
          className="flex items-center gap-2.5 bg-green-50 border border-green-100
                        rounded-lg px-3.5 py-2.5 mb-5"
        >
          <svg
            width="13"
            height="13"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            className="text-green-600 flex-shrink-0"
            aria-hidden="true"
          >
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
          </svg>
          <span className="text-xs font-medium text-green-700">
            Embeddings run entirely on your CPU — no code leaves your machine
          </span>
        </div>

        {/* Strategy card */}
        <div
          className={`rounded-xl border p-4 mb-5
          ${
            isRaptor
              ? "bg-amber-50 border-amber-200"
              : "bg-blue-50  border-blue-100"
          }`}
        >
          <div className="flex items-start gap-3">
            {/* Icon */}
            <div
              className={`w-8 h-8 rounded-lg flex items-center justify-center
                             flex-shrink-0 mt-0.5
              ${isRaptor ? "bg-amber-100" : "bg-blue-100"}`}
            >
              {isRaptor ? (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  className="text-amber-600"
                  aria-hidden="true"
                >
                  <path d="M12 22V12M12 12l-4-4M12 12l4-4M8 20h8M6 8l6-6 6 6" />
                </svg>
              ) : (
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  className="text-blue-600"
                  aria-hidden="true"
                >
                  <polygon points="12 2 2 7 12 12 22 7 12 2" />
                  <polyline points="2 17 12 22 22 17" />
                  <polyline points="2 12 12 17 22 12" />
                </svg>
              )}
            </div>

            <div className="flex-1 min-w-0">
              <div
                className={`text-[10px] font-bold uppercase tracking-widest mb-0.5
                ${isRaptor ? "text-amber-500" : "text-blue-400"}`}
              >
                Auto-selected Strategy
              </div>
              <div
                className={`text-sm font-bold mb-1
                ${isRaptor ? "text-amber-800" : "text-blue-800"}`}
              >
                {isRaptor
                  ? "Hierarchical 4-Level Tree"
                  : "Direct Flat Chunking"}
              </div>
              <p
                className={`text-xs leading-relaxed
                ${isRaptor ? "text-amber-600" : "text-blue-500"}`}
              >
                {isRaptor
                  ? `Codebase exceeds 50K LOC (${loc.toLocaleString()} LOC). RAPTOR builds per-file,
                     per-directory, and system-level summaries via Groq before embedding.
                     Expect 2–10 minutes.`
                  : `Under 50K LOC (${loc.toLocaleString()} LOC). Source files are chunked directly
                     and embedded locally. Usually completes in 1–3 minutes.`}
              </p>
            </div>

            {/* LOC pill */}
            <div className={`flex-shrink-0 text-right`}>
              <div
                className={`text-sm font-bold tabular-nums
                ${isRaptor ? "text-amber-700" : "text-blue-600"}`}
              >
                {loc.toLocaleString()}
              </div>
              <div
                className={`text-[10px]
                ${isRaptor ? "text-amber-400" : "text-blue-300"}`}
              >
                LOC
              </div>
            </div>
          </div>
        </div>

        {error && (
          <div
            className="flex items-start gap-2.5 bg-red-50 border border-red-200
                          rounded-lg px-3.5 py-3 mb-4 text-sm text-red-700"
          >
            <svg
              width="14"
              height="14"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              className="flex-shrink-0 mt-0.5"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
            {error}
          </div>
        )}

        {/* ── State: Already built ── */}
        {alreadyDone && !building && (
          <>
            <div
              className="flex items-center gap-2.5 bg-green-50 border
                            border-green-100 rounded-lg px-3.5 py-2.5 mb-4
                            text-xs font-medium text-green-700"
            >
              <svg
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                className="flex-shrink-0"
                aria-hidden="true"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
              Vector database already built. Rebuild only if the codebase
              changed.
            </div>

            <MetricStrip
              strategy={result.strategy}
              chunks={result.total_chunks}
              dbSize={result.vector_db_size_mb}
            />

            <div className="flex gap-3">
              <button
                onClick={() => navigate(`/project/${projectId}/generate`)}
                className="flex-1 flex items-center justify-center gap-2
                           bg-primary hover:bg-primary-hover text-white
                           text-sm font-semibold px-6 py-2.5 rounded-lg
                           shadow-sm transition-colors duration-150"
              >
                Continue to Generation
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
              <button
                onClick={() => {
                  dispatch({ type: "SET_CONTEXT_RESULT", payload: null });
                  setBuildDone(false);
                  setCurrentStep(0);
                }}
                className="px-4 py-2.5 text-sm font-medium text-gray-500
                           border border-gray-200 rounded-lg hover:bg-gray-50
                           hover:text-gray-700 transition-colors duration-150"
              >
                Rebuild
              </button>
            </div>
          </>
        )}

        {/* ── State: Building in progress ── */}
        {building && (
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <Spinner size="sm" className="text-primary" />
              <span className="text-sm font-medium text-gray-800">
                Building context database…
              </span>
            </div>
            <p className="text-xs text-gray-400 mb-4 leading-relaxed">
              {isRaptor
                ? "This may take 2–10 minutes for large codebases. Please keep this tab open."
                : "This usually takes 1–3 minutes depending on your CPU."}
            </p>
            <BuildProgress
              steps={steps}
              currentStep={currentStep}
              done={buildDone}
            />
          </div>
        )}

        {/* ── State: Just finished (buildDone=true but alreadyDone not yet synced) ── */}
        {buildDone && !alreadyDone && (
          <div>
            <BuildProgress steps={steps} currentStep={currentStep} done />
            <div className="mt-5">
              <MetricStrip
                strategy={result?.strategy}
                chunks={result?.total_chunks}
                dbSize={result?.vector_db_size_mb}
              />
              <button
                onClick={() => navigate(`/project/${projectId}/generate`)}
                className="w-full flex items-center justify-center gap-2
                           bg-primary hover:bg-primary-hover text-white
                           text-sm font-semibold px-6 py-2.5 rounded-lg
                           shadow-sm transition-colors duration-150"
              >
                Continue to Generation
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <path d="M5 12h14M12 5l7 7-7 7" />
                </svg>
              </button>
            </div>
          </div>
        )}

        {/* ── State: Not yet started ── */}
        {!alreadyDone && !building && !buildDone && (
          <div>
            <div
              className="flex items-center gap-2.5 bg-blue-50 border
                            border-blue-100 rounded-lg px-3.5 py-2.5 mb-4
                            text-xs font-medium text-blue-600"
            >
              <svg
                width="13"
                height="13"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                className="flex-shrink-0"
                aria-hidden="true"
              >
                <circle cx="12" cy="12" r="10" />
                <line x1="12" y1="8" x2="12" y2="8" />
                <line x1="12" y1="12" x2="12" y2="16" />
              </svg>
              {isRaptor
                ? "Large codebase detected. RAPTOR will build a 4-level summary hierarchy — keep this tab open during the build."
                : "Runs entirely on your machine. Expect 1–3 minutes depending on CPU speed."}
            </div>
            <button
              onClick={handleBuild}
              className="w-full flex items-center justify-center gap-2
                         bg-primary hover:bg-primary-hover active:bg-primary-active
                         text-white text-sm font-semibold
                         px-6 py-2.5 rounded-lg shadow-sm
                         transition-colors duration-150"
            >
              <svg
                width="14"
                height="14"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.2"
                strokeLinecap="round"
                aria-hidden="true"
              >
                <ellipse cx="12" cy="5" rx="9" ry="3" />
                <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
              </svg>
              Build Context Database
            </button>
          </div>
        )}
      </div>

      {/* ── Right: sidebar ── */}
      <div className="flex-[4] min-w-0 hidden md:block">
        <div className="h-[60px]" />

        {/* Sections queued */}
        {state.confirmedSections?.length > 0 && (
          <>
            <div className="flex items-center gap-2 mb-3">
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                Sections Queued
              </p>
              <span
                className="text-[10px] font-semibold text-primary
                               bg-primary/10 px-1.5 py-0.5 rounded-full"
              >
                {state.confirmedSections.length}
              </span>
              <div className="flex-1 h-px bg-gray-100" />
            </div>

            <div
              className="bg-white border border-gray-200 rounded-xl
                            overflow-hidden divide-y divide-gray-50 mb-5"
            >
              {state.confirmedSections.map((name, i) => (
                <div
                  key={name}
                  className="flex items-center gap-3 px-3.5 py-2.5
                                hover:bg-gray-50 transition-colors duration-100"
                >
                  <span
                    className="text-[10px] font-bold tabular-nums
                                   text-gray-300 w-5 flex-shrink-0 text-right"
                  >
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span
                    className="text-xs text-gray-700 font-medium
                                   leading-snug min-w-0 truncate"
                  >
                    {name}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* What happens explainer */}
        <div className="flex items-center gap-2 mb-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
            What Happens
          </p>
          <div className="flex-1 h-px bg-gray-100" />
        </div>

        <div
          className="bg-white border border-gray-200 rounded-xl
                        overflow-hidden divide-y divide-gray-50"
        >
          {[
            {
              icon: (
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <path d="M6 2h9l5 5v15H6V2z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="8" y1="13" x2="16" y2="13" />
                  <line x1="8" y1="17" x2="16" y2="17" />
                </svg>
              ),
              title: "Chunking",
              body: "Each source file split into 500-token overlapping chunks using tiktoken cl100k_base.",
            },
            {
              icon: (
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <circle cx="12" cy="12" r="3" />
                  <path
                    d="M12 1v4M12 19v4M4.22 4.22l2.83 2.83M16.95 16.95l2.83 2.83
                           M1 12h4M19 12h4M4.22 19.78l2.83-2.83M16.95 7.05l2.83-2.83"
                  />
                </svg>
              ),
              title: "Embedding",
              body: "all-MiniLM-L6-v2 (80 MB, CPU) runs in batches of 64 — no GPU required.",
            },
            {
              icon: (
                <svg
                  width="13"
                  height="13"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <ellipse cx="12" cy="5" rx="9" ry="3" />
                  <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
                  <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
                </svg>
              ),
              title: "Storage",
              body: "L2-normalised vectors stored in ChromaDB with file path and line number metadata.",
            },
            ...(isRaptor
              ? [
                  {
                    icon: (
                      <svg
                        width="13"
                        height="13"
                        viewBox="0 0 24 24"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        aria-hidden="true"
                      >
                        <path d="M12 22V12M12 12L8 8M12 12l4-4M6 20h12M4 8l8-8 8 8" />
                      </svg>
                    ),
                    title: "RAPTOR",
                    body: "Multi-level summaries (file → directory → system) built via Groq for large codebases.",
                  },
                ]
              : []),
          ].map((item, i, arr) => (
            <div key={item.title} className="flex gap-3 px-4 py-3.5">
              <span className="text-gray-400 flex-shrink-0 mt-0.5">
                {item.icon}
              </span>
              <div>
                <div className="text-xs font-semibold text-gray-700 mb-0.5">
                  {item.title}
                </div>
                <div className="text-[11px] text-gray-400 leading-relaxed">
                  {item.body}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
