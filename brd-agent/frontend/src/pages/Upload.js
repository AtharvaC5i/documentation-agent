import React, { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { Upload as UploadIcon, FileText, Zap, CheckCircle } from "lucide-react";
import { uploadTranscript, uploadUserStories, loadSynthetic, startExtraction } from "../utils/api";
import StepIndicator from "../components/StepIndicator";

export default function Upload() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [transcript, setTranscript] = useState(null);
  const [stories, setStories] = useState(null);
  const [loading, setLoading] = useState(false);
  const [useSynthetic, setUseSynthetic] = useState(false);
  const [error, setError] = useState("");

  const handleFile = (setter) => (e) => setter(e.target.files[0]);

  const handleStart = async () => {
    setLoading(true); setError("");
    try {
      if (useSynthetic) {
        await loadSynthetic(projectId);
      } else {
        if (!transcript && !stories) { setError("Upload at least one file or use synthetic data."); setLoading(false); return; }
        if (transcript) await uploadTranscript(projectId, transcript);
        if (stories) await uploadUserStories(projectId, stories);
      }
      await startExtraction(projectId);
      navigate(`/project/${projectId}/extraction`);
    } catch (e) {
      setError("Upload failed. Check that the backend is running.");
      setLoading(false);
    }
  };

  return (
    <div style={{ maxWidth: 680 }}>
      <StepIndicator current="upload" />
      <div className="page-header">
        <h2>Upload Project Inputs</h2>
        <p>Upload meeting transcripts and/or user stories. Both are optional individually.</p>
      </div>

      {error && <div className="alert alert-error mb-4">{error}</div>}

      {/* Synthetic data option */}
      <div className="card mb-4" style={{ border: useSynthetic ? "1.5px solid #2563eb" : undefined, cursor: "pointer" }} onClick={() => setUseSynthetic(!useSynthetic)}>
        <div className="flex items-center gap-3">
          <input type="checkbox" checked={useSynthetic} onChange={() => {}} style={{ width: 17, height: 17, accentColor: "#2563eb" }} />
          <div>
            <div className="font-semibold flex items-center gap-2"><Zap size={15} color="#2563eb" /> Use Synthetic Data (Demo)</div>
            <div className="text-sm text-muted mt-1">Use our pre-built ShopEase e-commerce project — complete transcript and 25 user stories. Best for testing the pipeline end-to-end.</div>
          </div>
        </div>
      </div>

      {!useSynthetic && (
        <div className="grid-2 mb-4">
          {/* Transcript upload */}
          <div className="card">
            <div className="card-title mb-1">Meeting Transcript</div>
            <div className="text-xs text-muted mb-3">.txt, .docx, or .pdf</div>
            <label className={`upload-zone${transcript ? " drag" : ""}`} style={{ display: "block" }}>
              <input type="file" accept=".txt,.docx,.pdf" style={{ display: "none" }} onChange={handleFile(setTranscript)} />
              {transcript ? (
                <div className="flex items-center gap-2" style={{ justifyContent: "center" }}>
                  <CheckCircle size={18} color="#10b981" />
                  <span className="text-sm font-semibold" style={{ color: "#059669" }}>{transcript.name}</span>
                </div>
              ) : (
                <>
                  <UploadIcon size={28} style={{ margin: "0 auto 8px" }} />
                  <div className="text-sm font-semibold">Click to upload transcript</div>
                  <div className="text-xs text-muted mt-1">or drag & drop</div>
                </>
              )}
            </label>
          </div>

          {/* User stories upload */}
          <div className="card">
            <div className="card-title mb-1">User Stories</div>
            <div className="text-xs text-muted mb-3">.txt, .csv, or .docx</div>
            <label className={`upload-zone${stories ? " drag" : ""}`} style={{ display: "block" }}>
              <input type="file" accept=".txt,.csv,.docx" style={{ display: "none" }} onChange={handleFile(setStories)} />
              {stories ? (
                <div className="flex items-center gap-2" style={{ justifyContent: "center" }}>
                  <CheckCircle size={18} color="#10b981" />
                  <span className="text-sm font-semibold" style={{ color: "#059669" }}>{stories.name}</span>
                </div>
              ) : (
                <>
                  <FileText size={28} style={{ margin: "0 auto 8px" }} />
                  <div className="text-sm font-semibold">Click to upload user stories</div>
                  <div className="text-xs text-muted mt-1">Jira export or plain text</div>
                </>
              )}
            </label>
          </div>
        </div>
      )}

      <div className="alert alert-info mb-6">
        <FileText size={15} style={{ flexShrink: 0, marginTop: 2 }} />
        <div className="text-sm">Inputs are processed entirely on your server. Files are never sent to third parties — only the extracted text chunks reach the Databricks LLM endpoint.</div>
      </div>

      <button className="btn btn-primary btn-lg" onClick={handleStart} disabled={loading}>
        {loading ? <><div className="spinner" style={{ width: 16, height: 16 }} /> Starting...</> : "Start Extraction →"}
      </button>
    </div>
  );
}
