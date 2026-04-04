import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { AppProvider } from "./context/AppContext";
import TopBar from "./components/layout/TopBar"; // ✅ fixed casing
import Stepper from "./components/layout/Stepper";
import IngestPage from "./pages/IngestPage";
import SectionsPage from "./pages/SectionsPage";
import ContextPage from "./pages/ContextPage";
import GeneratePage from "./pages/GeneratePage";
import ReviewPage from "./pages/ReviewPage";
import AssemblyPage from "./pages/AssemblyPage";
import ReportPage from "./pages/ReportPage";

function Layout({ children }) {
  return (
    <div className="min-h-screen bg-[#fafafa] flex flex-col">
      <TopBar />
      <Stepper />
      <main className="flex-1 max-w-[1024px] w-full mx-auto px-6 py-8">
        {" "}
        {/* ✅ 1024 not 1100 */}
        {children}
      </main>
    </div>
  );
}

export default function App() {
  return (
    <AppProvider>
      <HashRouter>
        <Routes>
          <Route path="/" element={<Navigate to="/ingest" replace />} />
          <Route
            path="/ingest"
            element={
              <Layout>
                <IngestPage />
              </Layout>
            }
          />
          <Route
            path="/project/:id/sections"
            element={
              <Layout>
                <SectionsPage />
              </Layout>
            }
          />
          <Route
            path="/project/:id/context"
            element={
              <Layout>
                <ContextPage />
              </Layout>
            }
          />
          <Route
            path="/project/:id/generate"
            element={
              <Layout>
                <GeneratePage />
              </Layout>
            }
          />
          <Route
            path="/project/:id/review"
            element={
              <Layout>
                <ReviewPage />
              </Layout>
            }
          />
          <Route
            path="/project/:id/assembly"
            element={
              <Layout>
                <AssemblyPage />
              </Layout>
            }
          />
          <Route
            path="/project/:id/report"
            element={
              <Layout>
                <ReportPage />
              </Layout>
            }
          />
        </Routes>
      </HashRouter>
    </AppProvider>
  );
}
