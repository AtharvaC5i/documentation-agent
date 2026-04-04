import { useState, useRef } from "react";

const ACCEPTED = ".pdf,.docx,.txt,.md";

export default function FileDropZone({ onFile, disabled = false }) {
  const [isDragging, setIsDragging] = useState(false);
  const inputRef = useRef(null);

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
  };
  const handleDragIn = (e) => {
    handleDrag(e);
    setIsDragging(true);
  };
  const handleDragOut = (e) => {
    handleDrag(e);
    setIsDragging(false);
  };

  const handleDrop = (e) => {
    handleDrag(e);
    setIsDragging(false);
    const file = e.dataTransfer.files?.[0];
    if (file) onFile(file);
  };

  const handleChange = (e) => {
    const file = e.target.files?.[0];
    if (file) {
      onFile(file);
      // reset so same file can be re-selected
      e.target.value = "";
    }
  };

  return (
    <div
      onClick={() => !disabled && inputRef.current?.click()}
      onDragEnter={handleDragIn}
      onDragLeave={handleDragOut}
      onDragOver={handleDrag}
      onDrop={handleDrop}
      className={`
        relative flex flex-col items-center justify-center gap-2
        border-2 border-dashed rounded-[10px] px-6 py-8
        cursor-pointer select-none transition-all duration-200
        ${
          isDragging
            ? "border-brand-purple bg-brand-purple-light"
            : "border-brand-border bg-white hover:border-brand-purple hover:bg-brand-purple-light"
        }
        ${disabled ? "opacity-50 cursor-not-allowed" : ""}
      `}
    >
      {/* Upload icon */}
      <svg
        className={`w-8 h-8 transition-colors duration-200 ${isDragging ? "text-brand-purple" : "text-brand-muted"}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={1.5}
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"
        />
      </svg>

      <p className="text-sm text-brand-navy font-medium text-center">
        {isDragging ? "Drop file here" : "Click to browse or drag & drop"}
      </p>
      <p className="text-xs text-brand-muted">.pdf · .docx · .txt · .md</p>

      <input
        ref={inputRef}
        type="file"
        accept={ACCEPTED}
        onChange={handleChange}
        className="sr-only"
        tabIndex={-1}
        aria-hidden="true"
      />
    </div>
  );
}
