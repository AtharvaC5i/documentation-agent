// src/components/generate/GenerateButton.jsx
import { Wand2 } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";
import { useGeneratePptx } from "../../hooks/useGeneratePptx";
import Spinner from "../ui/Spinner";

export default function GenerateButton() {
  const {
    inputMode,
    brdText,
    brdExtracted,
    techDocText,
    techDocExtracted,
    isGenerating,
    selectedSlides,
  } = useAppStore();
  const { run } = useGeneratePptx();

  const effectiveBrd = inputMode === "paste" ? brdText : brdExtracted;
  const effectiveTechDoc =
    inputMode === "paste" ? techDocText : techDocExtracted;
  const hasContent =
    effectiveBrd.trim().length > 0 || effectiveTechDoc.trim().length > 0;
  const canGenerate = hasContent && selectedSlides.length > 0 && !isGenerating;

  return (
    <div className="flex flex-col items-center gap-3 my-6">
      {/* ── Main button ──────────────────────────────────────── */}
      <button
        onClick={() => canGenerate && run()}
        disabled={!canGenerate}
        aria-busy={isGenerating}
        className={`
          relative flex items-center justify-center gap-2.5
          w-full max-w-sm h-12 px-8 rounded-[10px]
          text-white font-semibold text-[0.92rem] tracking-[0.01em]
          transition-all duration-200 overflow-hidden
          ${
            canGenerate
              ? "bg-gradient-to-br from-brand-navy to-brand-purple shadow-purple hover:shadow-purple-lg hover:-translate-y-px active:translate-y-0"
              : "bg-[#C4BAE8] cursor-not-allowed"
          }
        `}
      >
        {/* Subtle shimmer on hover when enabled */}
        {canGenerate && !isGenerating && (
          <span className="absolute inset-0 bg-white/5 opacity-0 hover:opacity-100 transition-opacity duration-200 rounded-[10px]" />
        )}

        {isGenerating ? (
          <>
            <Spinner size="sm" />
            <span>Generating…</span>
          </>
        ) : (
          <>
            <Wand2 size={15} strokeWidth={2} />
            <span>Generate Architecture Deck</span>
          </>
        )}
      </button>

      {/* ── Status messages ──────────────────────────────────── */}
      {!hasContent && (
        <p className="text-[0.75rem] text-brand-muted text-center max-w-xs leading-relaxed">
          {inputMode === "paste"
            ? "Paste your BRD or Tech Doc above to continue"
            : "Upload and extract a file above to continue"}
        </p>
      )}

      {hasContent && selectedSlides.length === 0 && (
        <p className="text-[0.75rem] text-[#92400E] text-center">
          Select at least one slide to continue
        </p>
      )}

      {isGenerating && (
        <p className="text-[0.75rem] text-brand-muted text-center max-w-sm leading-relaxed animate-pulse">
          Summarising docs → generating architecture → building diagram →
          compiling PowerPoint…
        </p>
      )}
    </div>
  );
}
