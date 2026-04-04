import { useState } from "react";
import { useAppStore } from "../../store/useAppStore";

const SLIDES = [
  { key: "Title", label: "Title" },
  { key: "ExecSummary", label: "Executive Summary" },
  { key: "Problem", label: "Problem Statement" },
  { key: "Solution", label: "Proposed Solution" },
  { key: "Diagram", label: "Architecture Diagram" },
  { key: "Components", label: "Component Breakdown" },
  { key: "DataFlow", label: "Data Flow" },
  { key: "TechStack", label: "Technology Stack" },
  { key: "Features", label: "Key Features & Capabilities" },
  { key: "NFR", label: "Non-Functional Requirements" },
  { key: "Roadmap", label: "Implementation Roadmap" },
  { key: "Risks", label: "Risks, Assumptions & Open Questions" },
  { key: "Closing", label: "Closing / Next Steps" },
];

function SlideCheckbox({ slideKey, label, checked, onChange }) {
  const id = `slide-${slideKey}`;
  return (
    <label
      htmlFor={id}
      className={`
        flex items-center gap-2.5 px-3 py-2.5 rounded-[8px] cursor-pointer
        border transition-all duration-150 select-none
        ${
          checked
            ? "border-brand-purple bg-brand-purple-light text-brand-navy"
            : "border-brand-border bg-white text-[#1A1A2E] hover:border-brand-purple hover:bg-brand-purple-light"
        }
      `}
    >
      {/* Hidden native checkbox — accessible but visually replaced */}
      <input
        id={id}
        type="checkbox"
        checked={checked}
        onChange={onChange}
        className="sr-only"
      />

      {/* Custom checkbox box */}
      <span
        className={`
          flex items-center justify-center w-4 h-4 rounded-[4px] shrink-0
          border transition-colors duration-150
          ${
            checked
              ? "bg-brand-purple border-brand-purple"
              : "bg-white border-brand-border"
          }
        `}
        aria-hidden="true"
      >
        {checked && (
          <svg
            className="w-2.5 h-2.5 text-white"
            viewBox="0 0 10 10"
            fill="none"
          >
            <path
              d="M1.5 5L4 7.5L8.5 2.5"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        )}
      </span>

      <span className="text-[0.82rem] font-medium leading-tight">{label}</span>
    </label>
  );
}

export default function SlideSelector() {
  const [open, setOpen] = useState(true);
  const { selectedSlides, toggleSlide, customSlidesRaw, setCustomSlidesRaw } =
    useAppStore();

  const allSelected = selectedSlides.length === SLIDES.length;
  const noneSelected = selectedSlides.length === 0;

  const handleSelectAll = () =>
    SLIDES.forEach(({ key }) => {
      if (!selectedSlides.includes(key)) toggleSlide(key);
    });
  const handleDeselectAll = () =>
    SLIDES.forEach(({ key }) => {
      if (selectedSlides.includes(key)) toggleSlide(key);
    });

  return (
    <div className="mb-6 border border-brand-border rounded-[12px] overflow-hidden bg-white shadow-sm">
      {/* ── Expander header ── */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="
          w-full flex items-center justify-between
          px-5 py-3.5 bg-white
          hover:bg-brand-purple-light transition-colors duration-150
        "
        aria-expanded={open}
      >
        <span className="text-[0.88rem] font-semibold text-brand-navy">
          Select slides to include
          <span className="ml-2 text-brand-muted font-normal text-[0.78rem]">
            ({selectedSlides.length} / {SLIDES.length} selected)
          </span>
        </span>

        <svg
          className={`w-4 h-4 text-brand-purple transition-transform duration-200 ${open ? "rotate-180" : ""}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={2}
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M19 9l-7 7-7-7"
          />
        </svg>
      </button>

      {/* ── Collapsible body ── */}
      {open && (
        <div className="px-5 pb-5 pt-1 border-t border-brand-border">
          {/* Select / Deselect all controls */}
          <div className="flex items-center gap-3 mb-4 mt-3">
            <button
              onClick={handleSelectAll}
              disabled={allSelected}
              className="
                text-[0.78rem] font-medium text-brand-purple
                hover:underline underline-offset-2
                disabled:opacity-40 disabled:cursor-not-allowed
                transition-opacity duration-150
              "
            >
              Select all
            </button>
            <span className="text-brand-border text-xs">|</span>
            <button
              onClick={handleDeselectAll}
              disabled={noneSelected}
              className="
                text-[0.78rem] font-medium text-brand-purple
                hover:underline underline-offset-2
                disabled:opacity-40 disabled:cursor-not-allowed
                transition-opacity duration-150
              "
            >
              Deselect all
            </button>
          </div>

          {/* 4-column checkbox grid */}
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-2">
            {SLIDES.map(({ key, label }) => (
              <SlideCheckbox
                key={key}
                slideKey={key}
                label={label}
                checked={selectedSlides.includes(key)}
                onChange={() => toggleSlide(key)}
              />
            ))}
          </div>

          {/* Divider */}
          <hr className="border-brand-border my-4" />

          {/* Custom slides textarea */}
          <div>
            <p className="text-[0.78rem] font-semibold uppercase tracking-[0.06em] text-brand-navy mb-1">
              Custom slides
              <span className="font-normal normal-case tracking-normal text-brand-muted ml-1">
                (optional)
              </span>
            </p>
            <p className="text-[0.75rem] text-brand-muted mb-2">
              One per line in format:{" "}
              <code className="bg-[#EDE9F7] text-brand-purple px-1 py-0.5 rounded text-[0.72rem]">
                Title|One-line content
              </code>
            </p>
            <textarea
              value={customSlidesRaw}
              onChange={(e) => setCustomSlidesRaw(e.target.value)}
              placeholder={`e.g. Appendix|Short note about appendix\nCustom Slide|Single-line content`}
              rows={3}
              className="
                w-full bg-white border border-brand-border rounded-[10px]
                px-4 py-3 text-[0.85rem] text-[#1A1A2E] font-sans
                resize-y shadow-sm
                placeholder:text-brand-muted
                focus:outline-none focus:border-brand-purple focus:ring-2 focus:ring-brand-purple/10
                transition-all duration-200
              "
            />
          </div>
        </div>
      )}
    </div>
  );
}
