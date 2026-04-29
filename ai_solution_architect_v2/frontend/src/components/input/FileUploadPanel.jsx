// src/components/input/FileUploadPanel.jsx
import { useState } from "react";
import { useAppStore } from "../../store/useAppStore";
import SingleFileUploader from "./SingleFileUploader";

const DOC_TYPES = [
  {
    id: "brd",
    label: "Busiess Requirement Document",
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
    description: "Upload your Business Requirement Document",
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
    description: "Upload your Technical Specifications document",
  },
];

export default function FileUploadPanel() {
  const [activeType, setActiveType] = useState("brd");
  const { setBrdExtracted, setTechDocExtracted } = useAppStore();

  const handleTypeChange = (id) => {
    if (id === "brd") setTechDocExtracted("");
    if (id === "tech") setBrdExtracted("");
    setActiveType(id);
  };

  return (
    <div className="flex flex-col items-center gap-5">
      {/* ── Segmented toggle ──────────────────────────────── */}
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
                  ${
                    isActive
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
          {DOC_TYPES.find((d) => d.id === activeType).description}
        </p>
      </div>

      {/* ── Upload slot ───────────────────────────────────── */}
      <div
        className="w-full max-w-md animate-[fadeSlideIn_0.2s_ease-out]"
        key={activeType}
      >
        {activeType === "brd" && (
          <SingleFileUploader
            label="BRD File"
            onExtracted={setBrdExtracted}
            onCleared={() => setBrdExtracted("")}
          />
        )}
        {activeType === "tech" && (
          <SingleFileUploader
            label="Technical Documentation"
            onExtracted={setTechDocExtracted}
            onCleared={() => setTechDocExtracted("")}
          />
        )}
      </div>
    </div>
  );
}
