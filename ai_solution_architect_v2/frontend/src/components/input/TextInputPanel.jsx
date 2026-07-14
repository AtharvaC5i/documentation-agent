// src/components/input/TextInputPanel.jsx
import { useState } from "react";
import { useAppStore } from "../../store/useAppStore";

const DOC_TYPES = [
  {
    id: "brd",
    label: "Business Requirement Document (BRD)",
    icon: (
      <svg
        className="w-4 h-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.8}
        aria-hidden="true"
      >
        <rect x="4" y="2" width="16" height="20" rx="2" />
        <path strokeLinecap="round" d="M8 7h8M8 11h8M8 15h5" />
      </svg>
    ),
    label_full: "Business Requirement Document",
    placeholder: "Describe the project goal, users, features, constraints…",
    description: "Paste the content of your Business Requirement Document",
  },
  {
    id: "tech",
    label: "Technical Documentation",
    icon: (
      <svg
        className="w-4 h-4"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth={1.8}
        aria-hidden="true"
      >
        <rect x="4" y="2" width="16" height="20" rx="2" />
        <path strokeLinecap="round" d="M8 7h4M8 11h8M8 15h6" />
        <path strokeLinecap="round" strokeLinejoin="round" d="M14 7l2 2-2 2" />
      </svg>
    ),
    label_full: "Technical Documentation",
    placeholder:
      "Existing systems, APIs, data models, infrastructure constraints…",
    description: "Paste the content of your Technical Documentation",
  },
];

function FieldLabel({ children, optional = false }) {
  return (
    <p className="text-[0.78rem] font-semibold uppercase tracking-[0.06em] text-brand-navy mb-1.5">
      {children}
      {optional && (
        <span className="font-normal normal-case tracking-normal text-brand-muted ml-1">
          (optional)
        </span>
      )}
    </p>
  );
}

export default function TextInputPanel() {
  const [activeType, setActiveType] = useState("brd");
  const { brdText, setBrdText, techDocText, setTechDocText } = useAppStore();

  const handleTypeChange = (id) => {
    if (id === "brd") setTechDocText("");
    if (id === "tech") setBrdText("");
    setActiveType(id);
  };

  const active = DOC_TYPES.find((d) => d.id === activeType);
  const value = activeType === "brd" ? brdText : techDocText;
  const onChange = activeType === "brd" ? setBrdText : setTechDocText;

  /* Live char count */
  const charCount = value.length;

  return (
    <div className="flex flex-col items-center gap-5">
      {/* ── Segmented toggle ────────────────────────────────── */}
      <div className="flex flex-col items-center gap-2">
        <p className="text-[0.72rem] font-semibold uppercase tracking-[0.07em] text-brand-muted">
          Document type
        </p>

        <div className="flex items-center gap-1.5 p-1 bg-[#EDE9F7] rounded-[12px]">
          {DOC_TYPES.map((opt) => {
            const isActive = activeType === opt.id;
            return (
              <button
                key={opt.id}
                onClick={() => handleTypeChange(opt.id)}
                aria-pressed={isActive}
                className={`
                  flex items-center gap-2 px-4 py-2 rounded-[9px]
                  text-[0.8rem] font-semibold transition-all duration-200 select-none
                  ${isActive
                    ? "bg-white text-brand-navy shadow-[0_1px_6px_rgba(124,92,191,0.18)] border border-brand-border"
                    : "text-brand-muted hover:text-brand-navy hover:bg-white/50"
                  }
                `}
              >
                <span
                  className={`transition-colors duration-200 ${isActive ? "text-brand-purple" : "text-brand-muted"}`}
                >
                  {opt.icon}
                </span>
                {opt.label}
              </button>
            );
          })}
        </div>

        {/* Helper text */}
        <p className="text-[0.74rem] text-brand-muted flex items-center gap-1.5">
          <svg
            className="w-3 h-3 shrink-0 text-brand-purple"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth={2}
            aria-hidden="true"
          >
            <circle cx="8" cy="8" r="6" />
            <path strokeLinecap="round" d="M8 7.5v3M8 5.5v.5" />
          </svg>
          {active.description}
        </p>
      </div>

      {/* ── Textarea ─────────────────────────────────────────── */}
      <div
        className="w-full max-w-2xl animate-[fadeSlideIn_0.2s_ease-out]"
        key={activeType}
      >
        <div className="flex items-baseline justify-between mb-1.5">
          <FieldLabel optional>{active.label_full}</FieldLabel>
          {/* Live char counter */}
          <span
            className={`
              text-[0.7rem] tabular-nums transition-colors duration-200
              ${charCount > 0 ? "text-brand-purple font-medium" : "text-brand-muted"}
            `}
          >
            {charCount > 0 ? `${charCount.toLocaleString()} chars` : ""}
          </span>
        </div>

        <div className="relative">
          <textarea
            value={value}
            onChange={(e) => onChange(e.target.value)}
            placeholder={active.placeholder}
            rows={12}
            className="
              w-full bg-[#FDFCFF] border border-brand-border rounded-[10px]
              px-4 py-3 text-[0.88rem] text-[#1A1A2E] font-sans
              resize-y shadow-[inset_0_1px_3px_rgba(124,92,191,0.05)]
              placeholder:text-brand-muted/60
              focus:outline-none focus:border-brand-purple
              focus:shadow-[0_0_0_3px_rgba(124,92,191,0.10),inset_0_1px_3px_rgba(124,92,191,0.05)]
              transition-all duration-200
            "
          />

          {/* Clear button — only visible when there's content */}
          {charCount > 0 && (
            <button
              onClick={() => onChange("")}
              aria-label="Clear text"
              className="
                absolute top-2.5 right-2.5
                flex items-center justify-center w-6 h-6
                rounded-full bg-[#EDE9F7] hover:bg-[#DDD4F5]
                text-brand-muted hover:text-brand-navy
                transition-all duration-150
              "
            >
              <svg
                className="w-3 h-3"
                viewBox="0 0 16 16"
                fill="none"
                stroke="currentColor"
                strokeWidth={2.2}
                aria-hidden="true"
              >
                <path strokeLinecap="round" d="M4 4l8 8M12 4l-8 8" />
              </svg>
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
