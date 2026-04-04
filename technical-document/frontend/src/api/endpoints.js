import client from "./client";

// ── Health ───────────────────────────────────────────────────────────────────
export const checkHealth = () => client.get("/health");

// ── Phase 1: Ingest ──────────────────────────────────────────────────────────
export const ingestGithub = (payload) => client.post("/ingest/github", payload);

export const ingestZip = (formData) =>
  client.post("/ingest/zip", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });

// ── Phase 2: Sections ────────────────────────────────────────────────────────
export const getSuggestions = (projectId) =>
  client.get(`/sections/suggest/${projectId}`);

export const confirmSections = (payload) =>
  client.post("/sections/confirm", payload);

// ── Phase 3: Context ─────────────────────────────────────────────────────────
export const buildContext = (projectId) =>
  client.post("/context/build", { project_id: projectId });

// ── Phase 4: Generation ──────────────────────────────────────────────────────
export const startGeneration = (projectId) =>
  client.post(`/generate/start/${projectId}`);

export const getGenerationStatus = (projectId) =>
  client.get(`/generate/status/${projectId}`);

export const getGenerationResults = (projectId) =>
  client.get(`/generate/results/${projectId}`);

// ── Phase 5: Review ──────────────────────────────────────────────────────────
export const initReview = (projectId, sections) =>
  client.post(`/review/${projectId}/init`, { sections });

export const getReviewState = (projectId) => client.get(`/review/${projectId}`);

export const submitDecision = (projectId, payload) =>
  client.post(`/review/${projectId}/decide`, payload);

export const regenerateSection = (projectId, sectionName) =>
  client.post(`/review/${projectId}/regenerate`, { section_name: sectionName });

// ── Phase 6: Assembly ────────────────────────────────────────────────────────
export const assembleDocument = (projectId, payload) =>
  client.post(`/api/assemble/${projectId}`, payload); // ✅ /api prefix required

export const downloadDocument = (projectId) =>
  client.get(`/api/assemble/${projectId}/download`, {
    responseType: "arraybuffer",
  });

// ── Phase 7: Publish ─────────────────────────────────────────────────────────
export const sendEmail = (projectId, payload) =>
  client.post(`/publish/${projectId}/email`, payload);

export const getPublishStatus = (projectId) =>
  client.get(`/publish/${projectId}/status`);

// ── Phase 8: Report ──────────────────────────────────────────────────────────
export const getReport = (projectId, metadata) =>
  client.post(`/report/${projectId}`, { metadata });

export const exportReport = (projectId, metadata) =>
  client.post(
    `/report/${projectId}/export`,
    { metadata },
    { responseType: "blob" },
  );
