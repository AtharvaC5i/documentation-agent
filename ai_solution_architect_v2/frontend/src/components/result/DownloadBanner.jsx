import { useRef } from "react";
import { useAppStore } from "../../store/useAppStore";

export default function DownloadBanner() {
  const { pptxBlob, resetResult } = useAppStore();
  const anchorRef = useRef(null);

  const handleDownload = () => {
    if (!pptxBlob) return;

    // Create a temporary object URL and trigger browser download
    const url = URL.createObjectURL(pptxBlob);
    const anchor = anchorRef.current;
    anchor.href = url;
    anchor.download = "architecture.pptx";
    anchor.click();

    // Revoke after a short delay so the download has time to start
    setTimeout(() => URL.revokeObjectURL(url), 2000);
  };

  return (
    <div>
      {/* Divider */}
      <hr className="border-brand-border mb-6" />

      {/* Ready card */}
      <div
        className="
          rounded-[12px] border border-brand-border
          bg-gradient-to-br from-[#EDE9F7] to-brand-bg
          px-6 py-5 mb-5
        "
      >
        <p className="font-serif text-[1.15rem] text-brand-navy mb-1">
          Your deck is ready
        </p>
        <p className="text-[0.85rem] text-brand-purple">
          Consulting-quality architecture document · Mermaid diagram embedded ·
          Ready to present
        </p>
      </div>

      {/* Download button — centered like Streamlit */}
      <div className="flex justify-center flex-col items-center gap-3">
        {/* Invisible anchor — triggered programmatically */}
        {/* eslint-disable-next-line jsx-a11y/anchor-has-content */}
        <a ref={anchorRef} aria-hidden="true" className="sr-only" />

        <button
          onClick={handleDownload}
          className="
            flex items-center justify-center gap-2.5
            px-8 h-12 rounded-[10px] w-full max-w-sm
            bg-gradient-to-br from-[#1A7F5A] to-[#2D9CDB]
            text-white font-semibold text-[0.95rem]
            shadow-green
            hover:shadow-[0_6px_24px_rgba(26,127,90,0.4)] hover:-translate-y-px
            active:translate-y-0
            transition-all duration-200
          "
          aria-label="Download architecture.pptx"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2.5}
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
            />
          </svg>
          <span>Download architecture.pptx</span>
        </button>

        {/* Hint text */}
        <p className="text-[0.8rem] text-brand-muted text-center">
          Want a fresh deck? Edit your inputs above and generate again.
        </p>

        {/* Clear result button */}
        <button
          onClick={resetResult}
          className="
            text-[0.78rem] text-brand-muted
            hover:text-brand-purple underline underline-offset-2
            transition-colors duration-150
          "
        >
          Clear result
        </button>
      </div>
    </div>
  );
}
