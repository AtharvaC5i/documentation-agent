// src/hooks/useGenerationPoller.js

import { useState, useEffect, useRef } from "react";
import { getGenerationStatus, getGenerationResults } from "../api/endpoints";

function inferStatus(s) {
  // If backend explicitly gives a real status, use it
  const raw = String(s.status ?? "")
    .toLowerCase()
    .replace(/[_\-\s]/g, "");
  if (["success", "completed", "done", "complete"].includes(raw))
    return "success";
  if (["lowquality", "low", "belowthreshold"].includes(raw))
    return "lowquality";
  if (["failed", "error", "failure"].includes(raw)) return "failed";
  if (["inprogress", "generating", "running", "processing"].includes(raw))
    return "inprogress";

  // ── Backend returned "pending" but section is actually done ──
  // Infer from the data itself
  if (s.content && s.content.trim().length > 0) {
    const score = s.quality_score ?? s.qualityScore ?? null;
    if (score !== null) {
      return score >= 0.5 ? "success" : "lowquality";
    }
    return "success"; // has content but no score — treat as done
  }

  return "pending";
}

export function useGenerationPoller(projectId, enabled) {
  const [status, setStatus] = useState(null);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!projectId || !enabled) return;

    const poll = async () => {
      try {
        const { data } = await getGenerationStatus(projectId);
        setStatus(data);

        if (data.finished) {
          clearInterval(intervalRef.current);
          try {
            const { data: res } = await getGenerationResults(projectId);
            const rawSections = res.sections ?? res.results ?? [];
            const sections = rawSections.map((s) => ({
              name: s.name,
              content: s.content ?? "",
              order: s.order ?? 0,
              quality_score: s.quality_score ?? s.qualityScore ?? null,
              status: inferStatus(s), // ← infer, don't trust backend field
              regenerated: s.regenerated ?? false,
            }));
            setResults(sections);
          } catch (e) {
            setError(e.message);
          }
        }
      } catch (e) {
        setError(e.message);
        clearInterval(intervalRef.current);
      }
    };

    poll();
    intervalRef.current = setInterval(poll, 3_000);
    return () => clearInterval(intervalRef.current);
  }, [projectId, enabled]);

  return { status, results, error };
}
