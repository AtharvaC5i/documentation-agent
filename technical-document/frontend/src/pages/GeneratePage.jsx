import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { startGeneration } from "../api/endpoints";
import { useGenerationPoller } from "../hooks/useGenerationPoller";
import Spinner from "../components/ui/Spinner";

// ── YOUR original normaliseStatus, untouched ──────────────────────────────────
function normaliseStatus(raw) {
  if (!raw) return "pending";
  const s = raw.toLowerCase().replace(/[_-]/g, "");
  if (s === "success" || s === "completed" || s === "done") return "success";
  if (s === "lowquality" || s === "low_quality" || s === "low")
    return "lowquality";
  if (s === "failed" || s === "error") return "failed";
  if (s === "inprogress" || s === "generating" || s === "running")
    return "inprogress";
  return "pending";
}

// ─── QualityBar (YOUR logic, reskinned) ───────────────────────────────────────
function QualityBar({ score }) {
  if (score === null || score === undefined) return null;
  const pct = Math.round(score * 100);
  const barColor =
    score >= 0.7
      ? "bg-green-500"
      : score >= 0.5
        ? "bg-amber-400"
        : "bg-red-500";
  const textColor =
    score >= 0.7
      ? "text-green-600"
      : score >= 0.5
        ? "text-amber-600"
        : "text-red-600";
  return (
    <div className="flex items-center gap-2.5 mt-2">
      <div className="flex-1 h-1 bg-gray-100 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${barColor}`}
          style={{ width: `${pct}%` }}
        />
      </div>
      <span
        className={`text-[10px] font-bold tabular-nums w-6 text-right ${textColor}`}
      >
        {pct}
      </span>
    </div>
  );
}

// ─── SectionStatusCard (YOUR logic, reskinned) ────────────────────────────────
function SectionStatusCard({ name, sectionData, isInProgress }) {
  const rawStatus = sectionData?.status ?? "pending";
  const status = isInProgress ? "inprogress" : normaliseStatus(rawStatus);
  const score = sectionData?.quality_score ?? sectionData?.qualityScore ?? null;
  const regen = sectionData?.regenerated ?? false;

  const cfg = {
    pending: {
      dot: "bg-gray-300",
      bg: "bg-white",
      border: "border-gray-200",
      label: "Pending",
      labelCls: "bg-gray-100 text-gray-500 border-gray-200",
    },
    inprogress: {
      dot: "bg-blue-500",
      bg: "bg-blue-50",
      border: "border-blue-200",
      label: "Generating",
      labelCls: "bg-blue-100 text-blue-700 border-blue-200",
    },
    success: {
      dot: "bg-green-500",
      bg: "bg-green-50/60",
      border: "border-green-200",
      label: "Done",
      labelCls: "bg-green-100 text-green-700 border-green-200",
    },
    lowquality: {
      dot: "bg-amber-400",
      bg: "bg-amber-50/60",
      border: "border-amber-200",
      label: "Low Quality",
      labelCls: "bg-amber-100 text-amber-700 border-amber-200",
    },
    failed: {
      dot: "bg-red-500",
      bg: "bg-red-50/60",
      border: "border-red-200",
      label: "Failed",
      labelCls: "bg-red-100 text-red-700 border-red-200",
    },
  }[status] ?? {
    dot: "bg-gray-300",
    bg: "bg-white",
    border: "border-gray-200",
    label: "Pending",
    labelCls: "bg-gray-100 text-gray-500 border-gray-200",
  };

  return (
    <div
      className={`flex flex-col px-4 py-3 rounded-xl border transition-all
                  duration-300 ${cfg.bg} ${cfg.border}`}
    >
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0 flex-1">
          <span
            className={`w-2 h-2 rounded-full flex-shrink-0 ${cfg.dot}
                        ${status === "inprogress" ? "animate-pulse" : ""}`}
          />
          <span className="text-sm font-medium text-gray-800 truncate">
            {name}
          </span>
        </div>
        <div className="flex items-center gap-2 flex-shrink-0">
          {regen && (
            <span
              className="text-[10px] font-semibold text-gray-400
                             bg-white border border-gray-200 px-1.5 py-0.5 rounded-full"
            >
              retried
            </span>
          )}
          {status === "inprogress" ? (
            <div className="flex items-center gap-1.5">
              <Spinner size="sm" className="text-blue-500" />
              <span
                className={`text-[10px] font-bold uppercase tracking-wide
                               px-2 py-0.5 rounded-full border ${cfg.labelCls}`}
              >
                {cfg.label}
              </span>
            </div>
          ) : (
            <span
              className={`text-[10px] font-bold uppercase tracking-wide
                             px-2 py-0.5 rounded-full border ${cfg.labelCls}`}
            >
              {status === "success" && score !== null
                ? `${Math.round(score * 100)}`
                : cfg.label}
            </span>
          )}
        </div>
      </div>
      {(status === "success" || status === "lowquality") && score !== null && (
        <QualityBar score={score} />
      )}
      {status === "lowquality" && (
        <p className="text-[11px] text-amber-600 mt-1.5 leading-relaxed">
          Score below 0.7 after one retry — you can regenerate this in Review.
        </p>
      )}
      {status === "failed" && (
        <p className="text-[11px] text-red-600 mt-1.5 leading-relaxed">
          Generation failed. Retry this section in the Review step.
        </p>
      )}
    </div>
  );
}

