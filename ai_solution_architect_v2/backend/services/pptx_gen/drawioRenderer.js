"use strict";

/**
 * drawioRenderer.js
 *
 * Renders draw.io XML → PNG via Puppeteer.
 * Uses a self-contained SVG renderer that reads the mxGraphModel XML
 * and draws swimlanes + nodes + edges entirely locally.
 */

const puppeteer = require("puppeteer");

async function renderDrawioToPng(drawioXml, opts = {}) {
  if (!drawioXml || !drawioXml.trim())
    throw new Error("drawioRenderer: empty XML");

  console.error("[drawioRenderer] Starting render...");
  console.error("[drawioRenderer] XML length:", drawioXml.length);

  const vpW = opts.width  || 1400;
  const vpH = opts.height || 850;
  const tmo = opts.timeout || 60000;

  let browser;
  try {
    browser = await puppeteer.launch({
      headless: "new",
      args: ["--no-sandbox","--disable-setuid-sandbox","--disable-dev-shm-usage","--disable-gpu"],
    });
    const page = await browser.newPage();
    await page.setViewport({ width: vpW, height: vpH, deviceScaleFactor: 1.5 });
    
    // Capture ALL console messages
    const pageLogs = [];
    page.on("console", msg => {
      const text = msg.text();
      pageLogs.push(text);
      console.error("[PAGE]", text);
    });
    page.on("error", err => console.error("[PAGE ERROR]", err));
    page.on("pageerror", err => console.error("[PAGE UNCAUGHT]", err));

    const html = _buildHtml(drawioXml);
    console.error("[drawioRenderer] HTML built, length:", html.length);
    
    await page.setContent(html, { waitUntil: "networkidle0", timeout: tmo });
    console.error("[drawioRenderer] Content set, waiting for script to populate SVG...");
    
    // Wait for SVG to be populated (not just diagram-ready)
    await page.waitForFunction(() => {
      const svg = document.getElementById("main-svg");
      return svg && svg.children && svg.children.length > 0;
    }, { timeout: tmo }).catch(err => {
      console.error("[drawioRenderer] WARNING: SVG population timeout");
    });
    
    await _delay(1000);
    console.error("[drawioRenderer] Delay complete, checking SVG state...");

    const el = await page.$("#diagram-wrap");
    if (!el) throw new Error("drawioRenderer: #diagram-wrap not found");

    // Check SVG content with FULL diagnostics
    const svgContent = await page.evaluate(() => {
      const svg = document.getElementById("main-svg");
      if (!svg) return { error: "SVG element not found" };
      
      const w = svg.getAttribute("width");
      const h = svg.getAttribute("height");
      const childCount = svg?.children?.length || 0;
      const allText = Array.from(svg.querySelectorAll("*"))
        .map(el => el.tagName)
        .slice(0, 20);
      
      return {
        width: w,
        height: h,
        childCount: childCount,
        childTypes: allText,
        innerHTML: svg.innerHTML.substring(0, 300),
      };
    });
    
    console.error("[drawioRenderer] SVG diagnostic:", JSON.stringify(svgContent, null, 2));
    console.error("[drawioRenderer] Browser console logs:", pageLogs.slice(-5).join(" | "));
    
    if (svgContent.error || svgContent.childCount === 0) {
      console.error("[drawioRenderer] CRITICAL: SVG is empty!");
      console.error("[drawioRenderer] All page logs:", pageLogs.join("\n"));
      throw new Error("drawioRenderer: SVG empty - script didn't render");
    }

    const boundingBox = await el.boundingBox();
    console.error("[drawioRenderer] Bounding box:", boundingBox);
    
    const buf = await el.screenshot({ type: "png", omitBackground: true });
    console.error("[drawioRenderer] Screenshot taken, size:", buf?.length, "bytes");
    
    // EMERGENCY DEBUG: Save PNG to OS temp directory for inspection (non-fatal)
    try {
      const fs = require("fs");
      const os = require("os");
      const path = require("path");
      const debugDir = process.env.DEBUG_PPTX_TMP || os.tmpdir();
      const debugPath = path.join(debugDir, "diagram-debug.png");
      try {
        fs.writeFileSync(debugPath, buf);
        console.error(`[drawioRenderer] DEBUG: PNG saved to ${debugPath} (${buf.length} bytes)`);
      } catch (writeErr) {
        console.error("[drawioRenderer] WARNING: failed to save debug PNG:", writeErr.message);
      }
    } catch (err) {
      console.error("[drawioRenderer] WARNING: debug save skipped (require failed):", err.message);
    }
    
    if (!buf || buf.length < 500) {
      console.error("[drawioRenderer] ERROR: PNG too small!");
      throw new Error(`drawioRenderer: PNG too small (${buf?.length} bytes) — render failed`);
    }
    
    console.error("[drawioRenderer] SUCCESS: PNG rendered");
    return buf;
  } catch (err) {
    console.error("[drawioRenderer] FATAL ERROR:", err.message);
    throw err;
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

function _buildHtml(xml) {
  // Escape the XML for safe embedding in a JS string
  const xmlEscaped = JSON.stringify(xml);

  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#F0EEFF; font-family: Arial, sans-serif; overflow:hidden; }
#diagram-wrap { display:inline-block; background:#F0EEFF; padding:40px; min-width:600px; min-height:400px; }
#main-svg { border:1px solid #999; display:block; background:white; }
#diagram-ready { display:none; }
</style>
</head>
<body>
<div id="diagram-wrap"><svg id="main-svg" xmlns="http://www.w3.org/2000/svg"></svg></div>
<div id="diagram-ready"></div>
<script>
(async function() {
  try {
    console.log("[SVG Init] Script started");
    
    const xmlStr = ${xmlEscaped};
    const NS = "http://www.w3.org/2000/svg";
    
    console.log("[SVG Init] XML loaded, length:", xmlStr.length);
    if (!xmlStr || xmlStr.length < 100) {
      throw new Error("XML string is too short: " + xmlStr.length);
    }

    // ── Parse draw.io XML ────────────────────────────────────────────────────
    const doc = new DOMParser().parseFromString(xmlStr, "text/xml");
    console.log("[SVG Init] Parsed XML");
    
    if (doc.getElementsByTagName("parsererror").length > 0) {
      const parseErr = doc.getElementsByTagName("parsererror")[0];
      throw new Error("XML parse error: " + parseErr.textContent);
    }
    
    const allCells = Array.from(doc.querySelectorAll("mxCell"));
    console.log("[SVG Init] Found total mxCells:", allCells.length);

    const nodeMap = {};
    const edges = [];

    allCells.forEach((cell, idx) => {
      const id = cell.getAttribute("id");
      const parent = cell.getAttribute("parent") || "1";
      const value = cell.getAttribute("value") || "";
      const isV = cell.getAttribute("vertex") === "1";
      const isE = cell.getAttribute("edge") === "1";

      if (isV && id !== "0" && id !== "1" && id !== null) {
        const geom = cell.querySelector("mxGeometry");
        if (geom) {
          nodeMap[id] = {
            id, parent, value,
            x: parseFloat(geom.getAttribute("x") || 0),
            y: parseFloat(geom.getAttribute("y") || 0),
            w: parseFloat(geom.getAttribute("width") || 120),
            h: parseFloat(geom.getAttribute("height") || 50),
            style: cell.getAttribute("style") || "",
            isSwimlane: (cell.getAttribute("style") || "").includes("swimlane"),
          };
        }
      }
      if (isE) {
        edges.push({
          src: cell.getAttribute("source"),
          tgt: cell.getAttribute("target"),
          label: value
        });
      }
    });

    console.log("[SVG Init] Extracted nodes:", Object.keys(nodeMap).length, "edges:", edges.length);

    // Quick exit if empty
    if (Object.keys(nodeMap).length === 0) {
      throw new Error("No nodes extracted from XML");
    }

    // ── Compute absolute positions ────────────────────────────────────────────
    function getAbsPos(id) {
      const n = nodeMap[id];
      if (!n) return { x: 0, y: 0 };
      if (n.parent === "0" || n.parent === "1") return { x: n.x, y: n.y };
      const p = getAbsPos(n.parent);
      const pNode = nodeMap[n.parent];
      const hdr = (pNode && pNode.isSwimlane) ? 35 : 0;
      return { x: p.x + n.x, y: p.y + n.y + hdr };
    }

    Object.values(nodeMap).forEach(n => {
      const abs = getAbsPos(n.id);
      n.ax = abs.x;
      n.ay = abs.y;
    });

    // ── Canvas bounds ─────────────────────────────────────────────────────────
    const PAD = 60;
    let maxX = 400, maxY = 300;
    Object.values(nodeMap).forEach(n => {
      maxX = Math.max(maxX, n.ax + n.w + 20);
      maxY = Math.max(maxY, n.ay + n.h + 20);
    });
    const svgW = Math.max(800, maxX + PAD);
    const svgH = Math.max(500, maxY + PAD);

    console.log("[SVG Init] Canvas:", svgW, "x", svgH);

    // ── Get SVG element ──────────────────────────────────────────────────────
    const svg = document.getElementById("main-svg");
    if (!svg) throw new Error("SVG element not found");
    
    svg.setAttribute("width", svgW);
    svg.setAttribute("height", svgH);
    svg.setAttribute("viewBox", "0 0 " + svgW + " " + svgH);
    console.log("[SVG Init] SVG element configured");

    // ── Defs (filters, markers) ──────────────────────────────────────────────
    const defs = document.createElementNS(NS, "defs");
    defs.innerHTML =
      '<filter id="ds" x="-15%" y="-15%" width="130%" height="130%">' +
        '<feDropShadow dx="2" dy="4" stdDeviation="5" flood-color="#000000" flood-opacity="0.2"/>' +
      '</filter>' +
      '<marker id="arr" markerWidth="12" markerHeight="10" refX="10" refY="5" orient="auto">' +
        '<polygon points="0 0, 12 5, 0 10" fill="#475569"/>' +
      '</marker>';
    svg.appendChild(defs);

    // ── Helper for element creation ──────────────────────────────────────────
    function mkEl(tag, attrs) {
      const el = document.createElementNS(NS, tag);
      Object.entries(attrs).forEach(([k, v]) => el.setAttribute(k, v));
      return el;
    }

    // ── Background ─────────────────────────────────────────────────────────────
    svg.appendChild(mkEl("rect", { x: 0, y: 0, width: svgW, height: svgH, fill: "#FFFFFF" }));
    console.log("[SVG Init] Background added");

    // ── Style parser ────────────────────────────────────────────────────────────
    function parseStyle(s) {
      const m = {};
      (s || "").split(";").forEach(p => {
        const [k, ...vs] = p.split("=");
        if (k && vs.length) m[k.trim()] = vs.join("=").trim();
      });
      return m;
    }
    function hx(v) { return v && v !== "none" ? (v.startsWith("#") ? v : "#" + v) : null; }

    // ── Draw swimlanes ──────────────────────────────────────────────────────────
    const swimlanes = Object.values(nodeMap).filter(n => n.isSwimlane);
    console.log("[SVG Init] Drawing", swimlanes.length, "swimlanes");
    
    swimlanes.forEach((n, idx) => {
      const st = parseStyle(n.style);
      const fill = hx(st.fillColor) || "#EDE9FE";
      const strk = hx(st.strokeColor) || "#7C3AED";
      const hdrColor = hx(st.fontColor) || "#6D28D9";

      svg.appendChild(mkEl("rect", {
        x: n.ax, y: n.ay, width: n.w, height: n.h,
        rx: 10, fill, stroke: strk, "stroke-width": 2.5, filter: "url(#ds)"
      }));

      const HDR = 35;
      svg.appendChild(mkEl("rect", {
        x: n.ax, y: n.ay, width: n.w, height: HDR,
        rx: 10, fill: hdrColor, stroke: strk, "stroke-width": 2.5
      }));

      const lt = mkEl("text", {
        x: n.ax + n.w / 2, y: n.ay + 22,
        "text-anchor": "middle", "font-size": 13, "font-weight": "bold",
        fill: "#FFFFFF", "font-family": "Arial, sans-serif"
      });
      lt.textContent = n.value || "Layer";
      svg.appendChild(lt);
    });

    // ── Draw edges ──────────────────────────────────────────────────────────────
    console.log("[SVG Init] Drawing", edges.length, "edges");
    
    edges.forEach(e => {
      const sn = nodeMap[e.src];
      const tn = nodeMap[e.tgt];
      if (!sn || !tn) return;

      const x1 = sn.ax + sn.w;
      const y1 = sn.ay + sn.h / 2;
      const x2 = tn.ax;
      const y2 = tn.ay + tn.h / 2;
      const gap = Math.max(Math.abs(x2 - x1) * 0.35, 40);

      svg.appendChild(mkEl("path", {
        d: "M " + x1 + " " + y1 + " C " + (x1 + gap) + " " + y1 + " " + (x2 - gap) + " " + y2 + " " + x2 + " " + y2,
        stroke: "#6B7280", "stroke-width": 2.2, fill: "none", "marker-end": "url(#arr)",
        "stroke-linecap": "round", "stroke-linejoin": "round"
      }));
    });

    // ── Draw components ─────────────────────────────────────────────────────────
    const components = Object.values(nodeMap).filter(n => !n.isSwimlane);
    console.log("[SVG Init] Drawing", components.length, "components");
    
    components.forEach(n => {
      const st = parseStyle(n.style);
      const fill = hx(st.fillColor) || "#3B82F6";
      const strk = hx(st.strokeColor) || "#1D4ED8";

      svg.appendChild(mkEl("rect", {
        x: n.ax, y: n.ay, width: n.w, height: n.h,
        rx: 8, fill, stroke: strk, "stroke-width": 2, filter: "url(#ds)"
      }));

      const lines = (n.value || "Comp").split("\\n").map(l => l.trim()).filter(l => l).slice(0, 2);
      if (lines.length === 0) lines.push("Comp");

      const lineHeight = 12;
      const totalHeight = lines.length * lineHeight;
      const startY = n.ay + (n.h - totalHeight) / 2 + lineHeight;

      lines.forEach((line, lineIndex) => {
        const fontSize = lineIndex === 0 ? 11 : 8;
        const t = mkEl("text", {
          x: n.ax + n.w / 2,
          y: startY + lineIndex * lineHeight,
          "text-anchor": "middle",
          "font-size": fontSize,
          "font-weight": "bold",
          fill: "#FFFFFF",
          "font-family": "Arial, sans-serif"
        });
        t.textContent = line.substring(0, 20);
        svg.appendChild(t);
      });
    });

    console.log("[SVG Init] SUCCESS: SVG fully rendered");
    
    // Signal completion
    setTimeout(() => {
      document.getElementById("diagram-ready").style.display = "block";
      console.log("[SVG Init] Diagram-ready signal sent");
    }, 300);

  } catch (err) {
    console.error("[SVG Init] FATAL:", err.message);
    console.error("[SVG Init] Stack:", err.stack);
    document.getElementById("diagram-ready").style.display = "block";
  }
})();
</script>
</body>
</html>`;
}

function _delay(ms) { return new Promise(r => setTimeout(r, ms)); }

module.exports = { renderDrawioToPng };