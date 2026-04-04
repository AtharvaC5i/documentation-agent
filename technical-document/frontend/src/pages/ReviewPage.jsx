import { useState, useEffect, useCallback, useRef } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useApp } from "../context/AppContext";
import {
  initReview,
  getReviewState,
  submitDecision,
  regenerateSection,
} from "../api/endpoints";
import Spinner from "../components/ui/Spinner";

// ── YOUR original inlineFormat, untouched ─────────────────────────────────────
function inlineFormat(text) {
  return text
    .replace(
      /`([^`]+)`/g,
      '<code class="bg-gray-100 border border-gray-200 rounded px-1 py-0.5 text-xs font-mono">$1</code>',
    )
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>")
    .replace(/__([^_]+)__/g, "<strong>$1</strong>")
    .replace(/_([^_]+)_/g, "<em>$1</em>");
}

// ── YOUR original MarkdownPreview, untouched ──────────────────────────────────
function MarkdownPreview({ content }) {
  if (!content)
    return (
      <p className="text-xs text-gray-400 italic">No content available.</p>
    );
  const lines = content.split("\n");
  const elements = [];
  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    if (line.startsWith("```")) {
      const lang = line.slice(3).trim();
      const code = [];
      i++;
      while (i < lines.length && !lines[i].startsWith("```")) {
        code.push(lines[i]);
        i++;
      }
      elements.push(
        <div
          key={`code-${i}`}
          className="my-3 rounded-lg overflow-hidden border border-gray-200"
        >
          {lang && (
            <div className="px-3 py-1 bg-gray-100 text-[11px] font-mono text-gray-500 border-b border-gray-200">
              {lang}
            </div>
          )}
          <pre className="bg-gray-50 px-4 py-3 text-xs font-mono text-gray-800 overflow-x-auto leading-relaxed">
            {code.join("\n")}
          </pre>
        </div>,
      );
      i++;
      continue;
    }
    if (line.startsWith("#### "))
      elements.push(
        <h4 key={i} className="text-sm font-bold text-gray-900 mt-4 mb-1">
          {line.slice(5)}
        </h4>,
      );
    else if (line.startsWith("### "))
      elements.push(
        <h3 key={i} className="text-base font-bold text-gray-900 mt-5 mb-1.5">
          {line.slice(4)}
        </h3>,
      );
    else if (line.startsWith("## "))
      elements.push(
        <h2
          key={i}
          className="text-lg font-bold text-gray-900 mt-6 mb-2 pb-1 border-b border-gray-200"
        >
          {line.slice(3)}
        </h2>,
      );
    else if (line.startsWith("# "))
      elements.push(
        <h1 key={i} className="text-xl font-bold text-gray-900 mt-6 mb-2">
          {line.slice(2)}
        </h1>,
      );
    else if (line.match(/^---+$/))
      elements.push(<hr key={i} className="border-gray-200 my-4" />);
    else if (line.startsWith("- ") || line.startsWith("* "))
      elements.push(
        <div key={i} className="flex gap-2 my-0.5">
          <span className="text-primary flex-shrink-0 mt-0.5 text-xs">•</span>
          <span
            className="text-sm text-gray-800 leading-relaxed"
            dangerouslySetInnerHTML={{ __html: inlineFormat(line.slice(2)) }}
          />
        </div>,
      );
    else if (/^\d+\. /.test(line)) {
      const num = line.match(/^(\d+)\. /)[1];
      elements.push(
        <div key={i} className="flex gap-2 my-0.5">
          <span className="text-primary font-bold flex-shrink-0 text-xs w-4 text-right mt-0.5">
            {num}.
          </span>
          <span
            className="text-sm text-gray-800 leading-relaxed"
            dangerouslySetInnerHTML={{
              __html: inlineFormat(line.replace(/^\d+\. /, "")),
            }}
          />
        </div>,
      );
    } else if (line.startsWith("> "))
      elements.push(
        <blockquote
          key={i}
          className="border-l-4 border-primary/40 pl-4 my-2 text-sm text-gray-500 italic"
        >
          {line.slice(2)}
        </blockquote>,
      );
    else if (line.trim() === "") elements.push(<div key={i} className="h-2" />);
    else
      elements.push(
        <p
          key={i}
          className="text-sm text-gray-800 leading-relaxed my-1"
          dangerouslySetInnerHTML={{ __html: inlineFormat(line) }}
        />,
      );
    i++;
  }
  return <div>{elements}</div>;
}

