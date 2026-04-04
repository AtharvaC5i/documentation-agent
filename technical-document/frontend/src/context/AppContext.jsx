import { createContext, useContext, useReducer } from "react";

const initialState = {
  projectId: null,
  metadata: {},
  analysis: null,
  filteredFileCount: 0,
  confirmedSections: [],
  sectionOrder: [],
  contextResult: null,
  generationStarted: false,
  generationFinished: false,
  generationResults: [],
  reviewDecisions: {},
  assemblyResult: null,
};

function reducer(state, action) {
  switch (action.type) {
    case "SET_PROJECT":
      return {
        ...state,
        projectId: action.payload.projectId,
        metadata: action.payload.metadata,
        analysis: action.payload.analysis,
        filteredFileCount: action.payload.filteredFileCount ?? 0,
      };
    case "SET_SECTIONS":
      return {
        ...state,
        confirmedSections: action.payload.confirmedSections,
        sectionOrder: action.payload.confirmedSections,
      };
    case "SET_CONTEXT_RESULT":
      return { ...state, contextResult: action.payload };
    case "SET_GENERATION_STARTED":
      return { ...state, generationStarted: true };
    case "SET_GENERATION_FINISHED": {
      const results = (action.payload.results ?? []).map((s) => ({
        ...s,
        status: ["success", "lowquality", "failed", "pending"].includes(
          s.status,
        )
          ? s.status
          : "success",
      }));
      return {
        ...state,
        generationFinished: true,
        generationResults: results,
        sectionOrder: [...results]
          .sort((a, b) => (a.order ?? 0) - (b.order ?? 0))
          .map((s) => s.name),
      };
    }
    case "SET_REVIEW_DECISION":
      return {
        ...state,
        reviewDecisions: {
          ...state.reviewDecisions,
          [action.payload.sectionName]: action.payload.decision,
        },
      };
    case "SET_SECTION_ORDER":
      return { ...state, sectionOrder: action.payload };
    case "SET_ASSEMBLY_RESULT":
      return { ...state, assemblyResult: action.payload };
    case "RESET":
      return initialState;
    default:
      return state;
  }
}

const AppContext = createContext(null);

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(reducer, initialState);

  const resetProject = () => dispatch({ type: "RESET" });

  return (
    <AppContext.Provider value={{ state, dispatch, resetProject }}>
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error("useApp must be used inside AppProvider");
  return ctx;
}
