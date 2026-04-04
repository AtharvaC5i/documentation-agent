import { useState, useEffect } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useApp } from "../context/AppContext";
import { getReport, getPublishStatus } from "../api/endpoints";
import Spinner from "../components/ui/Spinner";

// ── deriveStatus ──────────────────────────────────────────────────────────────
function deriveStatus(backendStatus, reviewDecisions, sectionName) {
  const decision = reviewDecisions?.[sectionName]?.action;
  if (decision === "approve") return "approved";
  if (decision === "reject") return "rejected";
  const raw = String(backendStatus ?? "").toLowerCase();
  if (["approve", "approved"].includes(raw)) return "approved";
  if (["reject", "rejected"].includes(raw)) return "rejected";
  return "pending";
}

// ── QualityCell ───────────────────────────────────────────────────────────────
function QualityCell({ score }) {
  if (score === null || score === undefined)
    return <span className="text-xs text-gray-300">—</span>;
  const pct = Math.round(score * 100);
  const cls =
    score >= 0.7
      ? "bg-green-100 text-green-700 border-green-200"
      : score >= 0.5
        ? "bg-amber-100 text-amber-700 border-amber-200"
        : "bg-red-100 text-red-700 border-red-200";
  return (
    <span
      className={`inline-flex items-center px-1.5 py-0.5 rounded-full
                      text-[10px] font-bold border tabular-nums ${cls}`}
    >
      {pct}
    </span>
  );
}

// ── StatusCell ────────────────────────────────────────────────────────────────
function StatusCell({ status }) {
  const map = {
    approved: "bg-green-100 text-green-700 border-green-200",
    rejected: "bg-red-100   text-red-700   border-red-200",
    pending: "bg-gray-100  text-gray-500  border-gray-200",
  };
  const labels = {
    approved: "Approved",
    rejected: "Rejected",
    pending: "Pending",
  };
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full
                      text-[10px] font-bold uppercase tracking-wide border
                      ${map[status] ?? map.pending}`}
    >
      {labels[status] ?? "Pending"}
    </span>
  );
}

// ── QualityBands ──────────────────────────────────────────────────────────────
function QualityBands({ sections }) {
  const green = sections.filter((s) => (s.quality_score ?? 0) >= 0.7).length;
  const amber = sections.filter((s) => {
    const sc = s.quality_score ?? 0;
    return sc >= 0.5 && sc < 0.7;
  }).length;
  const red = sections.filter((s) => (s.quality_score ?? 0) < 0.5).length;
  const total = sections.length;

  return (
    <div className="grid grid-cols-3 gap-3 mb-5">
      {[
        {
          label: "High Quality",
          range: "≥ 0.70",
          count: green,
          outer: "bg-green-50 border-green-200",
          dot: "bg-green-500",
          value: "text-green-700",
          bar: "bg-green-500",
        },
        {
          label: "Low Quality",
          range: "0.50–0.69",
          count: amber,
          outer: "bg-amber-50 border-amber-200",
          dot: "bg-amber-400",
          value: "text-amber-700",
          bar: "bg-amber-400",
        },
        {
          label: "Poor",
          range: "< 0.50",
          count: red,
          outer: "bg-red-50 border-red-200",
          dot: "bg-red-500",
          value: "text-red-700",
          bar: "bg-red-500",
        },
      ].map((b) => (
        <div key={b.label} className={`${b.outer} border rounded-xl px-4 py-4`}>
          <div className="flex items-center gap-2 mb-2.5">
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${b.dot}`} />
            <span className="text-xs font-semibold text-gray-700">
              {b.label}
            </span>
          </div>
          <div
            className={`text-2xl font-bold tabular-nums tracking-tight
                           leading-none mb-2 ${b.value}`}
          >
            {b.count}
          </div>
          <div className="w-full h-1 bg-white/70 rounded-full overflow-hidden mb-1.5">
            <div
              className={`h-full rounded-full ${b.bar} transition-all duration-700`}
              style={{
                width:
                  total > 0 ? `${Math.round((b.count / total) * 100)}%` : "0%",
              }}
            />
          </div>
          <div className="text-[10px] font-mono text-gray-400">{b.range}</div>
        </div>
      ))}
    </div>
  );
}

