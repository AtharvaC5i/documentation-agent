// src/hooks/useFileExtract.js
import { useState } from "react";
import { extractText } from "../api/architectApi";

export function useFileExtract() {
  const [isExtracting, setIsExtracting] = useState(false);
  const [extractError, setExtractError] = useState(null);
  const [result, setResult] = useState(null);

  const extract = async (file) => {
    if (!file) return;
    setIsExtracting(true);
    setExtractError(null);
    try {
      const { data } = await extractText(file);
      setResult({
        text: data.extracted_text,
        charCount: data.char_count,
        warning: data.warning,
      });
      return data.extracted_text;
    } catch (e) {
      setExtractError(e.response?.data?.detail ?? e.message);
      return null;
    } finally {
      setIsExtracting(false);
    }
  };

  const reset = () => {
    setResult(null);
    setExtractError(null);
    setIsExtracting(false);
  };

  return { extract, reset, isExtracting, extractError, result };
}
