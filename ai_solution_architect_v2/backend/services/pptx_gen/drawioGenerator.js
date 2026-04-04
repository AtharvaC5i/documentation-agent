"use strict";

/**
 * drawioGenerator.js — Professional architecture diagram builder
 *
 * Reads: architecture.diagram_components + architecture.diagram_connections
 * Falls back to: architecture.components + architecture.connections
 *
 * Output: draw.io XML with swimlane layers, coloured nodes, labelled edges
 */

const LAYER_RULES = [
  { layer: "Client",   keywords: ["user", "client", "browser", "mobile", "web app", "end user"] },
  { layer: "Frontend", keywords: ["frontend", "react", "angular", "vue", "streamlit", "ui", "dashboard", "portal"] },
  { layer: "Backend",  keywords: ["backend", "api", "fastapi", "flask", "django", "express", "server", "service", "gateway", "rest"] },
  { layer: "AI/ML",    keywords: ["ai", "ml", "llm", "gpt", "claude", "databricks", "groq", "openai", "model", "inference", "raptor", "embedding", "nlp", "vector"] },
  { layer: "Data",     keywords: ["database", "db", "postgres", "mysql", "mongo", "redis", "chroma", "chromadb", "sqlite", "store", "storage", "cache", "queue", "kafka", "s3", "json"] },
  { layer: "External", keywords: ["external", "third", "github", "gitlab", "auth", "oauth", "stripe", "aws", "azure", "gcp"] },
];

const LAYER_STYLES = {
  "Client":   { fill: "DBEAFE", stroke: "2563EB", header: "1D4ED8", text: "FFFFFF" },
  "Frontend": { fill: "EDE9FE", stroke: "7C3AED", header: "6D28D9", text: "FFFFFF" },
  "Backend":  { fill: "D1FAE5", stroke: "059669", header: "047857", text: "FFFFFF" },
  "AI/ML":    { fill: "FEF3C7", stroke: "D97706", header: "B45309", text: "FFFFFF" },
  "Data":     { fill: "FCE7F3", stroke: "DB2777", header: "9D174D", text: "FFFFFF" },
  "External": { fill: "F1F5F9", stroke: "64748B", header: "475569", text: "FFFFFF" },
};

const CANVAS_W   = 1400;
const CANVAS_H   = 780;
const MARGIN     = 36;
const NODE_W     = 148;
const NODE_H     = 52;
const COL_GAP    = 56;
const ROW_GAP    = 18;
const LANE_PAD_X = 16;
const LANE_PAD_T = 36;
const LANE_PAD_B = 16;

