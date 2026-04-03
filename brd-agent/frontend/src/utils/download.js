/**
 * Force-downloads the BRD as a .docx file.
 * Uses fetch + blob so the browser never tries to open it inline.
 */
export async function downloadBRD(projectId, projectName) {
  const url = `/api/projects/${projectId}/download`;
  const res = await fetch(url);

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`Download failed: ${res.status} — ${text}`);
  }

  const blob = await res.blob();
  const objectUrl = URL.createObjectURL(blob);

  const a = document.createElement("a");
  a.href = objectUrl;
  const safeName = (projectName || "BRD").replace(/[^a-zA-Z0-9_\-]/g, "_");
  a.download = `BRD_${safeName}.docx`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(objectUrl);
}