// ─── OverallProgress (YOUR logic, reskinned) ──────────────────────────────────
function OverallProgress({ completed, total, finished }) {
  const pct = total > 0 ? Math.round((completed / total) * 100) : 0;
  return (
    <div className="bg-white border border-gray-200 rounded-xl p-5 mb-5 shadow-sm">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          {finished ? (
            <span
              className="w-5 h-5 rounded-full bg-green-500 flex items-center
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
            <span className="w-2 h-2 rounded-full bg-primary animate-pulse" />
          )}
          <span className="text-sm font-semibold text-gray-900">
            {finished ? "Generation complete" : "Generating sections…"}
          </span>
        </div>
        <span className="text-sm font-bold tabular-nums text-gray-700">
          {completed} <span className="text-gray-300 font-normal">/</span>{" "}
          {total}
        </span>
      </div>
      <div className="flex gap-0.5 h-2 rounded-full overflow-hidden mb-2">
        {Array.from({ length: total }).map((_, i) => (
          <div
            key={i}
            className={`flex-1 transition-all duration-500
            ${i < completed ? "bg-primary" : "bg-gray-100"}`}
          />
        ))}
      </div>
      <div className="flex justify-between items-center text-xs text-gray-400">
        <span className="tabular-nums">{pct}% complete</span>
        {!finished && (
          <span className="flex items-center gap-1.5 text-primary font-medium">
            <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
            Live
          </span>
        )}
      </div>
    </div>
  );
}

// ─── QualitySummary (YOUR logic, reskinned) ───────────────────────────────────
function QualitySummary({ sections }) {
  if (!sections?.length) return null;
  const withScore = sections.filter((s) => s.quality_score != null);
  const avg = withScore.length
    ? withScore.reduce((a, s) => a + s.quality_score, 0) / withScore.length
    : 0;
  const norm = sections.map((s) => ({ ...s, _s: normaliseStatus(s.status) }));
  const green = norm.filter((s) => s._s === "success").length;
  const low = norm.filter((s) => s._s === "lowquality").length;
  const failed = norm.filter((s) => s._s === "failed").length;
  const regenerated = sections.filter((s) => s.regenerated).length;
  const metrics = [
    {
      label: "Avg Quality",
      value: Math.round(avg * 100),
      sub: "out of 100",
      color:
        avg >= 0.7
          ? "text-green-600"
          : avg >= 0.5
            ? "text-amber-600"
            : "text-red-600",
    },
    {
      label: "High Quality",
      value: green,
      sub: "≥ 0.7 score",
      color: "text-green-600",
    },
    {
      label: "Low / Failed",
      value: low + failed,
      sub: "needs review",
      color: low + failed > 0 ? "text-amber-600" : "text-gray-900",
    },
    {
      label: "Auto-retried",
      value: regenerated,
      sub: "sections",
      color: "text-gray-900",
    },
  ];
  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-5">
      {metrics.map((m) => (
        <div
          key={m.label}
          className="bg-white border border-gray-200 rounded-xl py-4 px-4 text-center shadow-sm"
        >
          <div
            className={`text-xl font-bold tabular-nums leading-none tracking-tight ${m.color}`}
          >
            {m.value}
          </div>
          <div className="text-[11px] font-semibold text-gray-700 mt-1.5 leading-none">
            {m.label}
          </div>
          <div className="text-[10px] text-gray-400 mt-0.5">{m.sub}</div>
        </div>
      ))}
    </div>
  );
}

