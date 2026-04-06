import { useState, useEffect, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useApp } from "../context/AppContext";
import {
  assembleDocument,
  downloadDocument,
  sendEmail,
} from "../api/endpoints";
import Spinner from "../components/ui/Spinner";

// ── YOUR original ASSEMBLY_STEPS, untouched ───────────────────────────────────
const ASSEMBLY_STEPS = [
  { key: "collect", label: "Collecting approved sections" },
  { key: "render", label: "Rendering DOCX with python-docx" },
  { key: "format", label: "Applying formatting & styles" },
  { key: "save", label: "Saving to storage" },
  { key: "done", label: "Document ready" },
];

// ── SectionOrderList (YOUR logic, reskinned) ──────────────────────────────────
function SectionOrderList({ order, decisions }) {
  return (
    <div
      className="bg-white border border-gray-200 rounded-xl overflow-hidden
                    divide-y divide-gray-50"
    >
      {order.map((name, i) => {
        const dec = decisions[name]?.action ?? "pending";
        const dot =
          dec === "approve"
            ? "bg-green-500"
            : dec === "reject"
              ? "bg-red-400"
              : "bg-gray-300";
        const dimmed = dec === "reject";
        return (
          <div
            key={name}
            className={`flex items-center gap-3 px-4 py-2.5 transition-opacity
                           ${dimmed ? "opacity-35" : ""}`}
          >
            <span
              className="text-[10px] text-gray-300 tabular-nums w-4
                             text-right flex-shrink-0 font-medium"
            >
              {i + 1}
            </span>
            <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dot}`} />
            <span className="text-xs font-medium text-gray-800 flex-1 truncate">
              {name}
            </span>
            {dec === "reject" && (
              <span className="text-[10px] text-red-400 font-semibold flex-shrink-0">
                skipped
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── AssemblyProgress (YOUR logic, reskinned) ──────────────────────────────────
function AssemblyProgress({ currentStep, done }) {
  const pct = Math.round(((currentStep + 1) / ASSEMBLY_STEPS.length) * 100);

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
              {done
                ? "Assembly complete"
                : ASSEMBLY_STEPS[currentStep]?.label + "…"}
            </span>
          </div>
          <span className="text-xs font-bold tabular-nums text-gray-400">
            {done ? "100%" : `${pct}%`}
          </span>
        </div>
        <div className="w-full h-1 bg-gray-100 rounded-full overflow-hidden">
          <div
            className="h-full rounded-full transition-all duration-500 ease-out"
            style={{
              width: done ? "100%" : `${pct}%`,
              backgroundColor: done
                ? "#22c55e"
                : "var(--color-primary, #01696f)",
            }}
          />
        </div>
      </div>

      {/* Step list */}
      <div className="divide-y divide-gray-50">
        {ASSEMBLY_STEPS.map((step, idx) => {
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
              <span
                className={`text-xs font-semibold
                ${isActive ? "text-primary" : ""}
                ${isComplete ? "text-green-700" : ""}
                ${isPending ? "text-gray-300" : ""}
              `}
              >
                {step.label}
              </span>
              {isComplete && (
                <span className="ml-auto text-[10px] font-bold text-green-400">
                  done
                </span>
              )}
              {isActive && (
                <Spinner size="sm" className="ml-auto text-primary" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── EmailForm (YOUR logic, reskinned) ─────────────────────────────────────────
function EmailForm({ projectId, metadata, onSent }) {
  // YOUR original state, untouched
  const [recipients, setRecipients] = useState("");
  const [subject, setSubject] = useState(
    `${metadata?.project_name ?? "Project"} — Technical Documentation`,
  );
  const [message, setMessage] = useState(
    `Please find attached the generated technical documentation for ${metadata?.project_name ?? "the project"}.`,
  );
  const [sending, setSending] = useState(false);
  const [sent, setSent] = useState(false);
  const [error, setError] = useState(null);

  // YOUR original handleSend, untouched
  const handleSend = async () => {
    const recList = recipients
      .split(",")
      .map((r) => r.trim())
      .filter(Boolean);
    if (!recList.length) {
      setError("Enter at least one recipient email.");
      return;
    }
    setSending(true);
    setError(null);
    try {
      await sendEmail(projectId, { recipients: recList, subject, message });
      setSent(true);
      onSent?.();
    } catch (e) {
      setError(e.message);
    } finally {
      setSending(false);
    }
  };

  if (sent) {
    return (
      <div
        className="flex items-center gap-2.5 bg-green-50 border border-green-200
                      rounded-xl px-4 py-3.5 text-sm font-medium text-green-700"
      >
        <svg
          width="15"
          height="15"
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
        Email sent successfully.
      </div>
    );
  }

  const inputCls = `w-full bg-white border border-gray-200 rounded-lg px-3 py-2.5
                    text-sm text-gray-800 placeholder:text-gray-300
                    focus:outline-none focus:ring-2 focus:ring-primary/20
                    focus:border-primary transition-colors`;

  return (
    <div className="bg-white border border-gray-200 rounded-xl overflow-hidden shadow-sm">
      {/* Header */}
      <div
        className="flex items-center gap-2.5 px-5 py-3.5 border-b border-gray-100
                      bg-gray-50"
      >
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
          <line x1="22" y1="2" x2="11" y2="13" />
          <polygon points="22 2 15 22 11 13 2 9 22 2" />
        </svg>
        <span className="text-xs font-bold uppercase tracking-widest text-gray-400">
          Send by Email
        </span>
      </div>

      <div className="px-5 py-4 flex flex-col gap-3.5">
        {error && (
          <div
            className="flex items-start gap-2 text-xs text-red-700 bg-red-50
                          border border-red-200 rounded-lg px-3 py-2.5"
          >
            <svg
              width="12"
              height="12"
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

        {/* Recipients */}
        <div>
          <label
            className="text-[10px] font-bold uppercase tracking-widest
                            text-gray-400 block mb-1.5"
          >
            Recipients{" "}
            <span className="text-red-400 normal-case tracking-normal">*</span>
          </label>
          <input
            type="text"
            value={recipients}
            onChange={(e) => setRecipients(e.target.value)}
            placeholder="alice@company.com, bob@company.com"
            className={inputCls}
          />
          <p className="text-[10px] text-gray-300 mt-1">
            Comma-separated addresses
          </p>
        </div>

        {/* Subject */}
        <div>
          <label
            className="text-[10px] font-bold uppercase tracking-widest
                            text-gray-400 block mb-1.5"
          >
            Subject
          </label>
          <input
            type="text"
            value={subject}
            onChange={(e) => setSubject(e.target.value)}
            className={inputCls}
          />
        </div>

        {/* Message */}
        <div>
          <label
            className="text-[10px] font-bold uppercase tracking-widest
                            text-gray-400 block mb-1.5"
          >
            Message
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            rows={3}
            className={`${inputCls} resize-none leading-relaxed`}
          />
        </div>

        <button
          onClick={handleSend}
          disabled={sending}
          className="flex items-center justify-center gap-2 bg-primary
                     hover:bg-primary-hover active:bg-primary-active text-white
                     text-sm font-semibold px-5 py-2.5 rounded-lg
                     transition-colors shadow-sm disabled:opacity-50
                     disabled:cursor-not-allowed w-full"
        >
          {sending ? (
            <>
              <Spinner size="sm" className="text-white" /> Sending…
            </>
          ) : (
            <>
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
                <line x1="22" y1="2" x2="11" y2="13" />
                <polygon points="22 2 15 22 11 13 2 9 22 2" />
              </svg>
              Send Document
            </>
          )}
        </button>
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function AssemblyPage() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  const { id: projectId } = useParams();

  // YOUR original state, untouched
  const [assembling, setAssembling] = useState(false);
  const [currentStep, setCurrentStep] = useState(0);
  const [assemblyDone, setAssemblyDone] = useState(false);
  const [error, setError] = useState(null);
  const [downloading, setDownloading] = useState(false);
  const [emailSent, setEmailSent] = useState(false);
  const stepTimerRef = useRef(null);

  // YOUR original guards, untouched
  useEffect(() => {
    if (!projectId) {
      navigate("/ingest");
      return;
    }
    if (!state.generationFinished) {
      navigate(`/project/${projectId}/generate`);
      return;
    }
  }, []);

  useEffect(() => {
    if (state.assemblyResult) setAssemblyDone(true);
  }, []);

  // YOUR original startStepAnimation, untouched
  const startStepAnimation = () => {
    let step = 0;
    const totalSteps = ASSEMBLY_STEPS.length - 1;
    const stepDuration = 800;
    stepTimerRef.current = setInterval(() => {
      step += 1;
      if (step < totalSteps) setCurrentStep(step);
      else clearInterval(stepTimerRef.current);
    }, stepDuration);
  };

  // YOUR original handleAssemble, untouched
  const handleAssemble = async () => {
    setAssembling(true);
    setError(null);
    setCurrentStep(0);
    setAssemblyDone(false);
    startStepAnimation();

    const orderedSections = state.sectionOrder
      .map((name, i) => {
        const found = state.generationResults.find((s) => s.name === name);
        if (!found) return null;
        return {
          name: found.name,
          content: found.content,
          order: i,
          quality_score: found.quality_score ?? null,
        };
      })
      .filter(Boolean);

    try {
      const { data } = await assembleDocument(projectId, {
        project_id: projectId,
        metadata: {
          project_name:
            state.metadata?.project_name ??
            state.metadata?.projectName ??
            "Untitled",
          client_name:
            state.metadata?.client_name ?? state.metadata?.clientName ?? "",
          team_members:
            state.metadata?.team_members ?? state.metadata?.teamMembers ?? [],
          description: state.metadata?.description ?? "",
        },
        sections: orderedSections,
      });
      clearInterval(stepTimerRef.current);
      setCurrentStep(ASSEMBLY_STEPS.length - 1);
      setAssemblyDone(true);
      dispatch({ type: "SET_ASSEMBLY_RESULT", payload: data });
    } catch (e) {
      clearInterval(stepTimerRef.current);
      setError(e.message);
    } finally {
      setAssembling(false);
    }
  };

  // YOUR original handleDownload, untouched
  const handleDownload = async () => {
    setDownloading(true);
    try {
      const response = await downloadDocument(projectId);
      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      const filename =
        `${state.metadata?.project_name ?? "documentation"}_docagent.docx`
          .replace(/\s+/g, "_")
          .toLowerCase();
      a.href = url;
      a.download = filename;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (e) {
      setError(`Download failed: ${e.message}`);
    } finally {
      setDownloading(false);
    }
  };

  // YOUR original cleanup, untouched
  useEffect(() => () => clearInterval(stepTimerRef.current), []);

  // YOUR original derived values, untouched
  const result = state.assemblyResult;
  const metadata = state.metadata ?? state.projectMetadata ?? null;
  const order = state.sectionOrder;
  const decisions = state.reviewDecisions;
  const approvedCount = order.filter(
    (name) => decisions[name]?.action === "approve",
  ).length;
  const rejectedCount = order.filter(
    (name) => decisions[name]?.action === "reject",
  ).length;

  // ──────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex gap-10">
      {/* ── Left: main content ── */}
      <div className="flex-[6] min-w-0">
        {/* Page heading */}
        <div className="mb-5">
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
            Document Assembly
          </h1>
          <p className="text-sm text-gray-500 mt-1 leading-relaxed">
            Approved sections are assembled into a formatted DOCX using{" "}
            <code
              className="text-xs font-mono text-gray-600 bg-gray-100
                             px-1 py-0.5 rounded"
            >
              python-docx
            </code>
            . Download the document directly.
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

        {/* ── State: pre-assembly ── */}
        {!assemblyDone && !assembling && (
          <>
            {/* KPI strip */}
            <div
              className="grid grid-cols-3 bg-white border border-gray-200
                            rounded-xl overflow-hidden mb-5"
            >
              {[
                { label: "Sections", value: order.length, sub: "total queued" },
                {
                  label: "Approved",
                  value: approvedCount,
                  sub: "will be included",
                  color: approvedCount > 0 ? "text-green-600" : undefined,
                },
                {
                  label: "Rejected",
                  value: rejectedCount,
                  sub: "will be skipped",
                  color: rejectedCount > 0 ? "text-red-500" : undefined,
                },
              ].map((m, i) => (
                <div
                  key={m.label}
                  className={`py-4 px-4 text-center
                       ${i < 2 ? "border-r border-gray-100" : ""}`}
                >
                  <div
                    className={`text-xl font-bold tabular-nums leading-none
                                   tracking-tight ${m.color ?? "text-gray-900"}`}
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

            {/* Warnings */}
            {rejectedCount > 0 && (
              <div
                className="flex items-center gap-2.5 bg-amber-50 border border-amber-200
                              rounded-lg px-3.5 py-2.5 mb-3 text-xs font-medium text-amber-700"
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
                  <path
                    d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0
                           1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
                  />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                <strong className="font-bold">{rejectedCount}</strong>
                &nbsp;rejected section
                {rejectedCount !== 1 ? "s" : ""} will be excluded from the
                document.
              </div>
            )}
            {approvedCount === 0 && (
              <div
                className="flex items-center gap-2.5 bg-amber-50 border border-amber-200
                              rounded-lg px-3.5 py-2.5 mb-3 text-xs font-medium text-amber-700"
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
                  <path
                    d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0
                           1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"
                  />
                  <line x1="12" y1="9" x2="12" y2="13" />
                  <line x1="12" y1="17" x2="12.01" y2="17" />
                </svg>
                No sections approved — the document will use all generated
                sections.
              </div>
            )}

            <button
              onClick={handleAssemble}
              className="w-full flex items-center justify-center gap-2
                         bg-primary hover:bg-primary-hover active:bg-primary-active
                         text-white text-sm font-semibold px-6 py-2.5
                         rounded-lg transition-colors shadow-sm mt-1"
            >
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
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                <polyline points="14 2 14 8 20 8" />
              </svg>
              Assemble Document
            </button>
          </>
        )}

        {/* ── State: assembling ── */}
        {assembling && (
          <div>
            <div className="flex items-center gap-2 mb-3">
              <Spinner size="sm" className="text-primary" />
              <span className="text-sm font-medium text-gray-800">
                Assembling document…
              </span>
            </div>
            <AssemblyProgress currentStep={currentStep} done={false} />
          </div>
        )}

        {/* ── State: assembled ── */}
        {assemblyDone && !assembling && (
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
              Document assembled successfully.
            </div>

            {/* Result KPI strip */}
            <div
              className="grid grid-cols-3 bg-white border border-gray-200
                            rounded-xl overflow-hidden mb-5"
            >
              {[
                {
                  label: "Word Count",
                  value: result?.word_count?.toLocaleString() ?? "—",
                  sub: "approx.",
                },
                {
                  label: "Est. Pages",
                  value: result?.page_estimate ?? "—",
                  sub: "pages",
                },
                {
                  label: "Sections",
                  value: result?.section_count ?? approvedCount,
                  sub: "included",
                },
              ].map((m, i) => (
                <div
                  key={m.label}
                  className={`py-4 px-4 text-center
                       ${i < 2 ? "border-r border-gray-100" : ""}`}
                >
                  <div
                    className="text-xl font-bold tabular-nums leading-none
                                  tracking-tight text-gray-900"
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

            {/* Download button */}
            <button
              onClick={handleDownload}
              disabled={downloading}
              className="w-full flex items-center justify-center gap-2
                         bg-primary hover:bg-primary-hover active:bg-primary-active
                         text-white text-sm font-semibold px-6 py-2.5
                         rounded-lg transition-colors shadow-sm mb-5
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {downloading ? (
                <>
                  <Spinner size="sm" className="text-white" /> Preparing
                  download…
                </>
              ) : (
                <>
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    aria-hidden="true"
                  >
                    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                    <polyline points="7 10 12 15 17 10" />
                    <line x1="12" y1="15" x2="12" y2="3" />
                  </svg>
                  Download DOCX
                </>
              )}
            </button>


            {/* Divider */}
            <div className="h-px bg-gray-100 my-5" />

            {/* Re-assemble + Continue */}
            <div className="flex gap-3">
              <button
                onClick={() => {
                  dispatch({ type: "SET_ASSEMBLY_RESULT", payload: null });
                  setAssemblyDone(false);
                  setCurrentStep(0);
                }}
                className="flex-1 border border-gray-200 rounded-lg py-2.5
                           text-sm font-medium text-gray-400 hover:text-gray-700
                           hover:bg-gray-50 transition-colors"
              >
                Re-assemble
              </button>
              <button
                onClick={() => navigate(`/project/${projectId}/report`)}
                className="flex-1 flex items-center justify-center gap-2
                           bg-primary hover:bg-primary-hover text-white
                           text-sm font-semibold px-6 py-2.5 rounded-lg
                           transition-colors shadow-sm"
              >
                Continue to Report
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
          </>
        )}
      </div>

      {/* ── Right: sidebar ── */}
      <div className="flex-[4] min-w-0 hidden md:block">
        <div className="h-[60px]" />

        {/* Document order */}
        <div className="flex items-center gap-2 mb-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
            Document Order
          </p>
          <div className="flex-1 h-px bg-gray-100" />
        </div>
        <div className="mb-5">
          <SectionOrderList order={order} decisions={decisions} />
        </div>

        {/* Review summary */}
        <div className="flex items-center gap-2 mb-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
            Review Summary
          </p>
          <div className="flex-1 h-px bg-gray-100" />
        </div>
        <div
          className="bg-white border border-gray-200 rounded-xl
                        overflow-hidden divide-y divide-gray-50 mb-5"
        >
          {[
            {
              label: "Approved",
              count: approvedCount,
              dot: "bg-green-500",
              text: "text-green-700",
            },
            {
              label: "Rejected",
              count: rejectedCount,
              dot: "bg-red-400",
              text: "text-red-600",
            },
            {
              label: "Pending",
              count: order.length - approvedCount - rejectedCount,
              dot: "bg-gray-200",
              text: "text-gray-400",
            },
          ].map((row) => (
            <div
              key={row.label}
              className="flex items-center justify-between px-4 py-3"
            >
              <div className="flex items-center gap-2.5">
                <span className={`w-2 h-2 rounded-full ${row.dot}`} />
                <span className="text-xs font-medium text-gray-700">
                  {row.label}
                </span>
              </div>
              <span className={`text-sm font-bold tabular-nums ${row.text}`}>
                {row.count}
              </span>
            </div>
          ))}
        </div>

        {/* Email sent indicator */}
        {emailSent && (
          <div
            className="flex items-center gap-2 text-xs font-medium text-green-700
                          bg-green-50 border border-green-200 rounded-lg px-3 py-2.5"
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
              <polyline points="20 6 9 17 4 12" />
            </svg>
            Document sent by email
          </div>
        )}
      </div>
    </div>
  );
}
