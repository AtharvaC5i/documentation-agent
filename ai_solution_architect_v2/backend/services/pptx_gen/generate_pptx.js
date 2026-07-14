"use strict";

const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { generateDrawioXml } = require("./drawioGenerator");
const { renderDrawioToPng } = require("./drawioRenderer");
const { addCustomSlide } = require("./customSlideRenderer");
const path = require("path");

// ── CLI ──────────────────────────────────────────────────────────────────────
const [, , inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  console.error("Usage: node generatepptx.js input.json output.pptx");
  process.exit(1);
}

const DATA = JSON.parse(fs.readFileSync(inputPath, "utf8"));

// Pre-read logos as base64 data URIs so pptxgenjs embeds them (not file references)
function _readLogoDataUri(filePath) {
  try {
    if (fs.existsSync(filePath)) {
      return (
        "data:image/png;base64," + fs.readFileSync(filePath).toString("base64")
      );
    }
  } catch (e) {
    log(`[pptx-gen] Could not read logo ${filePath}: ${e.message}`);
  }
  return null;
}
const imageLogoWhiteData = _readLogoDataUri(
  path.join(__dirname, "logo_white.png"),
);
const imageLogoData = _readLogoDataUri(path.join(__dirname, "logo.png"));
const LOGO_DATA = imageLogoWhiteData || imageLogoData; // prefer white version

// ── Brand colors ─────────────────────────────────────────────────────────────
const C = {
  purple: "3D35C9",
  purpleDark: "2A239A",
  purpleMid: "5B21B6",
  purpleLight: "A78BFA",
  purpleFaint: "EDE9FE",
  pageBg: "FFFFFF",
  closingBg: "5B21D4",
  white: "FFFFFF",
  offwhite: "FAFAFE",
  text: "1E1B4B",
  textDark: "222222",
  textMuted: "6B7280",
  border: "E2E0EF",
  success: "10B981",
  warning: "D97706",
  error: "EF4444",
  info: "2563EB",
};

const FONT_TITLE = "Calibri";
const FONT_BODY = "Calibri";
const W = 10;
const H = 5.625;

// ── Utilities ────────────────────────────────────────────────────────────────
function log(msg) {
  console.error(msg);
}

function shouldInclude(key) {
  try {
    const sel = DATA.selected_slides || DATA.selectedslides;
    if (!sel || !Array.isArray(sel) || sel.length === 0) return true;
    return sel.includes(key);
  } catch (e) {
    return true;
  }
}

// NEW: if custom_slides already has an exec summary, skip the predefined one
function hasCustomExecSummary() {
  const custom = DATA.custom_slides || DATA.customslides;
  if (!Array.isArray(custom)) return false;
  return custom.some(
    (cs) =>
      typeof cs === "object" &&
      (String(cs.type || "").toLowerCase() === "executive-summary" ||
        String(cs.title || "")
          .trim()
          .toLowerCase() === "executive summary"),
  );
}

function sanitize(val) {
  if (val === null || val === undefined) return "";

  return String(val)
    .replace(/[\u0000-\u0008\u000B\u000C\u000E-\u001F\u007F-\u009F]/g, "")
    .replace(/[\uD800-\uDFFF]/g, "") // remove invalid unicode surrogates
    .trim();
}

function R(slide, x, y, w, h, opts) {
  if (w > 0.001 && h > 0.001) slide.addShape("rect", { x, y, w, h, ...opts });
}
function E(slide, x, y, w, h, opts) {
  if (w > 0.001 && h > 0.001)
    slide.addShape("ellipse", { x, y, w, h, ...opts });
}

function clampH(h, min) {
  return Math.max(min || 0.2, h);
}

function addLogo(slide, x, y, w, h) {
  try {
    if (LOGO_DATA) {
      slide.addImage({
        data: LOGO_DATA,
        x,
        y,
        w,
        h,
        sizing: { type: "contain", w, h },
      });
    }
  } catch (e) {
    log(`[pptx-gen] logo skipped: ${e.message}`);
  }
}

// ── Layout constants ─────────────────────────────────────────────────────────
const HDR_H = 0.76;
const BODY_Y = 0.86;
const BODY_H = H - BODY_Y - 0.36;

// The editable title and closing slides are inserted by PowerPoint itself in
// pptx_service.py after this content deck has been written.  Do not ZIP-merge
// packages here: that produces invalid master/layout relationships.

