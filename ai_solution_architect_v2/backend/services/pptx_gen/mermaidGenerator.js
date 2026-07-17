"use strict";

const LAYER_RULES = [
  { layer: "Client",   keywords: ["user", "client", "browser", "mobile", "web app", "end user"] },
  { layer: "Frontend", keywords: ["frontend", "react", "angular", "vue", "streamlit", "ui", "dashboard", "portal"] },
  { layer: "Backend",  keywords: ["backend", "api", "fastapi", "flask", "django", "express", "server", "service", "gateway", "rest"] },
  { layer: "AI/ML",    keywords: ["ai", "ml", "llm", "gpt", "claude", "databricks", "groq", "openai", "model", "inference", "raptor", "embedding", "nlp", "vector"] },
  { layer: "Data",     keywords: ["database", "db", "postgres", "mysql", "mongo", "redis", "chroma", "chromadb", "sqlite", "store", "storage", "cache", "queue", "kafka", "s3", "json"] },
  { layer: "External", keywords: ["external", "third", "github", "gitlab", "auth", "oauth", "stripe", "aws", "azure", "gcp"] },
];

const LAYER_STYLES = {
  "Client":   { fill: "1D4ED8", stroke: "2563EB", text: "FFFFFF" },
  "Frontend": { fill: "6D28D9", stroke: "7C3AED", text: "FFFFFF" },
  "Backend":  { fill: "047857", stroke: "059669", text: "FFFFFF" },
  "AI/ML":    { fill: "B45309", stroke: "D97706", text: "FFFFFF" },
  "Data":     { fill: "9D174D", stroke: "DB2777", text: "FFFFFF" },
  "External": { fill: "475569", stroke: "64748B", text: "FFFFFF" },
};

function generateMermaidCode(data) {
  const arch = data.architecture || {};
  const rawC = arch.diagram_components || arch.components || [];
  const rawE = arch.diagram_connections || arch.connections || [];

  console.error("[mermaidGenerator] Input components:", rawC.length);
  console.error("[mermaidGenerator] Input connections:", rawE.length);

  if (!rawC.length) {
    console.error("[mermaidGenerator] No components found, using fallback...");
    return _fallbackCode(arch);
  }

  const components = rawC.map(c => ({
    id:    _safeId(c.id || c.name || String(Math.random())),
    label: (c.label || c.name || c.id || "").replace(/\\n/g, " ").substring(0, 36),
    tech:  (c.technology || "").substring(0, 22),
    desc:  (c.description || c.summary || "").replace(/\\n/g, " ").substring(0, 40),
  }));
  components.forEach(c => { c.layer = _detectLayer(c.label + " " + c.tech); });

  console.error("[mermaidGenerator] ✓ Component mapping:");
  components.forEach(c => {
    console.error(`  - "${c.label}" (tech:"${c.tech}") → layer:"${c.layer}"`);
  });

  const layerOrder = ["Client","Frontend","Backend","AI/ML","Data","External"];
  const byLayer = {};
  layerOrder.forEach(l => { byLayer[l] = []; });
  components.forEach(c => { (byLayer[c.layer] = byLayer[c.layer] || []).push(c); });

  const usedLayers = layerOrder.filter(l => byLayer[l] && byLayer[l].length > 0);
  console.error("[mermaidGenerator] Used layers:", usedLayers.length, usedLayers);

  let code = "graph LR\n";

  // Add subgraphs for layers
  usedLayers.forEach(layer => {
    const cls = _getClassName(layer);
    code += `  subgraph ${cls} [${layer}]\n`;
    byLayer[layer].forEach(c => {
      let nodeLabel = `<b>${_esc(c.label)}</b>`;
      if (c.tech) {
        nodeLabel += `<br/><i>${_esc(c.tech)}</i>`;
      }
      code += `    ${c.id}["${nodeLabel}"]:::${cls}\n`;
    });
    code += "  end\n";
  });

  // Add connections
  rawE.forEach(conn => {
    const s = _safeId(conn.from);
    const t = _safeId(conn.to);
    if (!components.some(c => c.id === s) || !components.some(c => c.id === t)) {
      console.error(`[mermaidGenerator] Warning: skipping edge ${conn.from} -> ${conn.to} (nodes not found)`);
      return;
    }
    const label = conn.label ? String(conn.label).replace(/[^a-zA-Z0-9\s_.\-\/]/g, "").substring(0, 25) : "";
    if (label) {
      code += `  ${s} -->|"${label}"| ${t}\n`;
    } else {
      code += `  ${s} --> ${t}\n`;
    }
  });

  // Add classDefs
  Object.entries(LAYER_STYLES).forEach(([layer, s]) => {
    const cls = _getClassName(layer);
    code += `  classDef ${cls} fill:#${s.fill},stroke:#${s.stroke},stroke-width:2px,color:#${s.text};\n`;
  });

  return code;
}

function _fallbackCode(arch) {
  const pairs = [
    { id:"client",   label:"User / Client",          layer:"Client"   },
    { id:"frontend", label:arch.frontend||"Frontend", layer:"Frontend" },
    { id:"backend",  label:arch.backend||"Backend",   layer:"Backend"  },
    { id:"ai",       label:arch.ai_layer||"AI Layer",  layer:"AI/ML"   },
    { id:"data",     label:arch.data_store||"Data",    layer:"Data"    },
  ].filter(n => n.label);
  const conns = pairs.slice(0,-1).map((p,i)=>({ from:p.id, to:pairs[i+1].id, label:"" }));
  return generateMermaidCode({ architecture:{ diagram_components:pairs, diagram_connections:conns } });
}

function _detectLayer(text) {
  const lower = (text||"").toLowerCase();
  for (const { layer, keywords } of LAYER_RULES) {
    if (keywords.some(k => lower.includes(k))) return layer;
  }
  return "Backend";
}

function _safeId(str) { return String(str).replace(/[^a-zA-Z0-9_-]/g,"_").toLowerCase(); }
function _getClassName(layer) { return layer.replace(/[^a-zA-Z0-9]/g, ""); }
function _esc(str) {
  return String(str)
    .replace(/&/g,"&amp;")
    .replace(/</g,"&lt;")
    .replace(/>/g,"&gt;")
    .replace(/"/g,"&quot;")
    .replace(/'/g,"&#39;");
}

module.exports = { generateMermaidCode };
