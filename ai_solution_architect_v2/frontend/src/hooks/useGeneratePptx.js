// src/hooks/useGeneratePptx.js
import { useAppStore } from "../store/useAppStore";
import { generatePptx } from "../api/architectApi";

export function useGeneratePptx() {
  const {
    inputMode,
    brdText,
    brdExtracted,
    techDocText,
    techDocExtracted,
    selectedSlides,
    customSlidesRaw,
    setIsGenerating,
    setPptxBlob,
    setGenerateError,
    resetResult,
  } = useAppStore();

  const run = async () => {
    const brd = inputMode === "paste" ? brdText : brdExtracted;
    const techDoc = inputMode === "paste" ? techDocText : techDocExtracted;

    if (!brd.trim()) {
      return;
    }

    resetResult();
    setIsGenerating(true);

    try {
      const res = await generatePptx({
        brdText: brd,
        techDocText: techDoc,
        selectedSlides,
        customSlidesRaw,
      });
      setPptxBlob(res.data); // Blob from axios responseType:'blob'
    } catch (err) {
      let message = "Unexpected error. Please try again.";

      if (err.code === "ECONNABORTED") {
        message =
          "The pipeline timed out. Try shortening your BRD or tech doc, then try again.";
      } else if (err.response) {
        // responseType:'blob' means the error body is also a Blob — parse it as text first
        try {
          const raw = await err.response.data.text();
          const json = JSON.parse(raw);
          message = `Pipeline error (${err.response.status}): ${json.detail ?? raw.slice(0, 300)}`;
        } catch {
          message = `Pipeline error (${err.response.status}): ${err.message}`;
        }
      } else if (err.request) {
        message =
          "Could not reach the backend. Make sure the API server is running on port 8000.";
      }

      setGenerateError(message);
    } finally {
      setIsGenerating(false);
    }
  };

  return { run };
}
