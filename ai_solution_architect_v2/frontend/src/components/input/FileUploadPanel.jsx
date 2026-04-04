// src/components/input/FileUploadPanel.jsx
import { useAppStore } from "../../store/useAppStore";
import SingleFileUploader from "./SingleFileUploader";

export default function FileUploadPanel() {
  const { setBrdExtracted, setTechDocExtracted } = useAppStore();

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
      <SingleFileUploader
        label="BRD File"
        onExtracted={setBrdExtracted}
        onCleared={() => setBrdExtracted("")}
      />
      <SingleFileUploader
        label="Technical Documentation"
        optional
        onExtracted={setTechDocExtracted}
        onCleared={() => setTechDocExtracted("")}
      />
    </div>
  );
}