// ════════════════════════════════════════════════════════════════════════════
// CONTENT CHROME
// ════════════════════════════════════════════════════════════════════════════
function contentChrome(slide, title) {
  slide.background = { color: C.pageBg };

  R(slide, 0, 0, 0.055, H, {
    fill: { color: C.purple },
    line: { color: C.purple },
  });

  // Purple background box at top-right so logo_white is visible
  R(slide, W - 1.3, 0, 1.3, HDR_H, {
    fill: { color: C.purple },
    line: { color: C.purple },
  });
  addLogo(slide, W - 1.2, 0.12, 1.08, 0.52);

  slide.addText(sanitize(title), {
    x: 0.18,
    y: 0.12,
    w: W - 1.6,
    h: 0.52,
    fontSize: 20,
    bold: true,
    color: C.text,
    fontFace: FONT_TITLE,
    align: "left",
    valign: "middle",
    margin: 0,
  });

  R(slide, 0, HDR_H, W, 0.06, {
    fill: { color: C.purple },
    line: { color: C.purple },
  });

  R(slide, 0, H - 0.28, W, 0.02, {
    fill: { color: C.border },
    line: { color: C.border },
  });

  const pn = sanitize(DATA.project?.name) || "AI Solution Architect";
  slide.addText(pn, {
    x: 0.22,
    y: H - 0.27,
    w: 4,
    h: 0.18,
    fontSize: 8,
    bold: true,
    color: C.purple,
    fontFace: FONT_BODY,
    align: "left",
    margin: 0,
  });
  slide.addText("Confidential", {
    x: 0.22,
    y: H - 0.14,
    w: 4,
    h: 0.14,
    fontSize: 7,
    color: C.textMuted,
    fontFace: FONT_BODY,
    align: "left",
    margin: 0,
  });
  slide.addText(pn, {
    x: W - 4.2,
    y: H - 0.22,
    w: 4,
    h: 0.18,
    fontSize: 8,
    bold: true,
    color: C.purple,
    fontFace: FONT_BODY,
    align: "right",
    margin: 0,
  });
}

