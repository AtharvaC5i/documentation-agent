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

  // Allow generation if EITHER BRD or Tech Doc is non-empty
  const effectiveBrd = inputMode === "paste" ? brdText : brdExtracted;
  const effectiveTechDoc =
    inputMode === "paste" ? techDocText : techDocExtracted;

  const hasContent =
    effectiveBrd.trim().length > 0 || effectiveTechDoc.trim().length > 0;

  const canGenerate = hasContent && selectedSlides.length > 0 && !isGenerating;

  const handleClick = async () => {
    if (!canGenerate) return;
    await run();
  };

  return (
    <div className="flex justify-center">
      <div className="w-full max-w-sm flex flex-col items-center gap-3">
        <button
          onClick={handleClick}
          disabled={!canGenerate}
          className={`
            w-full flex items-center justify-center gap-2.5
            px-8 h-12 rounded-[10px]
            text-white font-semibold text-[0.95rem] tracking-[0.02em]
            transition-all duration-200
            ${
              canGenerate
                ? `bg-gradient-to-br from-brand-navy to-brand-purple
                 shadow-purple hover:shadow-purple-lg hover:-translate-y-px
                 active:translate-y-0 active:shadow-purple`
                : "bg-gradient-to-br from-brand-navy/50 to-brand-purple/50 cursor-not-allowed opacity-60"
            }
          `}
          aria-busy={isGenerating}
          aria-label={
            isGenerating
              ? "Generating architecture deck…"
              : "Generate architecture deck"
          }
        >
          {isGenerating ? (
            <>
              <Spinner size="sm" />
              <span>Generating…</span>
            </>
          ) : (
            <>
              <span className="text-[1.1rem]">◈</span>
              <span>Generate Architecture Deck</span>
            </>
          )}
        </button>

        {/* Hint text below button */}
        {!hasContent && (
          <p className="text-[0.78rem] text-brand-muted text-center">
            {inputMode === "paste"
              ? "Paste your BRD and/or Technical Doc above to enable generation"
              : "Upload and extract your BRD and/or Technical Doc file above to enable generation"}
          </p>
        )}

        {selectedSlides.length === 0 && hasContent && (
          <p className="text-[0.78rem] text-[#92400E] text-center">
            Select at least one slide to include
          </p>
        )}

        {isGenerating && (
          <p className="text-[0.78rem] text-brand-muted text-center animate-pulse">
            Running AI pipeline: summarising docs → generating architecture →
            building diagram → compiling PowerPoint…
          </p>
        )}
      </div>
    </div>
  );
}