// ── SectionTable ──────────────────────────────────────────────────────────────
function SectionTable({ sections, reviewDecisions }) {
  const headers = [
    "#",
    "Section",
    "Words",
    "Quality",
    "Status",
    "Retried",
    "Edited",
    "Reviewer Note",
  ];
  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      <div className="overflow-x-auto">
        <table className="w-full text-xs border-collapse">
          <thead>
            <tr className="bg-gray-50 border-b border-gray-100">
              {headers.map((h) => (
                <th
                  key={h}
                  className={`px-4 py-3 text-[10px] font-bold uppercase
                                tracking-widest text-gray-400 whitespace-nowrap
                                ${
                                  h === "#"
                                    ? "text-left w-8"
                                    : h === "Section" || h === "Reviewer Note"
                                      ? "text-left"
                                      : "text-center"
                                }`}
                >
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {sections.map((s, i) => {
              const status = deriveStatus(
                s.review_status,
                reviewDecisions,
                s.name,
              );
              const reviewNote =
                reviewDecisions?.[s.name]?.note ?? s.reviewer_note ?? null;
              const wasEdited =
                !!reviewDecisions?.[s.name]?.editedContent || s.was_edited;
              return (
                <tr
                  key={s.name}
                  className={`border-b border-gray-50 last:border-0
                                hover:bg-gray-50/60 transition-colors
                                ${i % 2 === 0 ? "bg-white" : "bg-gray-50/30"}`}
                >
                  <td className="px-4 py-3 text-gray-300 tabular-nums font-bold">
                    {i + 1}
                  </td>
                  <td className="px-4 py-3 max-w-[200px]">
                    <span className="block truncate text-xs font-semibold text-gray-800">
                      {s.name}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-center tabular-nums text-gray-500">
                    {s.word_count?.toLocaleString() ?? "—"}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <QualityCell score={s.quality_score} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    <StatusCell status={status} />
                  </td>
                  <td className="px-4 py-3 text-center">
                    {s.regenerated ? (
                      <span className="text-[10px] font-bold text-amber-600">
                        Yes
                      </span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-center">
                    {wasEdited ? (
                      <span className="text-[10px] font-bold text-primary">
                        Yes
                      </span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-gray-500 max-w-[180px]">
                    {reviewNote ? (
                      <span className="italic text-xs truncate block">
                        {reviewNote}
                      </span>
                    ) : (
                      <span className="text-gray-300">—</span>
                    )}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// ── PublishStatusCard ─────────────────────────────────────────────────────────
function PublishStatusCard({ projectId }) {
  const [pub, setPub] = useState(null);
  useEffect(() => {
    getPublishStatus(projectId)
      .then(({ data }) => setPub(data))
      .catch(() => {});
  }, [projectId]);

  if (!pub?.published) return null;

  return (
    <div className="bg-green-50 border border-green-200 rounded-xl p-4 mb-5">
      <div className="flex items-center gap-2 mb-3">
        <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
        <span className="text-[10px] font-bold uppercase tracking-widest text-green-700">
          Published
        </span>
      </div>
      <div className="flex flex-col gap-1.5">
        {pub.recipients?.length > 0 && (
          <div className="text-xs text-gray-600">
            <span className="font-semibold text-gray-800">Recipients: </span>
            {pub.recipients.join(", ")}
          </div>
        )}
        {pub.sent_at && (
          <div className="text-xs text-gray-600">
            <span className="font-semibold text-gray-800">Sent at: </span>
            {new Date(pub.sent_at).toLocaleString()}
          </div>
        )}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ReportPage() {
  const { state, resetProject } = useApp(); // ← resetProject pulled here
  const navigate = useNavigate();
  const { id: projectId } = useParams();

  const [loading, setLoading] = useState(false);
  const [report, setReport] = useState(null);
  const [error, setError] = useState(null);

  // Navigation guards
  useEffect(() => {
    if (!projectId) {
      navigate("/ingest");
      return;
    }
    if (!state.assemblyResult) {
      navigate(`/project/${projectId}/assembly`);
      return;
    }
  }, []);

  // Auto-generate report on mount
  useEffect(() => {
    if (!projectId || !state.assemblyResult) return;
    const generate = async () => {
      setLoading(true);
      setError(null);
      try {
        const { data } = await getReport(projectId, state.metadata);
        setReport(data);
      } catch (e) {
        setError(e.message);
      } finally {
        setLoading(false);
      }
    };
    generate();
  }, [projectId]);

  // Regenerate handler
  const handleGenerateReport = async () => {
    setLoading(true);
    setError(null);
    try {
      const { data } = await getReport(projectId, state.metadata);
      setReport(data);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  };

  // ── Start new project handler ─────────────────────────────────────────────
  const handleStartNew = () => {
    resetProject(); // wipes all context state back to initialState
    navigate("/ingest"); // then navigates — guards see blank state, don't redirect
  };

  // Enrichment + derivations
  const rawSections = report?.sections ?? [];
  const sections = rawSections.map((s) => ({
    ...s,
    word_count:
      s.word_count ??
      state.generationResults
        .find((r) => r.name === s.name)
        ?.content?.split(/\s+/).length ??
      0,
  }));

  const avgScore = sections.length
    ? sections.reduce((a, s) => a + (s.quality_score ?? 0), 0) / sections.length
    : 0;
  const approved = sections.filter(
    (s) =>
      deriveStatus(s.review_status, state.reviewDecisions, s.name) ===
      "approved",
  ).length;
  const totalWords = sections.reduce((a, s) => a + (s.word_count ?? 0), 0);

  // ──────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex gap-10">
      {/* ── Left: main content ── */}
      <div className="flex-[7] min-w-0">
        <div className="mb-5">
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
            Run Report
          </h1>
          <p className="text-sm text-gray-500 mt-1 leading-relaxed">
            A full audit trail of this documentation run — section quality
            scores, review decisions, edits, and reviewer notes.
          </p>
        </div>

        {/* Error */}
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

        {/* Loading */}
        {loading && (
          <div
            className="flex flex-col items-center justify-center gap-3
                          py-20 text-sm text-gray-400"
          >
            <Spinner size="md" className="text-primary" />
            <span>Compiling report…</span>
          </div>
        )}

        {/* Report ready */}
        {report && !loading && (
          <>
            {/* Success notice */}
            <div
              className="flex items-center gap-2.5 bg-green-50 border border-green-100
                            rounded-lg px-3.5 py-2.5 mb-5 text-xs font-medium text-green-700"
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
              Report generated for {sections.length} section
              {sections.length !== 1 ? "s" : ""}.
            </div>

            {/* KPI strip */}
            <div
              className="grid grid-cols-2 sm:grid-cols-4 bg-white border
                            border-gray-200 rounded-xl overflow-hidden mb-5 shadow-sm"
            >
              {[
                {
                  label: "Total Sections",
                  value: sections.length,
                  sub: "in this run",
                  color: "text-gray-900",
                },
                {
                  label: "Avg Quality",
                  value: Math.round(avgScore * 100),
                  sub: "out of 100",
                  color:
                    avgScore >= 0.7
                      ? "text-green-600"
                      : avgScore >= 0.5
                        ? "text-amber-600"
                        : "text-red-600",
                },
                {
                  label: "Approved",
                  value: approved,
                  sub: `of ${sections.length}`,
                  color: approved > 0 ? "text-green-600" : "text-gray-900",
                },
                {
                  label: "Total Words",
                  value: totalWords.toLocaleString(),
                  sub: "across all sections",
                  color: "text-gray-900",
                },
              ].map((m, i, arr) => (
                <div
                  key={m.label}
                  className={`py-4 px-4 text-center
                       ${i < arr.length - 1 ? "border-r border-gray-100" : ""}`}
                >
                  <div
                    className={`text-xl font-bold tabular-nums leading-none
                                   tracking-tight ${m.color}`}
                  >
                    {m.value}
                  </div>
                  <div className="text-[11px] font-semibold text-gray-700 mt-1.5 leading-none">
                    {m.label}
                  </div>
                  <div className="text-[10px] text-gray-300 mt-0.5">
                    {m.sub}
                  </div>
                </div>
              ))}
            </div>

            {/* Quality breakdown */}
            <div className="flex items-center gap-2 mb-3">
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                Quality Breakdown
              </p>
              <div className="flex-1 h-px bg-gray-100" />
            </div>
            <QualityBands sections={sections} />

            {/* Section detail */}
            <div className="flex items-center gap-2 mb-3">
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                Section Detail
              </p>
              <div className="flex-1 h-px bg-gray-100" />
            </div>
            <div className="mb-5">
              <SectionTable
                sections={sections}
                reviewDecisions={state.reviewDecisions}
              />
            </div>

            {/* Regenerate */}
            <button
              onClick={handleGenerateReport}
              className="flex items-center gap-2 border border-gray-200 rounded-lg
                         px-5 py-2.5 text-xs font-semibold text-gray-400
                         hover:text-gray-700 hover:bg-gray-50 transition-colors"
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
                <polyline points="23 4 23 10 17 10" />
                <path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10" />
              </svg>
              Regenerate Report
            </button>

            {/* Start new — mobile only */}
            <div className="flex items-center gap-3 mt-6 md:hidden">
              <div className="flex-1 h-px bg-gray-100" />
              <span className="text-[10px] text-gray-300 font-medium">
                pipeline complete
              </span>
              <div className="flex-1 h-px bg-gray-100" />
            </div>
            <button
              onClick={handleStartNew}
              className="w-full flex items-center justify-center gap-2 mt-4
                         border border-gray-200 bg-white hover:bg-gray-50
                         text-gray-600 text-sm font-semibold px-6 py-2.5
                         rounded-lg transition-colors md:hidden"
            >
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
                <line x1="12" y1="5" x2="12" y2="19" />
                <line x1="5" y1="12" x2="19" y2="12" />
              </svg>
              Start New Project
            </button>
          </>
        )}
      </div>

      {/* ── Right: sidebar ── */}
      <div className="flex-[3] min-w-0 hidden md:block">
        <div className="h-[60px]" />

        <PublishStatusCard projectId={projectId} />

        {/* Assembly result */}
        {state.assemblyResult && (
          <>
            <div className="flex items-center gap-2 mb-3">
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                Assembly Result
              </p>
              <div className="flex-1 h-px bg-gray-100" />
            </div>
            <div
              className="bg-white border border-gray-200 rounded-xl
                            overflow-hidden divide-y divide-gray-50 mb-5 shadow-sm"
            >
              {[
                {
                  label: "Word Count",
                  value:
                    state.assemblyResult.word_count?.toLocaleString() ?? "—",
                },
                {
                  label: "Est. Pages",
                  value: state.assemblyResult.page_estimate ?? "—",
                },
                {
                  label: "Sections",
                  value: state.assemblyResult.section_count ?? "—",
                },
              ].map((row) => (
                <div
                  key={row.label}
                  className="flex items-center justify-between px-4 py-3"
                >
                  <span className="text-xs text-gray-400">{row.label}</span>
                  <span className="text-sm font-bold tabular-nums text-gray-900">
                    {row.value}
                  </span>
                </div>
              ))}
            </div>
          </>
        )}

        {/* Report contents */}
        <div className="flex items-center gap-2 mb-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
            Report Contents
          </p>
          <div className="flex-1 h-px bg-gray-100" />
        </div>
        <div
          className="bg-white border border-gray-200 rounded-xl
                        overflow-hidden divide-y divide-gray-50 mb-5 shadow-sm"
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
                  className="text-gray-400"
                  aria-hidden="true"
                >
                  <line x1="18" y1="20" x2="18" y2="10" />
                  <line x1="12" y1="20" x2="12" y2="4" />
                  <line x1="6" y1="20" x2="6" y2="14" />
                </svg>
              ),
              label: "Quality scores per section",
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
                  className="text-gray-400"
                  aria-hidden="true"
                >
                  <polyline points="20 6 9 17 4 12" />
                </svg>
              ),
              label: "Review decisions (approve/reject)",
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
                  className="text-gray-400"
                  aria-hidden="true"
                >
                  <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                  <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                </svg>
              ),
              label: "Edit & regeneration history",
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
                  className="text-gray-400"
                  aria-hidden="true"
                >
                  <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" />
                </svg>
              ),
              label: "Reviewer notes",
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
                  className="text-gray-400"
                  aria-hidden="true"
                >
                  <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                  <line x1="16" y1="13" x2="8" y2="13" />
                  <line x1="16" y1="17" x2="8" y2="17" />
                </svg>
              ),
              label: "Word count per section",
            },
          ].map((item) => (
            <div key={item.label} className="flex items-center gap-3 px-4 py-3">
              <span className="flex-shrink-0">{item.icon}</span>
              <span className="text-xs text-gray-500">{item.label}</span>
            </div>
          ))}
        </div>

        {/* Project info */}
        {state.metadata && (
          <>
            <div className="flex items-center gap-2 mb-3">
              <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                Project
              </p>
              <div className="flex-1 h-px bg-gray-100" />
            </div>
            <div className="bg-white border border-gray-200 rounded-xl p-4 mb-5 shadow-sm">
              <div className="text-sm font-semibold text-gray-900 mb-0.5">
                {state.metadata.project_name ??
                  state.metadata.projectName ??
                  "—"}
              </div>
              <div className="text-xs text-gray-400">
                {state.metadata.client_name ?? state.metadata.clientName ?? "—"}
              </div>
            </div>
          </>
        )}

        {/* Start New Project */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 shadow-sm">
          <div
            className="text-[10px] font-bold uppercase tracking-widest
                          text-gray-400 mb-1"
          >
            Pipeline Complete
          </div>
          <p className="text-xs text-gray-400 leading-relaxed mb-3">
            Your documentation has been generated, reviewed, assembled, and
            reported. Ready to start another run?
          </p>
          <button
            onClick={handleStartNew}
            className="w-full flex items-center justify-center gap-2
                       bg-primary hover:bg-primary-hover active:bg-primary-active
                       text-white text-xs font-semibold px-4 py-2.5
                       rounded-lg transition-colors shadow-sm"
          >
            <svg
              width="12"
              height="12"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="2.5"
              strokeLinecap="round"
              aria-hidden="true"
            >
              <line x1="12" y1="5" x2="12" y2="19" />
              <line x1="5" y1="12" x2="19" y2="12" />
            </svg>
            Start New Project
          </button>
        </div>
      </div>
    </div>
  );
}