// ─── ReadyState — fully redesigned, YOUR logic untouched ─────────────────────
function ReadyState({ total, onStart, loading }) {
  const minMins = Math.ceil((total * 15) / 60);
  const maxMins = Math.ceil((total * 30) / 60);

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden mb-6 shadow-sm">
      {/* Top strip */}
      <div className="border-b border-gray-100 px-6 py-4 flex items-center justify-between">
        <div>
          <p className="text-sm font-semibold text-gray-900">
            {total} section{total !== 1 ? "s" : ""} queued
          </p>
          <p className="text-xs text-gray-400 mt-0.5">
            Ready to begin RAG-based generation
          </p>
        </div>

        {/* Status pill */}
        <span
          className="inline-flex items-center gap-1.5 text-[10px] font-bold
                         uppercase tracking-widest text-amber-700
                         bg-amber-50 border border-amber-200
                         px-3 py-1 rounded-full"
        >
          <span className="w-1.5 h-1.5 rounded-full bg-amber-400" />
          Awaiting Start
        </span>
      </div>

      {/* Body */}
      <div className="px-6 py-5">
        {/* Process steps */}
        <div className="grid grid-cols-3 gap-3 mb-5">
          {[
            {
              step: "01",
              label: "Vector Retrieval",
              desc: "Most relevant code chunks fetched from your store",
            },
            {
              step: "02",
              label: "RAG Generation",
              desc: "Each section written using retrieved context",
            },
            {
              step: "03",
              label: "Quality Check",
              desc: "Sections below 0.7 score are auto-retried once",
            },
          ].map((item) => (
            <div
              key={item.step}
              className="bg-gray-50 border border-gray-100 rounded-lg px-3.5 py-3"
            >
              <span
                className="text-[10px] font-bold text-primary/60 font-mono
                               uppercase tracking-widest"
              >
                {item.step}
              </span>
              <p className="text-xs font-semibold text-gray-800 mt-1 mb-0.5">
                {item.label}
              </p>
              <p className="text-[11px] text-gray-400 leading-relaxed">
                {item.desc}
              </p>
            </div>
          ))}
        </div>

        {/* Meta row: estimate + section count */}
        <div className="flex items-center gap-3 mb-5">
          <div
            className="flex items-center gap-1.5 text-xs text-gray-500
                          bg-gray-50 border border-gray-100 rounded-lg px-3 py-2"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <circle cx="12" cy="12" r="10" />
              <polyline points="12 6 12 12 16 14" />
            </svg>
            <span className="font-medium">
              ~{minMins}–{maxMins} min estimated
            </span>
          </div>
          <div
            className="flex items-center gap-1.5 text-xs text-gray-500
                          bg-gray-50 border border-gray-100 rounded-lg px-3 py-2"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <path
                d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12
                       a2 2 0 0 0 2-2V8z"
              />
              <polyline points="14 2 14 8 20 8" />
            </svg>
            <span className="font-medium">
              {total} section{total !== 1 ? "s" : ""}
            </span>
          </div>
          <div
            className="flex items-center gap-1.5 text-xs text-gray-500
                          bg-gray-50 border border-gray-100 rounded-lg px-3 py-2"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <polyline points="22 12 18 12 15 21 9 3 6 12 2 12" />
            </svg>
            <span className="font-medium">Auto-retry on low quality</span>
          </div>
        </div>

        {/* Divider */}
        <div className="h-px bg-gray-100 mb-5" />

        {/* CTA row */}
        <div className="flex items-center justify-between">
          <p className="text-xs text-gray-400 max-w-xs leading-relaxed">
            Generation runs server-side. You can monitor progress in real time
            below once started.
          </p>

          <button
            onClick={onStart}
            disabled={loading}
            className="flex items-center gap-2.5 bg-primary hover:bg-primary-hover
                       active:bg-primary-active text-white text-sm font-semibold
                       px-7 py-2.5 rounded-lg transition-colors shadow-sm
                       disabled:opacity-50 disabled:cursor-not-allowed flex-shrink-0 ml-6"
          >
            {loading ? (
              <>
                <Spinner size="sm" className="text-white" />
                Starting…
              </>
            ) : (
              <>
                <svg
                  width="14"
                  height="14"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2.5"
                  strokeLinecap="round"
                  aria-hidden="true"
                >
                  <path d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
                Begin Generation
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}

// ─── Main Page ────────────────────────────────────────────────────────────────
export default function GeneratePage() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  const { id: projectId } = useParams();

  // ── YOUR original state, untouched ──
  const [starting, setStarting] = useState(false);
  const [startError, setStartError] = useState(null);
  const [pollingEnabled, setPollingEnabled] = useState(
    state.generationStarted && !state.generationFinished,
  );

  // ── YOUR original console.logs, untouched ──
  console.log(
    "generationResults:",
    JSON.stringify(state.generationResults, null, 2),
  );
  console.log("generationFinished:", state.generationFinished);

  // ── YOUR original status-fix effect, untouched ──
  useEffect(() => {
    if (state.generationResults.length && state.generationFinished) {
      const needsFix = state.generationResults.some(
        (s) =>
          !["success", "lowquality", "failed", "pending"].includes(s.status),
      );
      if (needsFix) {
        const fixed = state.generationResults.map((s) => ({
          ...s,
          status: ["success", "lowquality", "failed", "pending"].includes(
            s.status,
          )
            ? s.status
            : "success",
        }));
        dispatch({
          type: "SET_GENERATION_FINISHED",
          payload: { results: fixed },
        });
      }
    }
  }, []);

  // ── YOUR original guard effect, untouched ──
  useEffect(() => {
    if (!projectId) {
      navigate("/ingest");
      return;
    }
    if (!state.confirmedSections.length) {
      navigate(`/project/${projectId}/sections`);
      return;
    }
    if (!state.contextResult) {
      navigate(`/project/${projectId}/context`);
      return;
    }
  }, []);

  // ── YOUR original poller, untouched ──
  const {
    status,
    results,
    error: pollError,
  } = useGenerationPoller(projectId, pollingEnabled);

  // ── YOUR original results effect, untouched ──
  useEffect(() => {
    if (results && !state.generationFinished) {
      dispatch({ type: "SET_GENERATION_FINISHED", payload: { results } });
      setPollingEnabled(false);
    }
  }, [results]);

  // ── YOUR original handleStart, untouched ──
  const handleStart = async () => {
    setStarting(true);
    setStartError(null);
    try {
      await startGeneration(projectId);
      dispatch({ type: "SET_GENERATION_STARTED" });
      setPollingEnabled(true);
    } catch (e) {
      setStartError(e.message);
    } finally {
      setStarting(false);
    }
  };

  // ── YOUR original derived values, untouched ──
  const sections = state.confirmedSections;
  const total = sections.length;
  const statusSections = status?.sections ?? {};
  const inProgressName = status?.in_progress ?? null;
  const completedCount = status?.completed ?? 0;
  const finished = state.generationFinished;
  const finishedResults = state.generationResults ?? [];
  const isStarted = state.generationStarted || pollingEnabled;

  // ── YOUR original liveDisplayList, untouched ──
  const liveDisplayList = sections.map((name) => ({
    name,
    data: statusSections[name] ?? null,
    isInProgress: name === inProgressName,
  }));

  // ──────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex gap-10">
      {/* ── Left: main content ── */}
      <div className="flex-[6] min-w-0">
        {/* Page heading */}
        <div className="mb-5">
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
            Section Generation
          </h1>
          <p className="text-sm text-gray-500 mt-1 leading-relaxed">
            Each section is written via RAG using the most relevant code chunks
            from your vector store. Sections below{" "}
            <span className="font-medium text-gray-700">0.7</span> quality are
            automatically regenerated once.
          </p>
        </div>

        {/* Errors */}
        {startError && (
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
            {startError}
          </div>
        )}
        {pollError && (
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
            {pollError}
          </div>
        )}

        {/* Not started */}
        {!isStarted && !finished && (
          <ReadyState total={total} onStart={handleStart} loading={starting} />
        )}

        {/* In progress or finished — YOUR original condition, untouched */}
        {(isStarted || finished) && (
          <>
            <OverallProgress
              completed={finished ? total : completedCount}
              total={total}
              finished={finished}
            />

            {finished && <QualitySummary sections={finishedResults} />}

            {finished && (
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
                Generation complete —{" "}
                {finishedResults.filter((s) => s.status === "success").length}{" "}
                of {total} sections generated successfully.
              </div>
            )}

            {/* Section label */}
            <div className="flex items-center gap-2 mb-3">
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                Section Progress
              </p>
              <div className="flex-1 h-px bg-gray-100" />
            </div>

            {/* Section cards — YOUR original conditional render, untouched */}
            <div className="flex flex-col gap-2 mb-6">
              {finished
                ? [...finishedResults]
                    .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
                    .map((s) => (
                      <SectionStatusCard
                        key={s.name}
                        name={s.name}
                        sectionData={s}
                        isInProgress={false}
                      />
                    ))
                : liveDisplayList.map(({ name, data, isInProgress }) => (
                    <SectionStatusCard
                      key={name}
                      name={name}
                      sectionData={data}
                      isInProgress={isInProgress}
                    />
                  ))}
            </div>

            {/* Continue button */}
            {finished && (
              <button
                onClick={() => navigate(`/project/${projectId}/review`)}
                className="w-full flex items-center justify-center gap-2
                           bg-primary hover:bg-primary-hover text-white
                           text-sm font-semibold px-6 py-2.5 rounded-lg
                           transition-colors shadow-sm"
              >
                Continue to Review
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
            )}

            {/* Live polling indicator */}
            {!finished && pollingEnabled && (
              <div
                className="flex items-center justify-center gap-2
                              text-xs text-gray-400 py-4"
              >
                <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse" />
                Updating every 3 seconds
              </div>
            )}
          </>
        )}
      </div>

      {/* ── Right: sidebar ── */}
      <div className="flex-[4] min-w-0 hidden md:block">
        <div className="h-[60px]" />

        {/* Quality bands */}
        <div className="flex items-center gap-2 mb-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
            Quality Bands
          </p>
          <div className="flex-1 h-px bg-gray-100" />
        </div>
        <div
          className="bg-white border border-gray-200 rounded-xl
                        overflow-hidden divide-y divide-gray-50 mb-5 shadow-sm"
        >
          {[
            {
              dot: "bg-green-500",
              range: "≥ 0.70",
              label: "High Quality",
              desc: "Length, structure, and keyword relevance all strong.",
            },
            {
              dot: "bg-amber-400",
              range: "0.50–0.69",
              label: "Low Quality",
              desc: "Auto-retried once. May need manual review.",
            },
            {
              dot: "bg-red-500",
              range: "< 0.50",
              label: "Poor",
              desc: "Failed threshold after retry. Regenerate in Review.",
            },
          ].map((item) => (
            <div
              key={item.label}
              className="flex items-start gap-3 px-4 py-3.5"
            >
              <span
                className={`w-2 h-2 rounded-full flex-shrink-0 mt-1 ${item.dot}`}
              />
              <div>
                <div className="flex items-center gap-2 mb-0.5">
                  <span className="text-xs font-semibold text-gray-800">
                    {item.label}
                  </span>
                  <span className="text-[10px] font-mono text-gray-300">
                    {item.range}
                  </span>
                </div>
                <p className="text-[11px] text-gray-400 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            </div>
          ))}
        </div>

        {/* Scoring weights */}
        <div className="flex items-center gap-2 mb-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
            Scoring Weights
          </p>
          <div className="flex-1 h-px bg-gray-100" />
        </div>
        <div
          className="bg-white border border-gray-200 rounded-xl
                        overflow-hidden divide-y divide-gray-50 mb-5 shadow-sm"
        >
          {[
            {
              component: "Length",
              weight: "0.40",
              detail: "≥ 300 words = full score",
            },
            {
              component: "Structure",
              weight: "0.30",
              detail: "Headers, bullets, code blocks",
            },
            {
              component: "Keyword Relevance",
              weight: "0.30",
              detail: "Section name words in content",
            },
          ].map((row) => (
            <div
              key={row.component}
              className="flex items-center justify-between px-4 py-3"
            >
              <div>
                <div className="text-xs font-semibold text-gray-800">
                  {row.component}
                </div>
                <div className="text-[11px] text-gray-400">{row.detail}</div>
              </div>
              <span className="text-xs font-bold text-primary tabular-nums ml-4">
                {row.weight}
              </span>
            </div>
          ))}
        </div>

        {/* Live stats — YOUR original condition, untouched */}
        {isStarted && !finished && status && (
          <>
            <div className="flex items-center gap-2 mb-3">
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                Live Stats
              </p>
              <div className="flex-1 h-px bg-gray-100" />
            </div>
            <div className="grid grid-cols-2 gap-2 mb-4">
              <div
                className="bg-white border border-gray-200 rounded-xl
                              py-4 px-4 text-center shadow-sm"
              >
                <div className="text-xl font-bold tabular-nums text-gray-900 leading-none">
                  {completedCount}
                </div>
                <div
                  className="text-[10px] font-semibold uppercase tracking-widest
                                text-gray-400 mt-1.5"
                >
                  Completed
                </div>
                <div className="text-[10px] text-gray-300 mt-0.5">
                  of {total}
                </div>
              </div>
              <div
                className="bg-white border border-gray-200 rounded-xl
                              py-4 px-4 text-center shadow-sm"
              >
                <div className="text-xl font-bold tabular-nums text-gray-900 leading-none">
                  {inProgressName ? "1" : "0"}
                </div>
                <div
                  className="text-[10px] font-semibold uppercase tracking-widest
                                text-gray-400 mt-1.5"
                >
                  In Progress
                </div>
                <div className="text-[10px] text-gray-300 mt-0.5">section</div>
              </div>
            </div>
          </>
        )}

        {/* Estimated time — YOUR original condition, untouched */}
        {!finished && isStarted && (
          <div className="bg-gray-50 border border-gray-200 rounded-xl p-4 shadow-sm">
            <div
              className="text-[10px] font-bold uppercase tracking-widest
                            text-gray-400 mb-1"
            >
              Estimated Time
            </div>
            <div className="text-sm font-bold text-gray-900">
              ~{Math.ceil((total * 15) / 60)}–{Math.ceil((total * 30) / 60)} min
            </div>
            <p className="text-[11px] text-gray-400 mt-1 leading-relaxed">
              ~15–30s per section via your configured LLM
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