function generateDrawioXml(data) {
  const arch = data.architecture || {};
  const rawC = arch.diagram_components || arch.components || [];
  const rawE = arch.diagram_connections || arch.connections || [];

  console.error("[drawioGenerator] Input components:", rawC.length);
  console.error("[drawioGenerator] Input connections:", rawE.length);

  if (!rawC.length) {
    console.error("[drawioGenerator] No components found, using fallback...");
    return _fallbackXml(arch);
  }

  const components = rawC.map(c => ({
    id:    _safeId(c.id || c.name || String(Math.random())),
    label: (c.label || c.name || c.id || "").replace(/\\n/g, "\n").substring(0, 36),
    tech:  (c.technology || "").substring(0, 22),
    desc:  (c.description || c.summary || "").replace(/\\n/g, " ").substring(0, 40),
  }));
  components.forEach(c => { c.layer = _detectLayer(c.label + " " + c.tech); });

  console.error("[drawioGenerator] ✓ Component mapping:");
  components.forEach(c => {
    console.error(`  - "${c.label}" (tech:"${c.tech}") → layer:"${c.layer}"`);
  });

  console.error("[drawioGenerator] Components by layer:");
  const layerOrder = ["Client","Frontend","Backend","AI/ML","Data","External"];
  const byLayer = {};
  layerOrder.forEach(l => { byLayer[l] = []; });
  components.forEach(c => { (byLayer[c.layer] = byLayer[c.layer] || []).push(c); });

  layerOrder.forEach(l => {
    if (byLayer[l].length > 0) {
      console.error(`  ${l}: ${byLayer[l].length} (${byLayer[l].map(c => c.label).join(", ")})`);
    }
  });

  const usedLayers = layerOrder.filter(l => byLayer[l] && byLayer[l].length > 0);
  console.error("[drawioGenerator] Used layers:", usedLayers.length, usedLayers);
  
  if (usedLayers.length === 0) {
    console.error("[drawioGenerator] ERROR: No layers detected! Using fallback...");
    return _fallbackXml(arch);
  }
  
  const numCols = usedLayers.length;
  const colW = Math.floor((CANVAS_W - MARGIN * 2 - COL_GAP * (numCols - 1)) / numCols);
  const nodeW = Math.max(colW - LANE_PAD_X * 2, 120);

  const maxNodes = Math.max(...usedLayers.map(l => byLayer[l].length));
  const laneH = LANE_PAD_T + Math.max(maxNodes, 2) * (NODE_H + ROW_GAP) + LANE_PAD_B;

  console.error("[drawioGenerator] Canvas: max nodes per layer =", maxNodes, "lane height =", laneH);

  let cellId = 2;
  const idMap = {};
  components.forEach(c => { idMap[c.id] = cellId++; });

  const laneIdMap = {};
  usedLayers.forEach(l => { laneIdMap[l] = cellId++; });

  const cells = [];

  usedLayers.forEach((layer, i) => {
    const s   = LAYER_STYLES[layer] || LAYER_STYLES["External"];
    const lx  = MARGIN + i * (colW + COL_GAP);
    const lid = laneIdMap[layer];

    cells.push(
      `<mxCell id="${lid}" value="${_esc(layer)}" style="` +
      `swimlane;startSize=32;horizontal=1;fillColor=#${s.fill};` +
      `strokeColor=#${s.stroke};strokeWidth=2.5;fontColor=#${s.header};` +
      `fontSize=13;fontStyle=1;swimlaneLine=1;rounded=1;arcSize=8;shadow=1;align=center;verticalAlign=top;" ` +
      `vertex="1" parent="1">` +
      `<mxGeometry x="${lx}" y="${MARGIN}" width="${colW}" height="${laneH}" as="geometry"/>` +
      `</mxCell>`
    );

    byLayer[layer].forEach((c, j) => {
      const nid = idMap[c.id];
      const rx  = LANE_PAD_X;
      const ry  = LANE_PAD_T + j * (NODE_H + ROW_GAP);
      const meta = [];
      if (c.tech) meta.push(c.tech);
      if (c.desc) meta.push(c.desc);
      const metaHtml = meta.length ? `<br/><font style="font-size:8px;font-weight:normal;">${_esc(meta.join(' • '))}</font>` : '';
      const val = `${_esc(c.label)}${metaHtml}`;

      cells.push(
        `<mxCell id="${nid}" value="${_esc(val)}" style="` +
        `rounded=1;arcSize=24;whiteSpace=wrap;html=1;` +
        `fillColor=#${s.header};strokeColor=#${s.stroke};` +
        `fontColor=#${s.text};fontSize=11;fontStyle=1;align=center;verticalAlign=middle;` +
        `shadow=1;glass=0;separatorColor=#${s.stroke};" ` +
        `vertex="1" parent="${lid}">` +
        `<mxGeometry x="${rx}" y="${ry}" width="${nodeW}" height="${NODE_H}" as="geometry"/>` +
        `</mxCell>`
      );
    });
  });

  rawE.forEach((conn, idx) => {
    const s = _safeId(conn.from);
    const t = _safeId(conn.to);
    const sc = idMap[s];
    const tc = idMap[t];
    if (!sc || !tc) {
      console.error(`[drawioGenerator] Warning: skipping edge ${conn.from} -> ${conn.to} (nodes not found)`);
      return;
    }
    const eid = cellId++;
    const label = conn.label ? _esc(conn.label).substring(0, 25) : "";
    cells.push(
      `<mxCell id="${eid}" value="${label}" style="` +
      `edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;` +
      `exitX=1;exitY=0.5;exitDx=0;exitDy=0;entryX=0;entryY=0.5;entryDx=0;entryDy=0;` +
      `strokeColor=#475569;strokeWidth=2;fontSize=9;fontColor=#334155;` +
      `endArrow=block;endFill=1;curved=0;" ` +
      `edge="1" source="${sc}" target="${tc}" parent="1">` +
      `<mxGeometry relative="1" as="geometry"/>` +
      `</mxCell>`
    );
  });

  console.error("[drawioGenerator] Generated cells:", cells.length);
  if (cells.length === 0) {
    console.error("[drawioGenerator] CRITICAL: No cells generated! Components might be undetected.");
  }
  const xml = _wrap(cells);
  console.error("[drawioGenerator] XML size:", xml.length);
  if (xml.length < 500) {
    console.error("[drawioGenerator] WARNING: XML is suspiciously small - diagram may not render!");
  }
  return xml;
}

function _fallbackXml(arch) {
  const pairs = [
    { id:"client",   label:"User / Client",          layer:"Client"   },
    { id:"frontend", label:arch.frontend||"Frontend", layer:"Frontend" },
    { id:"backend",  label:arch.backend||"Backend",   layer:"Backend"  },
    { id:"ai",       label:arch.ai_layer||"AI Layer",  layer:"AI/ML"   },
    { id:"data",     label:arch.data_store||"Data",    layer:"Data"    },
  ].filter(n => n.label);
  const conns = pairs.slice(0,-1).map((p,i)=>({ from:p.id, to:pairs[i+1].id, label:"" }));
  return generateDrawioXml({ architecture:{ diagram_components:pairs, diagram_connections:conns } });
}

function _wrap(cells) {
  return `<mxGraphModel dx="1422" dy="762" grid="0" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="${CANVAS_W}" pageHeight="${CANVAS_H}" math="0" shadow="1"><root><mxCell id="0"/><mxCell id="1" parent="0"/>${cells.join("")}</root></mxGraphModel>`;
}

function _detectLayer(text) {
  const lower = (text||"").toLowerCase();
  for (const { layer, keywords } of LAYER_RULES) {
    if (keywords.some(k => lower.includes(k))) return layer;
  }
  return "Backend";
}

function _safeId(str) { return String(str).replace(/[^a-zA-Z0-9_-]/g,"_").toLowerCase(); }
function _esc(str) {
  return String(str).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;").replace(/"/g,"&quot;");
}

module.exports = { generateDrawioXml };