// ── SectionReviewCard ─────────────────────────────────────────────────────────
function SectionReviewCard({
  section,
  decision,
  onDecide,
  onRegenerate,
  regenerating,
}) {
  // YOUR original state, untouched
  const [expanded, setExpanded] = useState(false);
  const [editMode, setEditMode] = useState(false);
  const [editedContent, setEditedContent] = useState("");
  const [note, setNote] = useState("");

  const name = section.name;
  const content = decision?.edited_content || section.content || "";
  const score = section.quality_score ?? null;
  const status = decision?.action ?? "pending";
  const isRegen = regenerating === name;

  // YOUR original effects, untouched
  useEffect(() => {
    setEditedContent(content);
    setNote(decision?.note ?? "");
  }, [content, decision?.note]);

  // YOUR original scoreVariant, untouched
  const scoreVariant =
    score === null
      ? "gray"
      : score >= 0.7
        ? "green"
        : score >= 0.5
          ? "amber"
          : "red";

  // Status config (visual only upgrade)
  const cfg = {
    pending: {
      headerBg: "bg-white",
      border: "border-gray-200",
      bodyBg: "bg-white",
      labelCls: "bg-gray-100 text-gray-500 border-gray-200",
      label: "Pending",
    },
    approve: {
      headerBg: "bg-green-50",
      border: "border-green-200",
      bodyBg: "bg-green-50/30",
      labelCls: "bg-green-100 text-green-700 border-green-200",
      label: "Approved",
    },
    reject: {
      headerBg: "bg-red-50",
      border: "border-red-200",
      bodyBg: "bg-red-50/30",
      labelCls: "bg-red-100 text-red-700 border-red-200",
      label: "Rejected",
    },
  }[status] ?? {
    headerBg: "bg-white",
    border: "border-gray-200",
    bodyBg: "bg-white",
    labelCls: "bg-gray-100 text-gray-500 border-gray-200",
    label: "Pending",
  };

  const wordCount = content.split(/\s+/).filter(Boolean).length;

  // YOUR original handleApprove, untouched
  const handleApprove = () => {
    const finalContent =
      editMode && editedContent !== section.content ? editedContent : null;
    onDecide(name, "approve", finalContent, note || null);
    setEditMode(false);
  };

  // Score badge color
  const scoreBg =
    score === null
      ? ""
      : score >= 0.7
        ? "bg-green-100 text-green-700 border-green-200"
        : score >= 0.5
          ? "bg-amber-100 text-amber-700 border-amber-200"
          : "bg-red-100   text-red-700   border-red-200";

  return (
    <div
      className={`rounded-xl border transition-all duration-200 overflow-hidden
                     shadow-sm ${cfg.border}`}
    >
      {/* ── Header (click to expand) ── */}
      <div
        className={`flex items-center gap-3 px-5 py-4 cursor-pointer
                    hover:brightness-[0.98] transition-all ${cfg.headerBg}`}
        onClick={() => setExpanded((e) => !e)}
      >
        {/* Chevron */}
        <svg
          width="13"
          height="13"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2.5"
          strokeLinecap="round"
          className={`text-gray-300 flex-shrink-0 transition-transform duration-200
                         ${expanded ? "rotate-90" : ""}`}
          aria-hidden="true"
        >
          <polyline points="9 18 15 12 9 6" />
        </svg>

        {/* Name + meta */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 flex-wrap">
            <span className="text-sm font-semibold text-gray-900">{name}</span>
            {decision?.edited_content && (
              <span
                className="text-[10px] font-semibold text-gray-400
                               bg-white border border-gray-200 px-1.5 py-0.5 rounded-full"
              >
                edited
              </span>
            )}
          </div>
          <div className="text-[11px] text-gray-400 mt-0.5 tabular-nums">
            {wordCount.toLocaleString()} words
          </div>
        </div>

        {/* Right badges */}
        <div
          className="flex items-center gap-2 flex-shrink-0"
          onClick={(e) => e.stopPropagation()}
        >
          {score !== null && (
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-full
                              border tabular-nums ${scoreBg}`}
            >
              {Math.round(score * 100)}
            </span>
          )}
          <span
            className={`text-[10px] font-bold uppercase tracking-wide
                            px-2 py-0.5 rounded-full border ${cfg.labelCls}`}
          >
            {cfg.label}
          </span>
        </div>
      </div>

      {/* ── Expanded body ── */}
      {expanded && (
        <div className={`border-t border-gray-100 ${cfg.bodyBg}`}>
          {/* Content section */}
          <div className="px-5 pt-4 pb-3">
            <div className="flex items-center justify-between mb-3">
              <span className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
                {editMode ? "Editing Content" : "Content Preview"}
              </span>
              {!editMode ? (
                <button
                  onClick={() => setEditMode(true)}
                  className="flex items-center gap-1 text-xs font-medium
                             text-primary hover:text-primary-hover transition-colors"
                >
                  <svg
                    width="11"
                    height="11"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    aria-hidden="true"
                  >
                    <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                    <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                  </svg>
                  Edit
                </button>
              ) : (
                <button
                  onClick={() => {
                    setEditMode(false);
                    setEditedContent(content);
                  }}
                  className="text-xs font-medium text-gray-400 hover:text-gray-600
                             transition-colors"
                >
                  Cancel
                </button>
              )}
            </div>

            {editMode ? (
              <textarea
                value={editedContent}
                onChange={(e) => setEditedContent(e.target.value)}
                rows={16}
                className="w-full bg-white border border-gray-200 rounded-xl px-4 py-3
                           text-sm font-mono text-gray-800 leading-relaxed resize-y
                           focus:outline-none focus:ring-2 focus:ring-primary/20
                           focus:border-primary transition-colors shadow-sm"
              />
            ) : (
              <div
                className="bg-white border border-gray-200 rounded-xl px-5 py-4
                              max-h-96 overflow-y-auto shadow-sm"
              >
                <MarkdownPreview content={content} />
              </div>
            )}
          </div>

          {/* Reviewer note */}
          <div className="px-5 pb-4">
            <label
              className="text-[10px] font-bold uppercase tracking-widest
                              text-gray-400 block mb-1.5"
            >
              Reviewer Note
              <span className="text-gray-300 font-normal normal-case tracking-normal ml-1">
                (optional)
              </span>
            </label>
            <input
              type="text"
              value={note}
              onChange={(e) => setNote(e.target.value)}
              placeholder="Add a note for this section…"
              className="w-full bg-white border border-gray-200 rounded-lg px-3 py-2
                         text-sm text-gray-800 placeholder:text-gray-300
                         focus:outline-none focus:ring-2 focus:ring-primary/20
                         focus:border-primary transition-colors"
            />
          </div>

          {/* Action buttons */}
          <div className="flex items-center gap-2 px-5 pb-5 flex-wrap">
            {/* Approve */}
            <button
              onClick={handleApprove}
              className="flex items-center gap-1.5 bg-green-600 hover:bg-green-700
                         active:bg-green-800 text-white text-xs font-semibold
                         px-4 py-2 rounded-lg transition-colors shadow-sm"
            >
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                aria-hidden="true"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
              {editMode && editedContent !== section.content
                ? "Save & Approve"
                : "Approve"}
            </button>

            {/* Reject */}
            <button
              onClick={() => onDecide(name, "reject", null, note || null)}
              className="flex items-center gap-1.5 bg-red-500 hover:bg-red-600
                         active:bg-red-700 text-white text-xs font-semibold
                         px-4 py-2 rounded-lg transition-colors shadow-sm"
            >
              <svg
                width="11"
                height="11"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2.5"
                strokeLinecap="round"
                aria-hidden="true"
              >
                <line x1="18" y1="6" x2="6" y2="18" />
                <line x1="6" y1="6" x2="18" y2="18" />
              </svg>
              Reject
            </button>

            {/* Regenerate (right-aligned) */}
            <button
              onClick={() => onRegenerate(name)}
              disabled={isRegen}
              className="flex items-center gap-1.5 ml-auto border border-gray-200
                         bg-white hover:bg-gray-50 text-gray-500 hover:text-gray-700
                         text-xs font-semibold px-4 py-2 rounded-lg transition-colors
                         shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isRegen ? (
                <>
                  <Spinner size="sm" /> Regenerating…
                </>
              ) : (
                <>
                  <svg
                    width="11"
                    height="11"
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
                  Regenerate
                </>
              )}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

// ── ArrangeTab (YOUR logic, reskinned) ────────────────────────────────────────
function ArrangeTab({ order, setOrder, decisions }) {
  // YOUR original refs + state, untouched
  const dragItem = useRef(null);
  const dragOverItem = useRef(null);
  const [dragging, setDragging] = useState(null);
  const [dragOver, setDragOver] = useState(null);

  // YOUR original handlers, untouched
  const handleDragStart = (e, name) => {
    dragItem.current = name;
    setDragging(name);
    e.dataTransfer.effectAllowed = "move";
    const ghost = document.createElement("div");
    ghost.style.position = "absolute";
    ghost.style.top = "-1000px";
    document.body.appendChild(ghost);
    e.dataTransfer.setDragImage(ghost, 0, 0);
    setTimeout(() => document.body.removeChild(ghost), 0);
  };
  const handleDragEnter = (name) => {
    dragOverItem.current = name;
    setDragOver(name);
  };
  const handleDragEnd = () => {
    if (
      dragItem.current &&
      dragOverItem.current &&
      dragItem.current !== dragOverItem.current
    ) {
      const next = [...order];
      const fromIdx = next.indexOf(dragItem.current);
      const toIdx = next.indexOf(dragOverItem.current);
      next.splice(fromIdx, 1);
      next.splice(toIdx, 0, dragItem.current);
      setOrder(next);
    }
    dragItem.current = null;
    dragOverItem.current = null;
    setDragging(null);
    setDragOver(null);
  };

  return (
    <div>
      <p className="text-xs text-gray-400 mb-5 leading-relaxed">
        Drag sections into the order you want in the final document. The dot
        colour reflects the current review status.
      </p>

      <div className="flex flex-col gap-1.5">
        {order.map((name, i) => {
          const dec = decisions[name]?.action ?? "pending";
          const dot =
            dec === "approve"
              ? "bg-green-500"
              : dec === "reject"
                ? "bg-red-500"
                : "bg-gray-200";
          const isDragging = dragging === name;
          const isOver = dragOver === name && dragging !== name;

          return (
            <div
              key={name}
              draggable
              onDragStart={(e) => handleDragStart(e, name)}
              onDragEnter={() => handleDragEnter(name)}
              onDragOver={(e) => e.preventDefault()}
              onDragEnd={handleDragEnd}
              className={`flex items-center gap-3 bg-white border rounded-xl
                          px-4 py-3 select-none cursor-grab active:cursor-grabbing
                          transition-all duration-150 shadow-sm
                          ${isDragging ? "opacity-40 scale-[0.98] border-primary/40 shadow-lg" : "border-gray-200"}
                          ${isOver ? "border-primary bg-primary/5 shadow-md -translate-y-0.5" : ""}
                        `}
            >
              {/* Drag handle dots */}
              <div className="flex flex-col gap-[3px] flex-shrink-0 opacity-25">
                {[0, 1, 2].map((r) => (
                  <div key={r} className="flex gap-[3px]">
                    <span className="w-[3px] h-[3px] rounded-full bg-gray-500 block" />
                    <span className="w-[3px] h-[3px] rounded-full bg-gray-500 block" />
                  </div>
                ))}
              </div>

              {/* Index badge */}
              <span
                className="w-6 h-6 rounded-md bg-gray-100 border border-gray-200
                               flex items-center justify-center text-[11px] font-bold
                               text-gray-500 flex-shrink-0 tabular-nums"
              >
                {i + 1}
              </span>

              {/* Status dot */}
              <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dot}`} />

              {/* Name */}
              <span className="flex-1 text-sm font-medium text-gray-800 truncate">
                {name}
              </span>

              {/* Drop indicator */}
              {isOver && (
                <span
                  className="text-[10px] font-bold text-primary flex-shrink-0 uppercase
                                 tracking-wide"
                >
                  Drop here
                </span>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ── Main Page ─────────────────────────────────────────────────────────────────
export default function ReviewPage() {
  const { state, dispatch } = useApp();
  const navigate = useNavigate();
  const { id: projectId } = useParams();

  // YOUR original state, untouched
  const [activeTab, setActiveTab] = useState("review");
  const [decisions, setDecisions] = useState({});
  const [order, setOrder] = useState([]);
  const [regenerating, setRegenerating] = useState(null);
  const [initError, setInitError] = useState(null);
  const [submitErrors, setSubmitErrors] = useState({});
  const [approvingAll, setApprovingAll] = useState(false);

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
    if (state.sectionOrder.length) setOrder(state.sectionOrder);
    if (Object.keys(state.reviewDecisions).length)
      setDecisions(state.reviewDecisions);
  }, []);

  // YOUR original init + load, untouched
  useEffect(() => {
    if (!projectId || !state.generationResults.length) return;
    const init = async () => {
      try {
        const sections = state.generationResults.map((s) => ({
          name: s.name,
          content: s.content,
          order: s.order ?? 0,
          quality_score: s.quality_score ?? null,
        }));
        await initReview(projectId, sections).catch(() => {});
        const { data } = await getReviewState(projectId);
        if (data.sections) {
          const dec = {};
          const arr = Array.isArray(data.sections)
            ? data.sections
            : Object.entries(data.sections).map(([name, val]) => ({
                name,
                ...val,
              }));
          arr.forEach((s) => {
            if (s.status && s.status !== "pending") {
              dec[s.name] = {
                action: s.status,
                edited_content: s.edited_content ?? null,
                note: s.note ?? null,
              };
            }
          });
          setDecisions(dec);
        }
      } catch (e) {
        setInitError(e.message);
      }
    };
    init();
  }, [projectId]);

  // YOUR original order seed, untouched
  useEffect(() => {
    if (!order.length && state.generationResults.length) {
      const sorted = [...state.generationResults]
        .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
        .map((s) => s.name);
      setOrder(sorted);
    }
  }, [state.generationResults]);

  // YOUR original handleDecide, untouched
  const handleDecide = useCallback(
    async (name, action, editedContent, note) => {
      const decision = { action, edited_content: editedContent, note };
      setDecisions((prev) => ({ ...prev, [name]: decision }));
      dispatch({
        type: "SET_REVIEW_DECISION",
        payload: { sectionName: name, decision },
      });
      try {
        await submitDecision(projectId, {
          section_name: name,
          action,
          edited_content: editedContent ?? null,
          note: note ?? null,
        });
        setSubmitErrors((prev) => {
          const n = { ...prev };
          delete n[name];
          return n;
        });
      } catch (e) {
        setSubmitErrors((prev) => ({ ...prev, [name]: e.message }));
        setDecisions((prev) => {
          const n = { ...prev };
          delete n[name];
          return n;
        });
      }
    },
    [projectId, dispatch],
  );

  // YOUR original handleApproveAll, untouched
  const handleApproveAll = async () => {
    setApprovingAll(true);
    const pending = state.generationResults.filter(
      (s) => !decisions[s.name] || decisions[s.name].action === "pending",
    );
    for (const section of pending) {
      await handleDecide(section.name, "approve", null, null);
    }
    setApprovingAll(false);
  };

  // YOUR original handleRegenerate, untouched
  const handleRegenerate = useCallback(
    async (name) => {
      setRegenerating(name);
      try {
        const { data } = await regenerateSection(projectId, name);
        const result = data.result;
        const updated = state.generationResults.map((s) =>
          s.name === name
            ? {
                ...s,
                content: result.content,
                quality_score: result.quality_score,
                status: result.status,
                regenerated: true,
              }
            : s,
        );
        dispatch({
          type: "SET_GENERATION_FINISHED",
          payload: { results: updated },
        });
        setDecisions((prev) => {
          const n = { ...prev };
          delete n[name];
          return n;
        });
        dispatch({
          type: "SET_REVIEW_DECISION",
          payload: { sectionName: name, decision: null },
        });
      } catch (e) {
        setSubmitErrors((prev) => ({ ...prev, [name]: e.message }));
      } finally {
        setRegenerating(null);
      }
    },
    [projectId, state.generationResults, dispatch],
  );

  // YOUR original order sync effect, untouched
  useEffect(() => {
    if (order.length) dispatch({ type: "SET_SECTION_ORDER", payload: order });
  }, [order]);

  // YOUR original stats derivations, untouched
  const total = state.generationResults.length;
  const approved = Object.values(decisions).filter(
    (d) => d?.action === "approve",
  ).length;
  const rejected = Object.values(decisions).filter(
    (d) => d?.action === "reject",
  ).length;
  const edited = Object.values(decisions).filter(
    (d) => d?.edited_content,
  ).length;
  const pending = total - approved - rejected;
  const avgScore =
    total > 0
      ? state.generationResults.reduce(
          (a, s) => a + (s.quality_score ?? 0),
          0,
        ) / total
      : 0;
  const sortedSections = [...state.generationResults].sort(
    (a, b) => (a.order ?? 0) - (b.order ?? 0),
  );

  // ────────────────────────────────────────────────────────────────────────
  return (
    <div className="flex gap-10">
      {/* ── Left: main content ── */}
      <div className="flex-[6] min-w-0">
        {/* Page heading */}
        <div className="mb-5">
          <h1 className="text-xl font-semibold text-gray-900 tracking-tight">
            Review & Arrange
          </h1>
          <p className="text-sm text-gray-500 mt-1 leading-relaxed">
            Edit content, approve or reject each section, then arrange them into
            the order you want in the final document.
          </p>
        </div>

        {/* Init error */}
        {initError && (
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
            {initError}
          </div>
        )}

        {/* Pending warning */}
        {pending > 0 && (
          <div
            className="flex items-center gap-2.5 bg-amber-50 border border-amber-200
                          rounded-lg px-3.5 py-2.5 mb-4 text-xs font-medium text-amber-700"
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
            <strong className="font-bold">{pending}</strong>&nbsp;section
            {pending !== 1 ? "s" : ""} still pending — you can continue to
            assembly anyway.
          </div>
        )}

        {/* Tabs + Approve All */}
        <div className="flex items-center justify-between mb-5 gap-3 flex-wrap">
          {/* Tab switcher */}
          <div className="flex bg-gray-100 rounded-lg p-0.5 gap-0.5">
            {[
              { key: "review", label: "Review Sections" },
              { key: "arrange", label: "Arrange Order" },
            ].map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-1.5 text-xs font-semibold rounded-md
                            transition-all duration-150
                  ${
                    activeTab === tab.key
                      ? "bg-white text-gray-900 shadow-sm"
                      : "text-gray-400 hover:text-gray-600"
                  }`}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Approve All */}
          {activeTab === "review" && pending > 0 && (
            <button
              onClick={handleApproveAll}
              disabled={approvingAll}
              className="flex items-center gap-1.5 bg-green-600 hover:bg-green-700
                         active:bg-green-800 text-white text-xs font-semibold
                         px-4 py-2 rounded-lg transition-colors shadow-sm
                         disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {approvingAll ? (
                <>
                  <Spinner size="sm" className="text-white" /> Approving…
                </>
              ) : (
                <>
                  <svg
                    width="11"
                    height="11"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2.5"
                    strokeLinecap="round"
                    aria-hidden="true"
                  >
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  Approve All Pending ({pending})
                </>
              )}
            </button>
          )}
        </div>

        {/* Review tab */}
        {activeTab === "review" && (
          <div className="flex flex-col gap-2.5">
            {sortedSections.map((section) => (
              <div key={section.name}>
                {submitErrors[section.name] && (
                  <div
                    className="flex items-start gap-2 bg-red-50 border border-red-200
                                  rounded-lg px-3 py-2 mb-1.5 text-xs text-red-700"
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
                    {submitErrors[section.name]}
                  </div>
                )}
                <SectionReviewCard
                  section={section}
                  decision={decisions[section.name] ?? null}
                  onDecide={handleDecide}
                  onRegenerate={handleRegenerate}
                  regenerating={regenerating}
                />
              </div>
            ))}
          </div>
        )}

        {/* Arrange tab */}
        {activeTab === "arrange" && (
          <ArrangeTab order={order} setOrder={setOrder} decisions={decisions} />
        )}

        {/* Sticky continue */}
        <div
          className="sticky bottom-0 pb-2 pt-4
                        bg-gradient-to-t from-white via-white to-transparent mt-8"
        >
          <button
            onClick={() => navigate(`/project/${projectId}/assembly`)}
            className="w-full flex items-center justify-center gap-2
                       bg-primary hover:bg-primary-hover text-white
                       text-sm font-semibold px-6 py-2.5 rounded-lg
                       transition-colors shadow-sm"
          >
            Continue to Assembly
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

      {/* ── Right: sidebar ── */}
      <div className="flex-[4] min-w-0 hidden md:block">
        <div className="h-[60px]" />

        {/* Summary KPIs */}
        <div className="flex items-center gap-2 mb-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
            Review Summary
          </p>
          <div className="flex-1 h-px bg-gray-100" />
        </div>
        <div className="grid grid-cols-2 gap-2 mb-5">
          {[
            { label: "Total", value: total, sub: "sections" },
            {
              label: "Approved",
              value: approved,
              sub: "sections",
              color: approved > 0 ? "text-green-600" : undefined,
            },
            {
              label: "Pending",
              value: pending,
              sub: "sections",
              color: pending > 0 ? "text-amber-600" : undefined,
            },
            {
              label: "Avg Quality",
              value: Math.round(avgScore * 100),
              sub: "score",
              color:
                avgScore >= 0.7
                  ? "text-green-600"
                  : avgScore >= 0.5
                    ? "text-amber-600"
                    : "text-red-600",
            },
          ].map((m) => (
            <div
              key={m.label}
              className="bg-white border border-gray-200 rounded-xl py-4 px-4 text-center"
            >
              <div
                className={`text-xl font-bold tabular-nums leading-none
                               ${m.color ?? "text-gray-900"}`}
              >
                {m.value}
              </div>
              <div className="text-[11px] font-semibold text-gray-700 mt-1.5 leading-none">
                {m.label}
              </div>
              <div className="text-[10px] text-gray-300 mt-0.5">{m.sub}</div>
            </div>
          ))}
        </div>

        {/* Review progress bar */}
        <div className="bg-white border border-gray-200 rounded-xl p-4 mb-5">
          <div className="flex justify-between text-xs text-gray-400 mb-2.5">
            <span>Review progress</span>
            <span className="tabular-nums font-semibold text-gray-700">
              {approved + rejected} / {total}
            </span>
          </div>
          {/* Segmented bar */}
          <div className="flex gap-0.5 h-2 rounded-full overflow-hidden mb-3">
            {sortedSections.map((s) => {
              const dec = decisions[s.name]?.action ?? "pending";
              return (
                <div
                  key={s.name}
                  className={`flex-1 transition-all duration-300
                       ${
                         dec === "approve"
                           ? "bg-green-500"
                           : dec === "reject"
                             ? "bg-red-400"
                             : "bg-gray-100"
                       }`}
                />
              );
            })}
          </div>
          {/* Legend */}
          <div className="flex items-center gap-4 text-[11px] text-gray-400">
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-green-500 flex-shrink-0" />
              {approved} approved
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-red-400 flex-shrink-0" />
              {rejected} rejected
            </span>
            {edited > 0 && (
              <span className="flex items-center gap-1.5">
                <span className="w-2 h-2 rounded-full bg-primary flex-shrink-0" />
                {edited} edited
              </span>
            )}
          </div>
        </div>

        {/* Document order */}
        <div className="flex items-center gap-2 mb-3">
          <p className="text-[10px] font-bold uppercase tracking-widest text-gray-400">
            Document Order
          </p>
          <div className="flex-1 h-px bg-gray-100" />
        </div>
        <div
          className="bg-white border border-gray-200 rounded-xl
                        overflow-hidden divide-y divide-gray-50"
        >
          {order.map((name, i) => {
            const dec = decisions[name]?.action ?? "pending";
            const dot =
              dec === "approve"
                ? "bg-green-500"
                : dec === "reject"
                  ? "bg-red-400"
                  : "bg-gray-200";
            const nameColor =
              dec === "approve"
                ? "text-green-700"
                : dec === "reject"
                  ? "text-red-600"
                  : "text-gray-500";
            return (
              <div
                key={name}
                className="flex items-center gap-2.5 py-2.5 px-3.5
                              hover:bg-gray-50 transition-colors"
              >
                <span
                  className="text-[10px] text-gray-300 tabular-nums w-4
                                 text-right flex-shrink-0"
                >
                  {i + 1}
                </span>
                <span className={`w-2 h-2 rounded-full flex-shrink-0 ${dot}`} />
                <span
                  className={`text-xs font-medium flex-1 truncate ${nameColor}`}
                >
                  {name}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
