// src/components/result/DownloadBanner.jsx
import { useRef } from "react";
import { Download, FileSliders, RotateCcw } from "lucide-react";
import { useAppStore } from "../../store/useAppStore";

export default function DownloadBanner() {
  const { pptxBlob, resetResult } = useAppStore();
  const anchorRef = useRef(null);

  const handleDownload = () => {
    if (!pptxBlob) return;
    const url = URL.createObjectURL(pptxBlob);
    const anchor = anchorRef.current;
    anchor.href = url;
    anchor.download = "architecture.pptx";
    anchor.click();
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  };

  return (
    <div className="mt-6">
      <hr className="border-brand-border mb-6" />

      {/* ── Ready card ─────────────────────────────────────── */}
      <div className="rounded-[14px] border border-brand-border bg-white shadow-[0_2px_16px_rgba(124,92,191,0.07)] overflow-hidden mb-5">
        {/* Top accent bar */}
        <div className="h-1 w-full bg-gradient-to-r from-brand-navy to-brand-purple" />

        <div className="flex items-center gap-4 px-5 py-4">
          {/* Icon tile */}
          <span className="flex items-center justify-center w-10 h-10 rounded-[10px] bg-[#EDE9F7] shrink-0">
            <FileSliders
              size={18}
              className="text-brand-purple"
              strokeWidth={1.8}
            />
          </span>

          {/* Text */}
          <div className="flex-1">
            <p className="font-serif text-[1.05rem] text-brand-navy leading-tight">
              Your deck is ready
            </p>
            <p className="text-[0.78rem] text-brand-muted mt-0.5">
              Architecture document generated · Diagram embedded · Ready to
              present
            </p>
          </div>

          {/* Pill badge */}
          <span className="shrink-0 px-3 py-1 rounded-full bg-[#EDE9F7] text-brand-purple text-[0.7rem] font-semibold border border-brand-border">
            .pptx
          </span>
        </div>
      </div>

      {/* ── Actions ────────────────────────────────────────── */}
      <div className="flex flex-col items-center gap-3">
        {/* eslint-disable-next-line jsx-a11y/anchor-has-content */}
        <a ref={anchorRef} aria-hidden="true" className="sr-only" />

        {/* Download button */}
        <button
          onClick={handleDownload}
          className="
            flex items-center justify-center gap-2.5
            w-full max-w-sm h-12 px-8 rounded-[10px]
            bg-gradient-to-br from-brand-navy to-brand-purple
            text-white font-semibold text-[0.92rem]
            shadow-purple
            hover:shadow-purple-lg hover:-translate-y-px
            active:translate-y-0
            transition-all duration-200
          "
          aria-label="Download architecture.pptx"
        >
          <Download size={16} strokeWidth={2.2} />
          <span>Download architecture.pptx</span>
        </button>

        {/* Hint */}
        <p className="text-[0.76rem] text-brand-muted text-center">
          Want a fresh deck? Edit your inputs above and generate again.
        </p>

        {/* Clear result */}
        <button
          onClick={resetResult}
          className="
            flex items-center gap-1.5
            text-[0.75rem] text-brand-muted
            hover:text-brand-purple
            transition-colors duration-150
          "
        >
          <RotateCcw size={11} strokeWidth={2} />
          <span>Clear result</span>
        </button>
      </div>
    </div>
  );
}
