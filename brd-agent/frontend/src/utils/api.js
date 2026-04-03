import axios from "axios";

const API = axios.create({ baseURL: "/api" });

// ── Core project routes ────────────────────────────────────────────────────
export const getQuestionBank       = () => API.get("/question-bank");
export const createProject         = (data) => API.post("/projects/create", data);
export const listProjects          = () => API.get("/projects");
export const getProjectStatus      = (id) => API.get(`/projects/${id}/status`);

// ── Upload ─────────────────────────────────────────────────────────────────
export const loadSynthetic = (id) => API.post(`/projects/${id}/load-synthetic`);
export const uploadTranscript = (id, file) => {
  const fd = new FormData(); fd.append("file", file);
  return API.post(`/projects/${id}/upload-transcript`, fd);
};
export const uploadUserStories = (id, file) => {
  const fd = new FormData(); fd.append("file", file);
  return API.post(`/projects/${id}/upload-user-stories`, fd);
};

// ── Extraction ─────────────────────────────────────────────────────────────
export const startExtraction       = (id) => API.post(`/projects/${id}/extract`);
export const getRequirements       = (id) => API.get(`/projects/${id}/requirements`);
export const getConflicts          = (id) => API.get(`/projects/${id}/conflicts`);
export const resolveConflict       = (data) => API.post(`/projects/${data.project_id}/resolve-conflict`, data);

// ── Section management ─────────────────────────────────────────────────────
export const getSuggestedSections  = (id) => API.get(`/projects/${id}/suggested-sections`);
export const selectSections        = (data) => API.post(`/projects/${data.project_id}/select-sections`, data);
export const getSections           = (id) => API.get(`/projects/${id}/sections`);
export const approveSection        = (data) => API.post(`/projects/${data.project_id}/approve-section`, data);
export const regenerateSection     = (data) => API.post(`/projects/${data.project_id}/regenerate-section`, data);

// ── Document ───────────────────────────────────────────────────────────────
export const generateDocument      = (id) => API.post(`/projects/${id}/generate-document`);

// ── Follow-up email ────────────────────────────────────────────────────────
export const generateFollowupEmail = (id) => API.post(`/projects/${id}/generate-followup-email`);
export const getFollowupEmail      = (id) => API.get(`/projects/${id}/followup-email`);

// ── Living BRD ─────────────────────────────────────────────────────────────
export const uploadNewTranscript = (id, file) => {
  const fd = new FormData(); fd.append("file", file);
  return API.post(`/projects/${id}/upload-new-transcript`, fd);
};
export const getChanges            = (id) => API.get(`/projects/${id}/changes`);
export const applyChanges          = (data) => API.post(`/projects/${data.project_id}/apply-changes`, data);
export const getVersionHistory     = (id) => API.get(`/projects/${id}/version-history`);

// ── Traceability ───────────────────────────────────────────────────────────
export const generateTraceability  = (id) => API.post(`/projects/${id}/generate-traceability`);
export const getTraceability       = (id) => API.get(`/projects/${id}/traceability`);

// ── Downloads — blob fetch so browser always saves as .docx ───────────────
async function _blobDownload(url, filename) {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);
  const blob = await res.blob();
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(a.href);
}

export const downloadBRD = (id, projectName, version = 1) =>
  _blobDownload(
    `/api/projects/${id}/download`,
    `BRD_${(projectName || "document").replace(/\s+/g, "_")}_v${version}.docx`
  );

export const downloadTraceability = (id, projectName, version = 1) =>
  _blobDownload(
    `/api/projects/${id}/download-traceability`,
    `Traceability_${(projectName || "document").replace(/\s+/g, "_")}_v${version}.docx`
  );

export default API;
