import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import QuestionBank from "./pages/QuestionBank";
import NewProject from "./pages/NewProject";
import Upload from "./pages/Upload";
import Extraction from "./pages/Extraction";
import PipelineNavigator from "./pages/PipelineNavigator";
import ConflictResolution from "./pages/ConflictResolution";
import SectionSelection from "./pages/SectionSelection";
import Generation from "./pages/Generation";
import Review from "./pages/Review";
import Complete from "./pages/Complete";
import FollowupEmail from "./pages/FollowupEmail";
import LivingBRD from "./pages/LivingBRD";
import Traceability from "./pages/Traceability";
import "./index.css";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<Home />} />
          <Route path="question-bank" element={<QuestionBank />} />
          <Route path="new-project" element={<NewProject />} />
          <Route path="project/:projectId/upload" element={<Upload />} />
          <Route path="project/:projectId/extraction" element={<Extraction />} />
          <Route path="project/:projectId/pipeline" element={<PipelineNavigator />} />
          <Route path="project/:projectId/conflicts" element={<ConflictResolution />} />
          <Route path="project/:projectId/sections" element={<SectionSelection />} />
          <Route path="project/:projectId/generation" element={<Generation />} />
          <Route path="project/:projectId/review" element={<Review />} />
          <Route path="project/:projectId/complete" element={<Complete />} />
          <Route path="project/:projectId/followup-email" element={<FollowupEmail />} />
          <Route path="project/:projectId/living-brd" element={<LivingBRD />} />
          <Route path="project/:projectId/traceability" element={<Traceability />} />
          <Route path="*" element={<Navigate to="/" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
