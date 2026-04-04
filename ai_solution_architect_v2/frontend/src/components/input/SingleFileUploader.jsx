// src/components/input/SingleFileUploader.jsx
import { useState, useCallback } from "react";
import FileDropZone from "../ui/FileDropZone";
import ExtractedPreview from "../ui/ExtractedPreview";
import Spinner from "../ui/Spinner";
import Alert from "../ui/Alert";
import { useFileExtract } from "../../hooks/useFileExtract";

export default function SingleFileUploader({
  label,
  optional = false,
  onExtracted,
  onCleared,
}) {
  // Key trick: incrementing key forces a full remount of FileDropZone, resetting its state
  const [dropKey, setDropKey] = useState(0);
  const [fileName, setFileName] = useState(null);
  const { extract, isExtracting, extractError, result, reset } =
    useFileExtract();

  const handleFile = useCallback(
    async (file) => {
      setFileName(file.name);
      const text = await extract(file);
      if (text) onExtracted(text);
    },
    [extract, onExtracted],
  );

  const handleReplace = () => {
    reset(); // clear hook state
    setFileName(null);
    setDropKey((k) => k + 1); // remount drop zone
    onCleared?.(); // clear extracted text in store
  };

  return (
    <div className="flex flex-col gap-2">
      <p className="text-[0.78rem] font-semibold uppercase tracking-[0.06em] text-brand-navy">
        {label}
        {optional && (
          <span className="font-normal normal-case tracking-normal text-brand-muted ml-1">
            (optional)
          </span>
        )}
      </p>

      {!isExtracting && !result && !extractError && (
        <FileDropZone key={dropKey} onFile={handleFile} />
      )}

      {isExtracting && (
        <div className="flex items-center gap-3 border border-brand-border rounded-[10px] bg-white px-5 py-4">
          <Spinner size="md" />
          <span className="text-sm text-brand-navy">
            Extracting from <span className="font-medium">{fileName}</span>…
          </span>
        </div>
      )}

      {result && !isExtracting && (
        <div className="flex flex-col gap-2">
          {result.warning ? (
            <Alert type="warning" message={result.warning} />
          ) : (
            <Alert
              type="success"
              message={`${fileName} — ${result.charCount.toLocaleString()} characters extracted`}
            />
          )}
          <ExtractedPreview text={result.text} />
          <button
            onClick={handleReplace}
            className="
              self-start text-[0.8rem] text-brand-muted
              underline underline-offset-2
              hover:text-brand-purple transition-colors duration-150
            "
          >
            Replace file
          </button>
        </div>
      )}

      {extractError && !isExtracting && (
        <div className="flex flex-col gap-2">
          <Alert type="error" message={`Extraction failed: ${extractError}`} />
          <FileDropZone key={dropKey} onFile={handleFile} />
          <button
            onClick={handleReplace}
            className="self-start text-[0.78rem] text-brand-muted underline underline-offset-2 hover:text-brand-purple"
          >
            Clear
          </button>
        </div>
      )}
    </div>
  );
}
