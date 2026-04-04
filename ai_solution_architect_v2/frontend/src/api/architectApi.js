// src/api/architectApi.js
import axios from "axios";

const BASE = import.meta.env.VITE_ARCHITECT_API_URL ?? "/api/v1";

export const extractText = (file) => {
  const fd = new FormData();
  fd.append("file", file, file.name);
  return axios.post(`${BASE}/extract-text`, fd, { timeout: 60_000 });
};

export const generatePptx = ({
  brdText,
  techDocText,
  selectedSlides,
  customSlidesRaw,
}) => {
  const fd = new FormData();
  fd.append("brd_text", brdText);
  fd.append("tech_doc_text", techDocText);
  fd.append("selected_slides", JSON.stringify(selectedSlides));
  fd.append("custom_slides", customSlidesRaw ?? "");
  return axios.post(`${BASE}/generate-pptx`, fd, {
    responseType: "blob", // critical — binary PPTX response
    timeout: 360_000,
  });
};
