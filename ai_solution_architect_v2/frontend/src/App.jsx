// src/App.jsx
import { useAppStore } from "./store/useAppStore";
import Header from "./components/layout/Header";
import Footer from "./components/layout/Footer";
import InputModeToggle from "./components/input/InputModeToggle";
import TextInputPanel from "./components/input/TextInputPanel";
import FileUploadPanel from "./components/input/FileUploadPanel";
import SlideSelector from "./components/slides/SlideSelector";
import GenerateButton from "./components/generate/GenerateButton";
import DownloadBanner from "./components/result/DownloadBanner";
import Alert from "./components/ui/Alert";

export default function App() {
  const { inputMode, generateError, pptxBlob } = useAppStore();

  return (
    <div className="min-h-screen bg-brand-bg font-sans">
      <div className="max-w-[1100px] mx-auto px-4 sm:px-8 py-8 sm:py-10 pb-16">
        <Header />
        <InputModeToggle />
        <SlideSelector />

        <div className="mt-1">
          {inputMode === "paste" ? <TextInputPanel /> : <FileUploadPanel />}
        </div>

        <div className="mt-8">
          <GenerateButton />
        </div>

        {generateError && (
          <div className="mt-4 max-w-xl mx-auto">
            <Alert type="error" message={generateError} />
          </div>
        )}

        {pptxBlob && (
          <div className="mt-8">
            <DownloadBanner />
          </div>
        )}

        <Footer />
      </div>
    </div>
  );
}