// ── Bullet list ───────────────────────────────────────────────────────────────
function bulletList(slide, items, x, y, w, h, opts = {}) {
  if (!items || items.length === 0) return;
  const rowH = opts.rowH || 0.46;
  items.slice(0, 12).forEach((item, i) => {
    const text = sanitize(
      typeof item === "string"
        ? item
        : item.risk ||
            item.phase ||
            item.step ||
            item.description ||
            JSON.stringify(item),
    );
    const rowY = y + i * rowH;
    if (rowY + 0.22 > y + h) return;
    R(slide, x, rowY + 0.17, 0.1, 0.1, {
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(text, {
      x: x + 0.2,
      y: rowY,
      w: Math.max(0.5, w - 0.22),
      h: rowH,
      fontSize: opts.fontSize || 11.5,
      color: opts.color || C.textDark,
      fontFace: FONT_BODY,
      valign: "middle",
      margin: 0,
      wrap: true,
    });
  });
}

// ── Section label ─────────────────────────────────────────────────────────────
function sectionLabel(slide, text, x, y, w) {
  slide.addText(sanitize(text).toUpperCase(), {
    x,
    y,
    w,
    h: 0.24,
    fontSize: 8,
    bold: true,
    color: C.purple,
    fontFace: FONT_BODY,
    charSpacing: 0.8,
    margin: 0,
  });
  R(slide, x, y + 0.22, Math.min(w, 1.8), 0.025, {
    fill: { color: C.purple },
    line: { color: C.purple },
  });
}

// ── Card ──────────────────────────────────────────────────────────────────────
function card(slide, x, y, w, h, label, value, accentColor) {
  R(slide, x, y, w, h, {
    fill: { color: C.white },
    line: { color: C.border, width: 0.75 },
  });
  R(slide, x, y, w, 0.05, {
    fill: { color: C.purple },
    line: { color: C.purple },
  });
  if (label)
    slide.addText(sanitize(label).toUpperCase(), {
      x: x + 0.14,
      y: y + 0.1,
      w: w - 0.22,
      h: 0.22,
      fontSize: 7.5,
      bold: true,
      color: C.purple,
      fontFace: FONT_BODY,
      charSpacing: 0.8,
      margin: 0,
    });
  if (value)
    slide.addText(sanitize(value), {
      x: x + 0.14,
      y: y + (label ? 0.36 : 0.14),
      w: w - 0.22,
      h: clampH(h - (label ? 0.44 : 0.22)),
      fontSize: 11,
      color: C.textDark,
      fontFace: FONT_BODY,
      valign: "top",
      margin: 0,
      wrap: true,
    });
}

// ════════════════════════════════════════════════════════════════════════════
// CONTENT SLIDES
// ════════════════════════════════════════════════════════════════════════════

function addExecSummarySlide(pres) {
  const slide = pres.addSlide();
  contentChrome(slide, "Executive Summary");

  const a = DATA.alignment || {};
  const sol = DATA.proposed_solution || DATA.proposedsolution || {};
  const goals = a.goals || [];
  const metrics = a.success_metrics || a.successmetrics || [];
  const banner = sanitize(sol.summary || a.business_value || a.businessvalue);

  if (banner) {
    R(slide, 0.18, BODY_Y, W - 0.28, 0.68, {
      fill: { color: C.purpleFaint },
      line: { color: C.border, width: 0.75 },
    });
    R(slide, 0.18, BODY_Y, 0.06, 0.68, {
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(banner, {
      x: 0.36,
      y: BODY_Y + 0.06,
      w: W - 0.62,
      h: 0.56,
      fontSize: 11.5,
      color: C.text,
      bold: true,
      fontFace: FONT_BODY,
      align: "center",
      valign: "middle",
      margin: 0,
      wrap: true,
    });
  }

  const cY = BODY_Y + (banner ? 0.78 : 0.04);
  const c2X = 5.18;
  sectionLabel(slide, "Strategic Goals", 0.22, cY, 4.5);
  bulletList(slide, goals.slice(0, 5), 0.22, cY + 0.3, 4.6, BODY_H - 0.34);
  R(slide, 4.96, cY, 0.02, clampH(BODY_H - 0.1), {
    fill: { color: C.border },
    line: { color: C.border },
  });
  sectionLabel(slide, "Success Metrics", c2X, cY, 4.5);
  bulletList(slide, metrics.slice(0, 5), c2X, cY + 0.3, 4.5, BODY_H - 0.34);
}

function addProblemSlide(pres) {
  const slide = pres.addSlide();
  contentChrome(slide, "Problem Statement");

  const ps = DATA.problem_statement || DATA.problemstatement || {};
  const pains = ps.current_pain_points || ps.currentpainpoints || [];
  const impact = sanitize(ps.impact);
  const rootCause = sanitize(ps.root_cause || ps.rootcause);

  if (pains.length > 0) {
    const cW = 4.44,
      cH = 0.72,
      gY = 0.1;
    pains.slice(0, 6).forEach((pain, i) => {
      const x = i % 2 === 0 ? 0.18 : 5.08;
      const y = BODY_Y + 0.04 + Math.floor(i / 2) * (cH + gY);
      R(slide, x, y, cW, cH, {
        fill: { color: C.white },
        line: { color: C.border, width: 0.75 },
      });
      R(slide, x, y, cW, 0.05, {
        fill: { color: C.purple },
        line: { color: C.purple },
      });
      E(slide, x + 0.1, y + 0.17, 0.36, 0.36, {
        fill: { color: C.purple },
        line: { color: C.purple },
      });
      slide.addText(String(i + 1), {
        x: x + 0.1,
        y: y + 0.17,
        w: 0.36,
        h: 0.36,
        fontSize: 9,
        bold: true,
        color: C.white,
        fontFace: FONT_BODY,
        align: "center",
        valign: "middle",
        margin: 0,
      });
      slide.addText(
        sanitize(typeof pain === "string" ? pain : JSON.stringify(pain)),
        {
          x: x + 0.58,
          y: y + 0.1,
          w: cW - 0.72,
          h: clampH(cH - 0.18),
          fontSize: 10.5,
          color: C.textDark,
          fontFace: FONT_BODY,
          valign: "middle",
          wrap: true,
          margin: 0,
        },
      );
    });
  } else {
    slide.addText("No pain points specified.", {
      x: 0.3,
      y: BODY_Y + 0.2,
      w: 9,
      h: 0.4,
      fontSize: 12,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
  }

  const bY = H - 0.38 - 1.14;
  if (impact) card(slide, 0.18, bY, 4.44, 1.1, "Business Impact", impact);
  if (rootCause) card(slide, 5.08, bY, 4.44, 1.1, "Root Cause", rootCause);
}

function addSolutionSlide(pres) {
  const slide = pres.addSlide();
  contentChrome(slide, "Proposed Solution");

  const sol = DATA.proposed_solution || DATA.proposedsolution || {};
  const arch = DATA.architecture || {};
  const diff = sol.key_differentiators || sol.keydifferentiators || [];
  const approach = sanitize(sol.approach);
  const summary = sanitize(sol.summary);

  if (summary) {
    R(slide, 0.18, BODY_Y, W - 0.28, 0.68, {
      fill: { color: C.purpleFaint },
      line: { color: C.border, width: 0.75 },
    });
    R(slide, 0.18, BODY_Y, 0.06, 0.68, {
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(summary, {
      x: 0.36,
      y: BODY_Y + 0.06,
      w: W - 0.62,
      h: 0.56,
      fontSize: 11,
      color: C.text,
      bold: true,
      fontFace: FONT_BODY,
      align: "center",
      valign: "middle",
      margin: 0,
      wrap: true,
    });
  }

  const cY = BODY_Y + (summary ? 0.78 : 0.04);
  sectionLabel(slide, "Key Differentiators", 0.22, cY, 5.2);
  bulletList(slide, diff.slice(0, 5), 0.22, cY + 0.3, 5.2, 2.2);
  if (approach)
    card(slide, 5.98, cY, 3.66, 2.5, "Approach", approach, C.purple);

  const pattern = sanitize(arch.pattern);
  if (pattern) {
    const patY = cY + 2.62;
    if (patY + 0.72 < H - 0.3) {
      R(slide, 0.18, patY, W - 0.28, 0.72, {
        fill: { color: C.white },
        line: { color: C.border, width: 0.75 },
      });
      R(slide, 0.18, patY, 0.06, 0.72, {
        fill: { color: C.purpleLight },
        line: { color: C.purpleLight },
      });
      slide.addText("ARCHITECTURE PATTERN", {
        x: 0.38,
        y: patY + 0.06,
        w: 3.8,
        h: 0.2,
        fontSize: 7.5,
        bold: true,
        color: C.purple,
        fontFace: FONT_BODY,
        charSpacing: 0.6,
        margin: 0,
      });
      slide.addText(pattern, {
        x: 0.38,
        y: patY + 0.3,
        w: W - 0.6,
        h: 0.36,
        fontSize: 13,
        color: C.purple,
        bold: true,
        fontFace: FONT_BODY,
        margin: 0,
      });
    }
  }
}

function addDiagramSlide(pres, rawBase64) {
  const slide = pres.addSlide();
  contentChrome(slide, "High-Level Architecture Diagram");
  // Ensure proper data URI prefix for pptxgenjs image embedding
  const dataUri = rawBase64.startsWith("data:")
    ? rawBase64
    : "data:image/png;base64," + rawBase64;
  slide.addImage({
    data: dataUri,
    x: 0.18,
    y: BODY_Y,
    w: W - 0.28,
    h: BODY_H,
    sizing: { type: "contain", w: W - 0.28, h: BODY_H },
  });
}

function addComponentsSlide(pres) {
  const slide = pres.addSlide();
  contentChrome(slide, "Component Breakdown");

  const arch = DATA.architecture || {};
  const components = arch.components || [];

  if (components.length === 0) {
    const pairs = [
      ["Frontend", arch.frontend],
      ["Backend", arch.backend],
      ["AI Layer", arch.ai_layer || arch.ailayer],
      ["Data Store", arch.data_store || arch.datastore],
      ["Hosting", arch.hosting],
    ].filter(([, v]) => v);
    pairs.forEach(([label, value], i) => {
      card(
        slide,
        i % 2 === 0 ? 0.18 : 5.08,
        BODY_Y + Math.floor(i / 2) * 0.96,
        4.5,
        0.86,
        label,
        sanitize(value),
      );
    });
    return;
  }

  components.slice(0, 8).forEach((comp, i) => {
    const x = i % 2 === 0 ? 0.18 : 5.08;
    const y = BODY_Y + Math.floor(i / 2) * 1.08;
    const ac = i % 2 === 0 ? C.purple : C.purpleMid;
    const compName = sanitize(
      comp.name || comp.label || comp.id || "Component",
    );
    const compRole = sanitize(comp.role || "");
    const compTech = sanitize(comp.technology || "");

    R(slide, x, y, 4.5, 1.0, {
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
    });
    R(slide, x, y, 4.5, 0.05, { fill: { color: ac }, line: { color: ac } });
    slide.addText(compName, {
      x: x + 0.14,
      y: y + 0.1,
      w: 4.26,
      h: 0.24,
      fontSize: 11,
      bold: true,
      color: C.purple,
      fontFace: FONT_BODY,
      margin: 0,
    });
    if (compTech) {
      const bW = Math.min(Math.max(compTech.length * 0.082 + 0.28, 0.5), 4.22);
      R(slide, x + 0.14, y + 0.36, bW, 0.2, {
        fill: { color: C.purpleFaint },
        line: { color: C.border, width: 0.5 },
      });
      slide.addText(compTech, {
        x: x + 0.18,
        y: y + 0.38,
        w: bW - 0.08,
        h: 0.16,
        fontSize: 8,
        color: ac,
        bold: true,
        fontFace: FONT_BODY,
        margin: 0,
      });
    }
    if (compRole)
      slide.addText(compRole, {
        x: x + 0.14,
        y: y + (compTech ? 0.6 : 0.36),
        w: 4.26,
        h: 0.32,
        fontSize: 10,
        color: C.textMuted,
        fontFace: FONT_BODY,
        margin: 0,
        wrap: true,
      });
  });
}

function addDataFlowSlide(pres) {
  const slide = pres.addSlide();
  contentChrome(slide, "Data Flow");

  const steps = (DATA.data_flow || DATA.dataflow || []).slice(0, 8);
  if (steps.length === 0) {
    slide.addText("No data flow steps defined.", {
      x: 0.3,
      y: BODY_Y + 0.3,
      w: 9,
      h: 0.4,
      fontSize: 12,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
    return;
  }

  const stepH = 0.52,
    gapY = 0.07;

  const renderStep = (label, idx, x, y, boxW) => {
    const ac = idx % 2 === 0 ? C.purple : C.purpleMid;
    R(slide, x + 0.44, y, boxW, stepH, {
      fill: { color: idx % 2 === 0 ? C.white : C.purpleFaint },
      line: { color: C.border, width: 0.5 },
    });
    R(slide, x + 0.44, y, boxW, 0.04, {
      fill: { color: ac },
      line: { color: ac },
    });
    E(slide, x + 0.08, y + 0.09, 0.36, 0.36, {
      fill: { color: ac },
      line: { color: ac },
    });
    slide.addText(String(idx + 1), {
      x: x + 0.08,
      y: y + 0.09,
      w: 0.36,
      h: 0.36,
      fontSize: 10,
      bold: true,
      color: C.white,
      fontFace: FONT_BODY,
      align: "center",
      valign: "middle",
      margin: 0,
    });
    slide.addText(sanitize(label), {
      x: x + 0.58,
      y: y + 0.09,
      w: Math.max(0.5, boxW - 0.18),
      h: 0.36,
      fontSize: 11,
      color: C.textDark,
      fontFace: FONT_BODY,
      valign: "middle",
      margin: 0,
      wrap: true,
    });
    if (idx < steps.length - 1) {
      R(slide, x + 0.24, y + stepH, 0.02, clampH(gapY, 0.05), {
        fill: { color: C.purpleLight },
        line: { color: C.purpleLight },
      });
    }
  };

  const getLabel = (step) =>
    sanitize(
      typeof step === "string"
        ? step
        : step.step || step.description || JSON.stringify(step),
    );

  if (steps.length <= 4) {
    steps.forEach((step, i) =>
      renderStep(getLabel(step), i, 0.1, BODY_Y + i * (stepH + gapY), 9.26),
    );
  } else {
    const half = Math.ceil(steps.length / 2);
    [steps.slice(0, half), steps.slice(half)].forEach((col, ci) => {
      const xBase = ci === 0 ? 0.1 : 5.08;
      col.forEach((step, ri) => {
        renderStep(
          getLabel(step),
          ci === 0 ? ri : half + ri,
          xBase,
          BODY_Y + ri * (stepH + gapY),
          4.28,
        );
      });
    });
  }
}

function addTechStackSlide(pres) {
  const slide = pres.addSlide();
  contentChrome(slide, "Technology Stack");

  const ts = DATA.technology_stack || DATA.technologystack || {};
  const layers = [
    { label: "Frontend", items: ts.frontend || [] },
    { label: "Backend", items: ts.backend || [] },
    { label: "AI / ML", items: ts.ai_ml || ts.aiml || [] },
    { label: "Data", items: ts.data || [] },
    { label: "Infrastructure", items: ts.infrastructure || [] },
    { label: "Security", items: ts.security || [] },
  ].filter((l) => l.items.length > 0);

  if (layers.length === 0) {
    slide.addText("No technology stack defined.", {
      x: 0.3,
      y: BODY_Y + 0.3,
      w: 9,
      h: 0.4,
      fontSize: 12,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
    return;
  }

  const colW = 3.02,
    boxH = 1.48,
    gap = 0.1;
  const cols = [0.18, 3.5, 6.68];
  let col = 0,
    row = 0;

  layers.forEach((layer) => {
    const x = cols[col];
    const y = BODY_Y + row * (boxH + gap);
    R(slide, x, y, colW, boxH, {
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
    });
    R(slide, x, y, colW, 0.36, {
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(layer.label.toUpperCase(), {
      x: x + 0.1,
      y: y + 0.06,
      w: colW - 0.18,
      h: 0.24,
      fontSize: 8.5,
      bold: true,
      color: C.white,
      fontFace: FONT_BODY,
      charSpacing: 0.7,
      align: "center",
      margin: 0,
    });
    slide.addText(layer.items.slice(0, 5).map(sanitize).join("\n"), {
      x: x + 0.1,
      y: y + 0.42,
      w: colW - 0.18,
      h: clampH(boxH - 0.52),
      fontSize: 10.5,
      color: C.textDark,
      fontFace: FONT_BODY,
      valign: "top",
      wrap: true,
      margin: 0,
      lineSpacingMultiple: 1.15,
    });
    col++;
    if (col >= 3) {
      col = 0;
      row++;
    }
  });
}

function addFeaturesSlide(pres) {
  const slide = pres.addSlide();
  contentChrome(slide, "Key Features & Capabilities");

  const sol = DATA.proposed_solution || DATA.proposedsolution || {};
  const diff = sol.key_differentiators || sol.keydifferentiators || [];
  const goals = DATA.alignment?.goals || [];
  const seen = new Set();
  const features = [...diff, ...goals].filter((f) => {
    const k = String(f).trim().toLowerCase();
    if (seen.has(k)) return false;
    seen.add(k);
    return Boolean(f);
  });

  if (features.length === 0) {
    slide.addText("No features defined.", {
      x: 0.3,
      y: BODY_Y + 0.3,
      w: 9,
      h: 0.4,
      fontSize: 12,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
    return;
  }

  const accents = [C.purple, C.purpleMid, C.purpleLight];
  const renderF = (items, xBase, cW) => {
    items.slice(0, 6).forEach((item, i) => {
      const y = BODY_Y + i * 0.72;
      const ac = accents[i % 3];
      R(slide, xBase, y, cW, 0.64, {
        fill: { color: i % 2 === 0 ? C.white : C.offwhite },
        line: { color: C.border, width: 0.75 },
      });
      R(slide, xBase, y, cW, 0.05, {
        fill: { color: ac },
        line: { color: ac },
      });
      E(slide, xBase + 0.1, y + 0.14, 0.34, 0.34, {
        fill: { color: ac },
        line: { color: ac },
      });
      slide.addText(String(i + 1), {
        x: xBase + 0.1,
        y: y + 0.14,
        w: 0.34,
        h: 0.34,
        fontSize: 9,
        bold: true,
        color: C.white,
        fontFace: FONT_BODY,
        align: "center",
        valign: "middle",
        margin: 0,
      });
      slide.addText(sanitize(item), {
        x: xBase + 0.54,
        y: y + 0.08,
        w: Math.max(0.5, cW - 0.64),
        h: 0.48,
        fontSize: 11,
        color: C.textDark,
        fontFace: FONT_BODY,
        valign: "middle",
        margin: 0,
        wrap: true,
      });
    });
  };

  if (features.length <= 6) renderF(features, 0.18, 9.62);
  else {
    const half = Math.ceil(features.length / 2);
    renderF(features.slice(0, half), 0.18, 4.52);
    renderF(features.slice(half), 5.08, 4.52);
  }
}

function addNFRSlide(pres) {
  const slide = pres.addSlide();
  contentChrome(slide, "Non-Functional Requirements");

  const nf = DATA.non_functional || DATA.nonfunctional || {};
  const nfrs = [
    { label: "Scalability", value: sanitize(nf.scalability) },
    { label: "Security", value: sanitize(nf.security) },
    { label: "Availability", value: sanitize(nf.availability) },
    { label: "Performance", value: sanitize(nf.performance) },
    { label: "Compliance", value: sanitize(nf.compliance) },
  ].filter((n) => n.value);

  if (nfrs.length === 0) {
    slide.addText("Non-functional requirements not specified.", {
      x: 0.3,
      y: BODY_Y + 0.3,
      w: 9,
      h: 0.4,
      fontSize: 12,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
    return;
  }

  const cW = 4.52,
    cH = 1.06,
    gap = 0.12;
  nfrs.forEach((nfr, i) => {
    const x = i % 2 === 0 ? 0.18 : 5.08;
    const y = BODY_Y + Math.floor(i / 2) * (cH + gap);
    R(slide, x, y, cW, cH, {
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
    });
    R(slide, x, y, cW, 0.32, {
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(nfr.label.toUpperCase(), {
      x: x + 0.1,
      y: y + 0.05,
      w: cW - 0.18,
      h: 0.22,
      fontSize: 8,
      bold: true,
      color: C.white,
      fontFace: FONT_BODY,
      charSpacing: 0.6,
      align: "center",
      margin: 0,
    });
    slide.addText(nfr.value, {
      x: x + 0.12,
      y: y + 0.36,
      w: cW - 0.22,
      h: clampH(cH - 0.44),
      fontSize: 11,
      color: C.textDark,
      fontFace: FONT_BODY,
      valign: "top",
      wrap: true,
      margin: 0,
    });
  });
}

function addRoadmapSlide(pres) {
  const slide = pres.addSlide();
  contentChrome(slide, "Implementation Roadmap");

  const phases = (DATA.roadmap || []).slice(0, 3);
  if (phases.length === 0) {
    slide.addText("Roadmap not defined.", {
      x: 0.3,
      y: BODY_Y + 0.3,
      w: 9,
      h: 0.4,
      fontSize: 12,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
    return;
  }

  const phaseColors = [C.purple, C.purpleMid, C.purpleLight];
  const phaseH = clampH(H - BODY_Y - 0.32, 0.8);
  const phaseW = (W - 0.54 - 0.14 * (phases.length - 1)) / phases.length;

  phases.forEach((phase, i) => {
    const x = 0.22 + i * (phaseW + 0.14);
    const color = phaseColors[i] || C.purple;
    R(slide, x, BODY_Y, phaseW, phaseH, {
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
    });
    R(slide, x, BODY_Y, phaseW, 0.6, {
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(sanitize(phase.phase) || `Phase ${i + 1}`, {
      x: x + 0.1,
      y: BODY_Y + 0.04,
      w: phaseW - 0.14,
      h: 0.3,
      fontSize: 9.5,
      bold: true,
      color: C.white,
      fontFace: FONT_BODY,
      align: "center",
      valign: "middle",
      margin: 0,
      wrap: true,
    });
    const dur = sanitize(phase.duration);
    if (dur)
      slide.addText(dur, {
        x: x + 0.1,
        y: BODY_Y + 0.36,
        w: phaseW - 0.14,
        h: 0.2,
        fontSize: 8.5,
        color: C.white,
        fontFace: FONT_BODY,
        italic: true,
        align: "center",
        margin: 0,
      });

    (phase.deliverables || []).slice(0, 5).forEach((d, di) => {
      const dy = BODY_Y + 0.68 + di * 0.55;
      if (dy + 0.48 > BODY_Y + phaseH - 0.04) return;
      R(slide, x + 0.1, dy, Math.max(0.2, phaseW - 0.18), 0.48, {
        fill: { color: C.purpleFaint },
        line: { color: C.border, width: 0.5 },
      });
      E(slide, x + 0.18, dy + 0.15, 0.16, 0.16, {
        fill: { color },
        line: { color },
      });
      slide.addText(sanitize(d), {
        x: x + 0.4,
        y: dy + 0.05,
        w: Math.max(0.2, phaseW - 0.56),
        h: 0.38,
        fontSize: 9,
        color: C.textDark,
        fontFace: FONT_BODY,
        valign: "middle",
        wrap: true,
        margin: 0,
      });
    });
  });
}

function addRisksSlide(pres) {
  const risks = DATA.risks || [];
  const assumptions = DATA.assumptions || [];
  const questions = DATA.open_questions || DATA.openquestions || [];
  if (!risks.length && !assumptions.length && !questions.length) return;

  const slide = pres.addSlide();
  contentChrome(slide, "Risks, Assumptions & Open Questions");

  const sections = [
    { label: "Risks & Mitigation", items: risks, x: 0.18, isRisk: true },
    { label: "Assumptions", items: assumptions, x: 3.46, isRisk: false },
    { label: "Open Questions", items: questions, x: 6.74, isRisk: false },
  ];
  const cW = 3.04;
  const cH = clampH(H - BODY_Y - 0.32, 0.8);

  sections.forEach(({ label, items, x, isRisk }) => {
    R(slide, x, BODY_Y, cW, cH, {
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
    });
    R(slide, x, BODY_Y, cW, 0.4, {
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(sanitize(label).toUpperCase(), {
      x: x + 0.1,
      y: BODY_Y,
      w: cW - 0.14,
      h: 0.4,
      fontSize: 9,
      bold: true,
      color: C.white,
      fontFace: FONT_BODY,
      align: "center",
      valign: "middle",
      margin: 0,
      charSpacing: 0.3,
    });

    if (items.length === 0) {
      slide.addText("None identified.", {
        x: x + 0.1,
        y: BODY_Y + 0.48,
        w: cW - 0.18,
        h: 0.3,
        fontSize: 10,
        color: C.textMuted,
        italic: true,
        fontFace: FONT_BODY,
        margin: 0,
      });
      return;
    }

    if (isRisk) {
      items.slice(0, 5).forEach((r, i) => {
        const riskText = sanitize(typeof r === "string" ? r : r.risk);
        const mitText = typeof r === "object" ? sanitize(r.mitigation) : "";
        const rH = clampH(mitText ? 0.8 : 0.46, 0.3);
        const ry = BODY_Y + 0.48 + i * (rH + 0.07);
        if (ry + rH > BODY_Y + cH - 0.04) return;
        R(slide, x + 0.1, ry, cW - 0.18, rH, {
          fill: { color: C.offwhite },
          line: { color: C.border, width: 0.5 },
        });
        R(slide, x + 0.1, ry, 0.05, rH, {
          fill: { color: C.error },
          line: { color: C.error },
        });
        slide.addText(riskText, {
          x: x + 0.2,
          y: ry + 0.06,
          w: cW - 0.32,
          h: 0.28,
          fontSize: 9.5,
          bold: true,
          color: C.textDark,
          fontFace: FONT_BODY,
          wrap: true,
          margin: 0,
        });
        if (mitText)
          slide.addText(mitText, {
            x: x + 0.2,
            y: ry + 0.38,
            w: cW - 0.32,
            h: 0.36,
            fontSize: 9,
            color: C.textMuted,
            fontFace: FONT_BODY,
            italic: true,
            wrap: true,
            margin: 0,
          });
      });
    } else {
      bulletList(
        slide,
        items.slice(0, 7),
        x + 0.1,
        BODY_Y + 0.48,
        cW - 0.18,
        cH - 0.54,
        { fontSize: 10.5, rowH: 0.44 },
      );
    }
  });
}

// ════════════════════════════════════════════════════════════════════════════
// MAIN
// ════════════════════════════════════════════════════════════════════════════
(async () => {
  log("[pptx-gen] Starting PowerPoint generation pipeline...");
  log(`[pptx-gen] Project: ${DATA.project?.name || "Unknown"}`);

  // STEP 1 — draw.io XML
  log("\n[pptx-gen] STEP 1: Generating draw.io XML...");
  const startXml = Date.now();
  let drawioXml;
  try {
    drawioXml = generateDrawioXml(DATA);
    log(`[pptx-gen] draw.io XML: ${drawioXml.length} chars`);
    log(`[pptx-gen] STEP 1 duration: ${Date.now() - startXml} ms`);
  } catch (err) {
    console.error(`[pptx-gen] FATAL: draw.io XML failed: ${err.message}`);
    process.exit(1);
  }

  // STEP 2 — Render PNG via Puppeteer (non-fatal: diagram slide skipped on failure)
  log("\n[pptx-gen] STEP 2: Rendering PNG...");
  const startPng = Date.now();
  let diagramRawB64 = null;
  try {
    const pngBuffer = await renderDrawioToPng(drawioXml, {
      width: 1400,
      height: 850,
    });
    if (!pngBuffer || pngBuffer.length < 1000) {
      log(
        `[pptx-gen] WARNING: PNG buffer too small (${pngBuffer ? pngBuffer.length : 0} bytes) — diagram slide will be skipped`,
      );
    } else {
      diagramRawB64 = pngBuffer.toString("base64");
      log(`[pptx-gen] PNG: ${pngBuffer.length} bytes — OK`);
      log(`[pptx-gen] Diagram base64 length: ${diagramRawB64.length}`);
      log(`[pptx-gen] STEP 2 duration: ${Date.now() - startPng} ms`);
    }
  } catch (err) {
    log(
      `[pptx-gen] WARNING: PNG render failed: ${err.message} — diagram slide will be skipped`,
    );
  }

  // STEP 3 — Build the content deck. The service inserts editable templates.
  log("\n[pptx-gen] STEP 3: Building content PPTX...");
  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.title = sanitize(DATA.project?.name) || "AI Solution Architecture";
  pres.author = "AI Solution Architect";
  pres.subject = "High-Level Architecture Document";

  // Skip predefined exec summary if a custom one is present in custom_slides
  if (shouldInclude("ExecSummary")) addExecSummarySlide(pres);
  if (shouldInclude("Problem")) addProblemSlide(pres);
  if (shouldInclude("Solution")) addSolutionSlide(pres);
  if (shouldInclude("Diagram") && diagramRawB64)
    addDiagramSlide(pres, diagramRawB64);
  if (shouldInclude("Components")) addComponentsSlide(pres);
  if (shouldInclude("DataFlow")) addDataFlowSlide(pres);
  if (shouldInclude("TechStack")) addTechStackSlide(pres);
  if (shouldInclude("Features")) addFeaturesSlide(pres);
  if (shouldInclude("NFR")) addNFRSlide(pres);
  if (shouldInclude("Roadmap")) addRoadmapSlide(pres);
  if (shouldInclude("Risks")) addRisksSlide(pres);

  // ── Custom slides ──────────────────────────────────────────────────────
  try {
    const custom = DATA.custom_slides || DATA.customslides;
    if (Array.isArray(custom) && custom.length > 0) {
      log(
        `[pptx-gen] Rendering ${custom.length} custom slide(s) via layout engine...`,
      );
      const ctx = {
        R,
        E,
        clampH,
        sanitize,
        card,
        bulletList,
        sectionLabel,
        contentChrome,
        addLogo,
        C,
        FONT_TITLE,
        FONT_BODY,
        W,
        H,
        HDR_H,
        BODY_Y,
        BODY_H,
      };
      for (const cs of custom) {
        try {
          addCustomSlide(pres, cs, DATA, ctx);
        } catch (err) {
          log(
            `[pptx-gen] custom slide '${cs?.title || "?"}' skipped: ${err.message}`,
          );
          try {
            const fallbackSlide = pres.addSlide();
            contentChrome(fallbackSlide, sanitize(cs?.title) || "Custom");
            const rawBullets = cs?.bullets || cs?.content;
            if (Array.isArray(rawBullets)) {
              bulletList(
                fallbackSlide,
                rawBullets
                  .map((b) =>
                    typeof b === "string" ? b : sanitize(JSON.stringify(b)),
                  )
                  .filter(Boolean),
                0.22,
                BODY_Y,
                W - 0.36,
                BODY_H,
              );
            }
          } catch (_) {}
        }
      }
    }
  } catch (err) {
    log(`[pptx-gen] custom slides block failed: ${err.message}`);
  }

  // STEP 4 — Write content; the service assembles the final editable deck.
  log(`\n[pptx-gen] STEP 4: Writing content PPTX → ${outputPath}`);
  await pres.writeFile({ fileName: outputPath });

  log(`\n[pptx-gen] Done → ${outputPath}`);
  process.exit(0);
})();
