// src/components/slides/SlideSelector.jsx
import { useState } from "react";
import { LayoutTemplate, ChevronDown, Check, Sparkles } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";

const SLIDES = [
  { key: "Problem", label: "Problem Statement", group: "core" },
  { key: "Solution", label: "Proposed Solution", group: "core" },
  { key: "Diagram", label: "Architecture Diagram", group: "core" },
  { key: "Components", label: "Component Breakdown", group: "core" },
  { key: "DataFlow", label: "Data Flow", group: "core" },
  { key: "TechStack", label: "Technology Stack", group: "core" },
  { key: "Features", label: "Key Features & Capabilities", group: "detail" },
  { key: "NFR", label: "Non-Functional Requirements", group: "detail" },
  { key: "Roadmap", label: "Implementation Roadmap", group: "detail" },
  { key: "Risks", label: "Risks & Assumptions", group: "detail" },
];

const GROUPS = [
  { key: "core", label: "Core Architecture" },
  { key: "detail", label: "Details & NFRs" },
];

/* ── Single pill ─────────────────────────────────────────── */
function SlidePill({ slideKey, label, index, checked, onChange }) {
  return (
    <button
      type="button"
      role="checkbox"
      aria-checked={checked}
      onClick={onChange}
      className={`
        group relative flex items-center gap-2.5 w-full
        px-3 py-2.5 rounded-[10px] text-left
        border transition-all duration-200 select-none
        ${
          checked
            ? "bg-[#F0EBFF] border-brand-purple/50 shadow-[0_0_0_3px_rgba(124,92,191,0.07)]"
            : "bg-white border-brand-border hover:border-brand-purple/30 hover:bg-[#FAF8FF]"
        }
      `}
    >
      <span
        className={`
        shrink-0 w-5 h-5 rounded-full text-[0.6rem] font-bold
        flex items-center justify-center tabular-nums
        transition-all duration-200
        ${
          checked
            ? "bg-brand-purple text-white"
            : "bg-[#EDE9F7] text-brand-muted group-hover:bg-[#E2D9F3]"
        }
      `}
      >
        {checked ? <Check size={10} strokeWidth={3} /> : index}
      </span>

      <span
        className={`
        flex-1 text-[0.78rem] font-medium leading-tight
        transition-colors duration-200
        ${checked ? "text-brand-navy" : "text-[#4A4870] group-hover:text-brand-navy"}
      `}
      >
        {label}
      </span>

      <span
        className={`shrink-0 transition-all duration-200 ${checked ? "opacity-100 scale-100" : "opacity-0 scale-75"}`}
      >
        <Check size={12} className="text-brand-purple" strokeWidth={2.5} />
      </span>
    </button>
  );
}

/* ── Group section ───────────────────────────────────────── */
function SlideGroup({
  groupKey,
  groupLabel,
  selectedSlides,
  toggleSlide,
  onToggleGroup,
}) {
  const groupSlides = SLIDES.filter((s) => s.group === groupKey);
  const startIndex = SLIDES.findIndex((s) => s.group === groupKey) + 1;
  const allOn = groupSlides.every((s) => selectedSlides.includes(s.key));

  return (
    <div>
      <div className="flex items-center gap-2 mb-2">
        <span className="text-[0.65rem] font-bold uppercase tracking-[0.1em] text-brand-muted whitespace-nowrap">
          {groupLabel}
        </span>
        <div className="flex-1 h-px bg-brand-border" />
        <button
          onClick={() => onToggleGroup(groupSlides)}
          className="text-[0.65rem] font-semibold text-brand-purple/70 hover:text-brand-purple transition-colors ml-1 shrink-0"
        >
          {allOn ? "Deselect all" : "Select all"}
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-1.5 mb-4">
        {groupSlides.map((slide, i) => (
          <SlidePill
            key={slide.key}
            slideKey={slide.key}
            label={slide.label}
            index={startIndex + i}
            checked={selectedSlides.includes(slide.key)}
            onChange={() => toggleSlide(slide.key)}
          />
        ))}
      </div>
    </div>
  );
}

