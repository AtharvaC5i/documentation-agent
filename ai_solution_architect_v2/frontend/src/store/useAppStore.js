// src/store/useAppStore.js
import { create } from "zustand";

const DEFAULT_SLIDES = [
  "Title",
  "ExecSummary",
  "Problem",
  "Solution",
  "Diagram",
  "Components",
  "DataFlow",
  "TechStack",
  "Features",
  "NFR",
  "Roadmap",
  "Risks",
  "Closing",
];

export const useAppStore = create((set) => ({
  inputMode: "paste", // 'paste' | 'upload'
  brdText: "",
  techDocText: "",
  brdExtracted: "",
  techDocExtracted: "",
  selectedSlides: [...DEFAULT_SLIDES],
  customSlidesRaw: "",
  pptxBlob: null,
  isGenerating: false,
  generateError: null,

  setInputMode: (mode) => set({ inputMode: mode }),
  setBrdText: (v) => set({ brdText: v }),
  setTechDocText: (v) => set({ techDocText: v }),
  setBrdExtracted: (v) => set({ brdExtracted: v }),
  setTechDocExtracted: (v) => set({ techDocExtracted: v }),
  toggleSlide: (key) =>
    set((s) => ({
      selectedSlides: s.selectedSlides.includes(key)
        ? s.selectedSlides.filter((k) => k !== key)
        : [...s.selectedSlides, key],
    })),
  setCustomSlidesRaw: (v) => set({ customSlidesRaw: v }),
  setPptxBlob: (blob) => set({ pptxBlob: blob }),
  setIsGenerating: (v) => set({ isGenerating: v }),
  setGenerateError: (msg) => set({ generateError: msg }),
  resetResult: () => set({ pptxBlob: null, generateError: null }),
}));