/* ── Main component ──────────────────────────────────────── */
export default function SlideSelector() {
  const [open, setOpen] = useState(true);
  const { selectedSlides, toggleSlide, customSlidesRaw, setCustomSlidesRaw } =
    useAppStore();

  const selectAll = () =>
    SLIDES.forEach((s) => {
      if (!selectedSlides.includes(s.key)) toggleSlide(s.key);
    });
  const clearAll = () =>
    SLIDES.forEach((s) => {
      if (selectedSlides.includes(s.key)) toggleSlide(s.key);
    });
  const toggleGroup = (groupSlides) => {
    const allOn = groupSlides.every((s) => selectedSlides.includes(s.key));
    groupSlides.forEach((s) => {
      const isOn = selectedSlides.includes(s.key);
      if (allOn && isOn) toggleSlide(s.key);
      if (!allOn && !isOn) toggleSlide(s.key);
    });
  };

  return (
    <div className="mb-6 rounded-[14px] bg-white border border-brand-border shadow-[0_2px_16px_rgba(124,92,191,0.07)] overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center gap-3.5 px-5 py-4 hover:bg-[#FDFCFF] transition-colors duration-150"
        aria-expanded={open}
        aria-controls="slide-selector-body"
      >
        <span className="flex items-center justify-center w-9 h-9 rounded-[9px] bg-[#EDE9F7] shrink-0">
          <LayoutTemplate
            size={16}
            className="text-brand-purple"
            strokeWidth={1.8}
          />
        </span>
        <div className="flex-1 text-left">
          <p className="text-[0.88rem] font-semibold text-brand-navy leading-none">
            Slide deck composition
          </p>
          <p className="text-[0.72rem] text-brand-muted mt-0.5">
            Choose which slides to include in your deck
          </p>
        </div>
        <ChevronDown
          size={16}
          className={`text-brand-purple shrink-0 transition-transform duration-300 ${open ? "rotate-180" : ""}`}
          strokeWidth={2}
        />
      </button>

      {/* Body */}
      {open && (
        <div
          id="slide-selector-body"
          className="px-5 pt-3 pb-5 border-t border-brand-border"
        >
          {/* Select / clear all */}
          <div className="flex items-center justify-end gap-2 mb-3">
            <button
              onClick={selectAll}
              className="text-[0.7rem] font-semibold text-brand-purple hover:text-brand-navy transition-colors"
            >
              Select all
            </button>
            <span className="text-brand-border text-xs">·</span>
            <button
              onClick={clearAll}
              className="text-[0.7rem] font-medium text-brand-muted hover:text-brand-navy transition-colors"
            >
              Clear all
            </button>
          </div>

          {/* Grouped slide pills */}
          {GROUPS.map(({ key, label }) => (
            <SlideGroup
              key={key}
              groupKey={key}
              groupLabel={label}
              selectedSlides={selectedSlides}
              toggleSlide={toggleSlide}
              onToggleGroup={toggleGroup}
            />
          ))}

          {/* Custom slides */}
          <div className="flex items-center gap-2 mb-3">
            <span className="text-[0.65rem] font-bold uppercase tracking-[0.1em] text-brand-muted whitespace-nowrap">
              Custom Slides
            </span>
            <div className="flex-1 h-px bg-brand-border" />
            <span className="text-[0.65rem] text-brand-muted font-medium">
              optional
            </span>
          </div>

          <p className="text-[0.73rem] text-brand-muted mb-2 leading-relaxed">
            One slide topic per line — AI will automatically expand each into
            full slide content
          </p>

          <textarea
            value={customSlidesRaw}
            onChange={(e) => setCustomSlidesRaw(e.target.value)}
            placeholder={`e.g. Implementation Timeline\nBudget Breakdown\nStakeholder Analysis`}
            rows={3}
            className="
              w-full bg-[#FDFCFF] border border-brand-border rounded-[10px]
              px-4 py-3 text-[0.84rem] text-[#1A1A2E] font-sans
              resize-y shadow-[inset_0_1px_3px_rgba(124,92,191,0.04)]
              placeholder:text-brand-muted/50
              focus:outline-none focus:border-brand-purple
              focus:shadow-[0_0_0_3px_rgba(124,92,191,0.09)]
              transition-all duration-200
            "
          />

          <div className="flex items-start gap-2 mt-2.5 px-3 py-2.5 rounded-[9px] bg-[#F5F2FF] border border-brand-purple/15">
            <Sparkles
              size={13}
              className="text-brand-purple shrink-0 mt-0.5"
              strokeWidth={1.8}
            />
            <p className="text-[0.7rem] text-[#4A4870] leading-relaxed">
              Each line is treated as a topic. The AI will automatically
              generate{" "}
              <span className="font-semibold text-brand-purple">
                rich, structured slide content
              </span>{" "}
              based on your BRD and technical documentation.
            </p>
          </div>
        </div>
      )}
    </div>
  );
}
