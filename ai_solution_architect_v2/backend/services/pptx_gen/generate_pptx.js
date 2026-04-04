/**
 * generate_pptx.js  —  AI Solution Architect · PowerPoint Generator
 *
 * Usage: node generate_pptx.js <input.json> <output.pptx>
 *
 * Slides:
 *  1.  Title
 *  2.  Executive Summary
 *  3.  Problem Statement
 *  4.  Proposed Solution Overview
 *  5.  Architecture Diagram  (draw.io XML → local Puppeteer render → PNG)
 *  6.  Component Breakdown
 *  7.  Data Flow
 *  8.  Technology Stack
 *  9.  Key Features & Capabilities
 * 10.  Non-Functional Requirements
 * 11.  Implementation Roadmap
 * 12.  Risks, Assumptions & Open Questions
 * 13.  Closing / Next Steps
 */

"use strict";

const fs      = require("fs");
const pptxgen = require("pptxgenjs");
const { generateDrawioXml } = require("./drawioGenerator");
const { renderDrawioToPng } = require("./drawioRenderer");

// ─── CLI ─────────────────────────────────────────────────────────────────────
const [,, inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  console.error("Usage: node generate_pptx.js <input.json> <output.pptx>");
  process.exit(1);
}

const DATA = JSON.parse(fs.readFileSync(inputPath, "utf8"));

// ─── Design System ────────────────────────────────────────────────────────────
const C = {
  primary:   "2D1B69",
  accent:    "7C3AED",
  accentAlt: "A78BFA",
  accentMid: "8B5CF6",
  white:     "FFFFFF",
  offwhite:  "F8F7FF",
  light:     "EDE9FE",
  lightMid:  "DDD6FE",
  border:    "C4B5FD",
  muted:     "6B7280",
  mutedDark: "4B5563",
  dark:      "1F2937",
  success:   "059669",
  warning:   "D97706",
  danger:    "DC2626",
  info:      "2563EB",
};

const FONT_TITLE = "Georgia";
const FONT_BODY  = "Calibri";
const W = 10;
const H = 5.625;


function log(msg) { console.error(msg); }

function _shouldInclude(key) {
  try {
    const sel = DATA.selected_slides;
    if (!sel || !Array.isArray(sel) || sel.length === 0) return true;
    return sel.includes(key);
  } catch (e) { return true; }
}

// ─── Reusable shadow factory (never reuse — PptxGenJS mutates in place) ────────
const mkShadow = () => ({ type: "outer", blur: 8, offset: 2, angle: 135, color: "000000", opacity: 0.10 });

// ─── Layout helpers ───────────────────────────────────────────────────────────

/** Standard content-slide background */
function pageBackground(slide) {
  slide.background = { color: C.offwhite };
}

/** Header band with gradient feel: deep indigo left → lighter right */
function headerBand(slide, title, subtitle) {
  // Full-width header band
  slide.addShape("rect", {
    x: 0, y: 0, w: W, h: 0.78,
    fill: { color: C.primary }, line: { color: C.primary },
  });
  // Accent colour strip on left edge
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.22, h: H,
    fill: { color: C.accent }, line: { color: C.accent },
  });
  // Right decorative circle (subtle)
  slide.addShape("ellipse", {
    x: 8.5, y: -0.6, w: 2.2, h: 2.2,
    fill: { color: C.accentMid, transparency: 88 },
    line: { color: C.accentMid, transparency: 85, width: 1 },
  });
  slide.addText(title, {
    x: 0.42, y: 0.08, w: W - 0.6, h: 0.52,
    fontSize: 20, bold: true, color: C.white,
    fontFace: FONT_TITLE, valign: "middle", margin: 0,
  });
  if (subtitle) {
    slide.addText(subtitle, {
      x: 0.42, y: 0.60, w: W - 0.6, h: 0.22,
      fontSize: 9, color: C.accentAlt, fontFace: FONT_BODY,
      italic: true, valign: "top", margin: 0,
    });
  }
}

/** White card with left accent stripe */
function card(slide, x, y, w, h, label, value, accentColor) {
  const ac = accentColor || C.accent;
  slide.addShape("rect", {
    x, y, w, h,
    fill: { color: C.white }, line: { color: C.border, width: 0.75 },
    shadow: mkShadow(),
  });
  slide.addShape("rect", {
    x, y, w: 0.06, h,
    fill: { color: ac }, line: { color: ac },
  });
  if (label) {
    slide.addText(label.toUpperCase(), {
      x: x + 0.12, y: y + 0.08, w: w - 0.2, h: 0.22,
      fontSize: 7.5, bold: true, color: ac,
      fontFace: FONT_BODY, charSpacing: 0.5, margin: 0,
    });
  }
  if (value) {
    slide.addText(value, {
      x: x + 0.12,
      y: y + (label ? 0.32 : 0.10),
      w: w - 0.20,
      h: h - (label ? 0.40 : 0.18),
      fontSize: 11.5, color: C.dark, fontFace: FONT_BODY,
      valign: "top", margin: 0, wrap: true,
    });
  }
}

/**
 * ✅ FIXED bulletList — was using invalid { type:"bullet", indent:15 } object.
 * PptxGenJS only accepts bullet: true  OR  bullet: { type:"number" }
 */
function bulletList(slide, items, x, y, w, h, opts = {}) {
  if (!items || items.length === 0) return;
  const richText = items.map((item, i) => {
    const text = typeof item === "string"
      ? item
      : (item.risk || item.phase || item.step || item.description || JSON.stringify(item));
    return {
      text,
      options: {
        bullet: true,               // ← FIXED: was { type:"bullet", indent:15 } — invalid
        breakLine: i < items.length - 1,
        fontSize: opts.fontSize || 12,
        color: opts.color || C.dark,
        fontFace: FONT_BODY,
      },
    };
  });
  slide.addText(richText, {
    x, y, w, h,
    valign: "top",
    margin: [4, 6, 4, 8],
    paraSpaceAfter: opts.paraSpaceAfter !== undefined ? opts.paraSpaceAfter : 5,
  });
}

/** Small ALL-CAPS section label */
function sectionLabel(slide, text, x, y, w) {
  slide.addText(text.toUpperCase(), {
    x, y, w, h: 0.24,
    fontSize: 8.5, bold: true, color: C.accent,
    fontFace: FONT_BODY, charSpacing: 0.5, margin: 0,
  });
}

/** Footer strip on content slides */
function addFooter(slide, text) {
  slide.addShape("rect", {
    x: 0.22, y: H - 0.22, w: W - 0.22, h: 0.22,
    fill: { color: C.lightMid }, line: { color: C.lightMid },
  });
  slide.addText(text || "AI Solution Architect  ·  Confidential", {
    x: 0.38, y: H - 0.21, w: W - 0.5, h: 0.18,
    fontSize: 7.5, color: C.muted, fontFace: FONT_BODY,
    italic: true, margin: 0,
  });
}

// ─── Slide 1 — Title ──────────────────────────────────────────────────────────

function addTitleSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.primary };

  // Large decorative circles — top right
  slide.addShape("ellipse", {
    x: 6.5, y: -1.2, w: 5.5, h: 5.5,
    fill: { color: C.accent, transparency: 85 },
    line: { color: C.accent, transparency: 80, width: 1 },
  });
  slide.addShape("ellipse", {
    x: 8.2, y: 3.4, w: 3.0, h: 3.0,
    fill: { color: C.accentAlt, transparency: 90 },
    line: { color: C.accentAlt, transparency: 85, width: 1 },
  });
  // Bottom-left decorative circle
  slide.addShape("ellipse", {
    x: -0.8, y: 3.6, w: 3.5, h: 3.5,
    fill: { color: C.accentMid, transparency: 92 },
    line: { color: C.accentMid, transparency: 88, width: 1 },
  });

  // Left accent bar
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.32, h: H,
    fill: { color: C.accent }, line: { color: C.accent },
  });

  const name    = DATA.project?.name    || "Solution Architecture";
  const tagline = DATA.project?.tagline || "High-Level Architecture & Implementation Plan";
  const context = DATA.project?.client_context || "";

  slide.addText("AI SOLUTION ARCHITECT", {
    x: 0.55, y: 1.05, w: 7.5, h: 0.38,
    fontSize: 9.5, bold: true, color: C.accentAlt,
    fontFace: FONT_BODY, charSpacing: 3.5, margin: 0,
  });
  slide.addText(name, {
    x: 0.55, y: 1.48, w: 8.2, h: 1.85,
    fontSize: 40, bold: true, color: C.white,
    fontFace: FONT_TITLE, valign: "top", margin: 0,
  });
  // Lavender divider line
  slide.addShape("rect", {
    x: 0.55, y: 3.38, w: 3.2, h: 0.04,
    fill: { color: C.accentAlt }, line: { color: C.accentAlt },
  });
  slide.addText(tagline, {
    x: 0.55, y: 3.5, w: 8.0, h: 0.62,
    fontSize: 15, color: C.accentAlt,
    fontFace: FONT_BODY, italic: true, margin: 0,
  });
  if (context) {
    slide.addText(context, {
      x: 0.55, y: 4.18, w: 7.5, h: 0.45,
      fontSize: 11, color: C.white, fontFace: FONT_BODY,
      transparency: 15, margin: 0,
    });
  }
  // Footer
  slide.addShape("rect", {
    x: 0, y: H - 0.4, w: W, h: 0.4,
    fill: { color: "000000", transparency: 72 },
    line: { color: "000000", transparency: 72 },
  });
  slide.addText("CONFIDENTIAL  ·  Generated by AI Solution Architect", {
    x: 0.55, y: H - 0.36, w: 9, h: 0.30,
    fontSize: 8.5, color: C.accentAlt, fontFace: FONT_BODY, margin: 0,
  });
}

// ─── Slide 2 — Executive Summary ─────────────────────────────────────────────

function addExecSummarySlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Executive Summary");

  const a       = DATA.alignment          || {};
  const sol     = DATA.proposed_solution  || {};
  const goals   = a.goals                 || [];
  const metrics = a.success_metrics       || [];
  const bizVal  = a.business_value        || "";
  const solSum  = sol.summary             || "";

  // Hero banner — solution summary
  const bannerText = solSum || bizVal;
  if (bannerText) {
    slide.addShape("rect", {
      x: 0.32, y: 0.9, w: W - 0.54, h: 0.68,
      fill: { color: C.light }, line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    slide.addShape("rect", {
      x: 0.32, y: 0.9, w: 0.06, h: 0.68,
      fill: { color: C.accent }, line: { color: C.accent },
    });
    slide.addText(bannerText, {
      x: 0.5, y: 0.93, w: W - 0.76, h: 0.60,
      fontSize: 13, color: C.primary, fontFace: FONT_BODY,
      bold: true, valign: "middle", margin: [0, 8, 0, 8], wrap: true,
    });
  }

  const col2Start = 4.72;
  const dividerX  = 4.58;

  // Goals
  sectionLabel(slide, "Strategic Goals", 0.42, 1.72, 4.0);
  if (goals.length > 0) {
    bulletList(slide, goals.slice(0, 5), 0.42, 1.98, 4.0, 3.08, { fontSize: 11.5 });
  } else {
    slide.addText("No goals defined.", {
      x: 0.42, y: 1.98, w: 4.0, h: 0.4,
      fontSize: 11, color: C.muted, italic: true, fontFace: FONT_BODY, margin: 0,
    });
  }

  // Vertical divider
  slide.addShape("rect", {
    x: dividerX, y: 1.72, w: 0.02, h: 3.55,
    fill: { color: C.border }, line: { color: C.border },
  });

  // Success metrics
  sectionLabel(slide, "Success Metrics", col2Start, 1.72, 5.0);
  if (metrics.length > 0) {
    bulletList(slide, metrics.slice(0, 5), col2Start, 1.98, 5.1, 3.08, { fontSize: 11.5 });
  } else {
    slide.addText("No metrics defined.", {
      x: col2Start, y: 1.98, w: 4.8, h: 0.4,
      fontSize: 11, color: C.muted, italic: true, fontFace: FONT_BODY, margin: 0,
    });
  }

  // Business value footer note
  if (bizVal && solSum) {
    slide.addText(`Business Value: ${bizVal}`, {
      x: 0.42, y: H - 0.42, w: W - 0.6, h: 0.28,
      fontSize: 9.5, color: C.muted, fontFace: FONT_BODY,
      italic: true, margin: 0,
    });
  }

  addFooter(slide);
}

// ─── Slide 3 — Problem Statement ─────────────────────────────────────────────

function addProblemSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Problem Statement & Business Context");

  const ps      = DATA.problem_statement || {};
  const pains   = ps.current_pain_points || [];
  const impact  = ps.impact              || "";
  const rootCause = ps.root_cause        || "";

  sectionLabel(slide, "Current Pain Points", 0.42, 0.94, 9.0);

  if (pains.length > 0) {
    // Render pain points as numbered cards in a 2-column grid
    const cardW = 4.4, cardH = 0.70, gapX = 0.3, gapY = 0.1;
    const cols  = [0.42, 5.18];
    const startY = 1.22;
    const maxPains = 6;

    pains.slice(0, maxPains).forEach((pain, i) => {
      const col  = i % 2;
      const row  = Math.floor(i / 2);
      const x    = cols[col];
      const y    = startY + row * (cardH + gapY);
      const ac   = i % 3 === 0 ? C.accent : i % 3 === 1 ? C.accentMid : C.accentAlt;

      slide.addShape("rect", {
        x, y, w: cardW, h: cardH,
        fill: { color: C.white }, line: { color: C.border, width: 0.75 },
        shadow: mkShadow(),
      });
      // Number bubble
      slide.addShape("ellipse", {
        x: x + 0.1, y: y + 0.15, w: 0.38, h: 0.38,
        fill: { color: ac }, line: { color: ac },
      });
      slide.addText(String(i + 1), {
        x: x + 0.1, y: y + 0.15, w: 0.38, h: 0.38,
        fontSize: 10.5, bold: true, color: C.white,
        fontFace: FONT_BODY, align: "center", valign: "middle", margin: 0,
      });
      slide.addText(pain, {
        x: x + 0.58, y: y + 0.10, w: cardW - 0.72, h: cardH - 0.18,
        fontSize: 11, color: C.dark, fontFace: FONT_BODY,
        valign: "middle", wrap: true, margin: 0,
      });
    });
  } else {
    slide.addText("No pain points specified.", {
      x: 0.42, y: 1.22, w: 9, h: 0.4,
      fontSize: 12, color: C.muted, italic: true, fontFace: FONT_BODY, margin: 0,
    });
  }

  // Impact + Root cause cards at bottom
  if (impact) {
    card(slide, 0.42, 4.12, 4.38, 1.08, "Business Impact", impact, C.danger);
  }
  if (rootCause) {
    card(slide, 5.18, 4.12, 4.42, 1.08, "Root Cause", rootCause, C.warning);
  }

  addFooter(slide);
}

// ─── Slide 4 — Proposed Solution Overview ────────────────────────────────────

function addSolutionSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Proposed Solution Overview");

  const sol  = DATA.proposed_solution || {};
  const arch = DATA.architecture      || {};
  const diff = sol.key_differentiators || [];
  const approach = sol.approach        || "";
  const summary  = sol.summary         || "";

  // Hero banner
  if (summary) {
    slide.addShape("rect", {
      x: 0.32, y: 0.9, w: W - 0.54, h: 0.65,
      fill: { color: C.light }, line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    slide.addShape("rect", {
      x: 0.32, y: 0.9, w: 0.06, h: 0.65,
      fill: { color: C.accent }, line: { color: C.accent },
    });
    slide.addText(summary, {
      x: 0.50, y: 0.93, w: W - 0.76, h: 0.58,
      fontSize: 12.5, color: C.primary, bold: true,
      fontFace: FONT_BODY, valign: "middle", margin: [0, 4, 0, 4], wrap: true,
    });
  }

  // Key differentiators
  sectionLabel(slide, "Key Differentiators", 0.42, 1.68, 5.2);
  if (diff.length > 0) {
    bulletList(slide, diff.slice(0, 5), 0.42, 1.94, 5.2, 2.35, { fontSize: 11.5 });
  } else {
    slide.addText("No differentiators specified.", {
      x: 0.42, y: 1.94, w: 5.2, h: 0.4,
      fontSize: 11, color: C.muted, italic: true, fontFace: FONT_BODY, margin: 0,
    });
  }

  // Approach card (right column)
  if (approach) {
    card(slide, 5.88, 1.68, 3.72, 2.60, "Approach", approach, C.accent);
  }

  // Architecture pattern pill
  if (arch.pattern) {
    slide.addShape("rect", {
      x: 0.42, y: 4.44, w: W - 0.64, h: 0.75,
      fill: { color: C.white }, line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    slide.addShape("rect", {
      x: 0.42, y: 4.44, w: 0.06, h: 0.75,
      fill: { color: C.accentMid }, line: { color: C.accentMid },
    });
    slide.addText("ARCHITECTURE PATTERN", {
      x: 0.60, y: 4.49, w: 4, h: 0.22,
      fontSize: 7.5, bold: true, color: C.accentMid,
      fontFace: FONT_BODY, charSpacing: 0.5, margin: 0,
    });
    slide.addText(arch.pattern, {
      x: 0.60, y: 4.72, w: W - 0.82, h: 0.40,
      fontSize: 13, color: C.primary, bold: true,
      fontFace: FONT_BODY, margin: 0,
    });
  }

  addFooter(slide);
}


// ─── Slide 5 — Architecture Diagram (draw.io → Puppeteer → PNG) ──────────────

function addDiagramSlide(pres, imgBase64) {
  const slide = pres.addSlide();
  slide.background = { color: C.dark };

  // Accent strip
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.22, h: H,
    fill: { color: C.accent }, line: { color: C.accent },
  });
  // Header
  slide.addShape("rect", {
    x: 0.22, y: 0, w: W - 0.22, h: 0.72,
    fill: { color: C.primary }, line: { color: C.primary },
  });
  // Decorative circle
  slide.addShape("ellipse", {
    x: 8.5, y: -0.5, w: 2.0, h: 2.0,
    fill: { color: C.accent, transparency: 88 },
    line: { color: C.accent, transparency: 85, width: 1 },
  });
  slide.addText("HIGH-LEVEL ARCHITECTURE DIAGRAM", {
    x: 0.42, y: 0.10, w: W - 0.6, h: 0.54,
    fontSize: 18, bold: true, color: C.white,
    fontFace: FONT_TITLE, valign: "middle", margin: 0,
  });

  // Diagram image — always present (main() throws loudly if generation fails)
  slide.addImage({
    data: imgBase64,
    x: 0.28, y: 0.80, w: W - 0.44, h: 4.52,
    sizing: { type: "contain", w: W - 0.44, h: 4.52 },
  });

  slide.addText("Architecture diagram rendered locally via draw.io  ·  AI Solution Architect", {
    x: 0.42, y: H - 0.28, w: W - 0.5, h: 0.22,
    fontSize: 7.5, color: C.muted, fontFace: FONT_BODY,
    italic: true, align: "center", margin: 0,
  });
}

// ─── Slide 6 — Component Breakdown ───────────────────────────────────────────

function addComponentsSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Component Breakdown");

  const arch       = DATA.architecture || {};
  const components = arch.components   || [];

  if (components.length === 0) {
    // Fallback: show architecture key–value pairs when no components array
    const pairs = [
      ["Frontend",    arch.frontend],
      ["Backend",     arch.backend],
      ["AI Layer",    arch.ai_layer],
      ["Data Store",  arch.data_store],
      ["Hosting",     arch.hosting],
    ].filter(([, v]) => v);

    const colW = 4.5, colH = 0.88, gap = 0.12;
    const cols = [0.32, 5.18];
    pairs.forEach(([label, value], i) => {
      card(slide, cols[i % 2], 0.95 + Math.floor(i / 2) * (colH + gap), colW, colH, label, value);
    });
    addFooter(slide);
    return;
  }

  const maxComp = 8;
  const shown   = components.slice(0, maxComp);
  const colW = 4.5, colH = 1.0, gap = 0.1;
  const cols = [0.32, 5.18];
  const startY = 0.92;

  shown.forEach((comp, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x   = cols[col];
    const y   = startY + row * (colH + gap);
    const ac  = col === 0 ? C.accent : C.accentMid;

    slide.addShape("rect", {
      x, y, w: colW, h: colH,
      fill: { color: C.white }, line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    slide.addShape("rect", {
      x, y, w: 0.06, h: colH,
      fill: { color: ac }, line: { color: ac },
    });
    // Support both {name,role,technology} and {id,label} shapes from LLM
    const compName = comp.name || comp.label || comp.id || "Component";
    const compRole = comp.role || "";
    const compTech = comp.technology || "";
    // Name
    slide.addText(compName, {
      x: x + 0.12, y: y + 0.08, w: colW - 0.22, h: 0.26,
      fontSize: 12, bold: true, color: C.primary,
      fontFace: FONT_BODY, margin: 0,
    });
    // Technology badge
    if (compTech) {
      slide.addShape("rect", {
        x: x + 0.12, y: y + 0.36, w: Math.min(compTech.length * 0.08 + 0.2, colW - 0.28), h: 0.22,
        fill: { color: C.lightMid }, line: { color: C.border, width: 0.5 },
      });
      slide.addText(compTech, {
        x: x + 0.16, y: y + 0.38, w: colW - 0.32, h: 0.18,
        fontSize: 8.5, color: ac, bold: true,
        fontFace: FONT_BODY, margin: 0,
      });
    }
    // Role
    if (compRole) {
      slide.addText(compRole, {
        x: x + 0.12, y: y + (compTech ? 0.62 : 0.38), w: colW - 0.22, h: 0.32,
        fontSize: 10.5, color: C.mutedDark,
        fontFace: FONT_BODY, margin: 0, wrap: true,
      });
    }
  });

  if (components.length > maxComp) {
    slide.addText(`+ ${components.length - maxComp} more components — see architecture JSON`, {
      x: 0.32, y: H - 0.38, w: W - 0.5, h: 0.24,
      fontSize: 9, color: C.muted, italic: true, fontFace: FONT_BODY, margin: 0,
    });
  }

  addFooter(slide);
}

// ─── Slide 7 — Data Flow ──────────────────────────────────────────────────────

function addDataFlowSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Data Flow & System Flow");

  const steps = (DATA.data_flow || []).slice(0, 8);

  if (steps.length === 0) {
    slide.addText("No data flow steps defined in the architecture JSON.", {
      x: 0.5, y: 2.5, w: 9, h: 0.5,
      fontSize: 13, color: C.muted, align: "center",
      fontFace: FONT_BODY, margin: 0, italic: true,
    });
    addFooter(slide);
    return;
  }

  const stepH  = 0.54;
  const gapY   = 0.08;
  const startY = 0.94;

  if (steps.length <= 4) {
    // Single column — large cards
    steps.forEach((step, i) => {
      const label = typeof step === "string" ? step : (step.step || step.description || JSON.stringify(step));
      const y = startY + i * (stepH + gapY);
      const ac = i % 2 === 0 ? C.accent : C.accentMid;

      slide.addShape("rect", {
        x: 0.68, y, w: 9.0, h: stepH,
        fill: { color: i % 2 === 0 ? C.white : C.light },
        line: { color: C.border, width: 0.5 }, shadow: mkShadow(),
      });
      // Number bubble
      slide.addShape("ellipse", {
        x: 0.28, y: y + 0.07, w: 0.40, h: 0.40,
        fill: { color: ac }, line: { color: ac },
      });
      slide.addText(String(i + 1), {
        x: 0.28, y: y + 0.07, w: 0.40, h: 0.40,
        fontSize: 11.5, bold: true, color: C.white,
        fontFace: FONT_BODY, align: "center", valign: "middle", margin: 0,
      });
      slide.addText(label, {
        x: 0.88, y: y + 0.10, w: 8.6, h: 0.34,
        fontSize: 12, color: C.dark, fontFace: FONT_BODY,
        valign: "middle", margin: 0, wrap: true,
      });
      // Connector arrow
      if (i < steps.length - 1) {
        slide.addShape("line", {
          x: 0.48, y: y + stepH, w: 0, h: gapY,
          line: { color: C.accentAlt, width: 1.5, dashType: "sysDot" },
        });
      }
    });
  } else {
    // 2-column layout
    const half   = Math.ceil(steps.length / 2);
    const xBases = [0.32, 5.18];
    [steps.slice(0, half), steps.slice(half)].forEach((col, colIdx) => {
      col.forEach((step, rowIdx) => {
        const globalIdx = colIdx === 0 ? rowIdx : half + rowIdx;
        const label = typeof step === "string" ? step : (step.step || step.description || JSON.stringify(step));
        const xBase = xBases[colIdx];
        const y = startY + rowIdx * (stepH + gapY);
        const ac = globalIdx % 2 === 0 ? C.accent : C.accentMid;

        slide.addShape("rect", {
          x: xBase + 0.42, y, w: 4.3, h: stepH,
          fill: { color: globalIdx % 2 === 0 ? C.white : C.light },
          line: { color: C.border, width: 0.5 }, shadow: mkShadow(),
        });
        slide.addShape("ellipse", {
          x: xBase + 0.08, y: y + 0.07, w: 0.36, h: 0.36,
          fill: { color: ac }, line: { color: ac },
        });
        slide.addText(String(globalIdx + 1), {
          x: xBase + 0.08, y: y + 0.07, w: 0.36, h: 0.36,
          fontSize: 10, bold: true, color: C.white,
          fontFace: FONT_BODY, align: "center", valign: "middle", margin: 0,
        });
        slide.addText(label, {
          x: xBase + 0.55, y: y + 0.10, w: 4.0, h: 0.34,
          fontSize: 11, color: C.dark, fontFace: FONT_BODY,
          valign: "middle", margin: 0, wrap: true,
        });
      });
    });
  }

  addFooter(slide);
}

// ─── Slide 8 — Technology Stack ───────────────────────────────────────────────

function addTechStackSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Technology Stack");

  const ts = DATA.technology_stack || {};
  const layerDefs = [
    { label: "Frontend",       items: ts.frontend       || [], color: C.accent   },
    { label: "Backend",        items: ts.backend        || [], color: C.info     },
    { label: "AI / ML",        items: ts.ai_ml          || [], color: C.success  },
    { label: "Data",           items: ts.data           || [], color: C.warning  },
    { label: "Infrastructure", items: ts.infrastructure || [], color: C.muted    },
    { label: "Security",       items: ts.security       || [], color: C.danger   },
  ].filter(l => l.items.length > 0);

  if (layerDefs.length === 0) {
    slide.addText("No technology stack defined.", {
      x: 0.5, y: 2.5, w: 9, h: 0.5,
      fontSize: 13, color: C.muted, align: "center",
      fontFace: FONT_BODY, margin: 0, italic: true,
    });
    addFooter(slide);
    return;
  }

  const colW = 3.0, boxH = 1.42, gap = 0.12;
  const cols  = [0.32, 3.52, 6.72];
  let col = 0, row = 0;

  layerDefs.forEach((layer) => {
    const x = cols[col];
    const y = 0.92 + row * (boxH + gap);

    slide.addShape("rect", {
      x, y, w: colW, h: boxH,
      fill: { color: C.white }, line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    // Coloured header band inside the card
    slide.addShape("rect", {
      x, y, w: colW, h: 0.32,
      fill: { color: layer.color }, line: { color: layer.color },
    });
    slide.addText(layer.label.toUpperCase(), {
      x: x + 0.1, y: y + 0.05, w: colW - 0.2, h: 0.22,
      fontSize: 8.5, bold: true, color: C.white,
      fontFace: FONT_BODY, charSpacing: 0.5, margin: 0,
    });
    // Tech items as joined text with dividers
    const techItems = layer.items.slice(0, 5);
    // Render each tech item as a small pill/badge row
    const richItems = techItems.map((t, ti) => ({
      text: t + (ti < techItems.length - 1 ? "  ·  " : ""),
      options: {
        fontSize: 11,
        color: C.dark,
        fontFace: FONT_BODY,
      },
    }));
    slide.addText(richItems, {
      x: x + 0.1, y: y + 0.36, w: colW - 0.2, h: boxH - 0.44,
      valign: "top", wrap: true, margin: [2, 4, 2, 4],
    });

    col++;
    if (col >= 3) { col = 0; row++; }
  });

  addFooter(slide);
}

// ─── Slide 9 — Key Features & Capabilities ────────────────────────────────────

function addFeaturesSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Key Features & Capabilities");

  const sol  = DATA.proposed_solution || {};
  const diff = sol.key_differentiators || [];
  const goals = DATA.alignment?.goals  || [];

  // Combine differentiators and goals; deduplicate
  const seen     = new Set();
  const features = [...diff, ...goals].filter((f) => {
    const key = String(f).trim().toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return Boolean(f);
  });

  if (features.length === 0) {
    slide.addText("No features or capabilities defined.", {
      x: 0.5, y: 2.5, w: 9, h: 0.5,
      fontSize: 13, color: C.muted, align: "center",
      fontFace: FONT_BODY, margin: 0, italic: true,
    });
    addFooter(slide);
    return;
  }

  const renderFeatures = (items, xBase, colW) => {
    items.slice(0, 6).forEach((item, i) => {
      const y  = 0.94 + i * 0.74;
      const ac = i % 3 === 0 ? C.accent : i % 3 === 1 ? C.accentMid : C.accentAlt;

      slide.addShape("rect", {
        x: xBase, y, w: colW, h: 0.64,
        fill: { color: C.white }, line: { color: C.border, width: 0.75 },
        shadow: mkShadow(),
      });
      slide.addShape("rect", {
        x: xBase, y, w: 0.06, h: 0.64,
        fill: { color: ac }, line: { color: ac },
      });
      slide.addText(item, {
        x: xBase + 0.14, y: y + 0.10, w: colW - 0.22, h: 0.44,
        fontSize: 11.5, color: C.dark, fontFace: FONT_BODY,
        valign: "middle", margin: 0, wrap: true,
      });
    });
  };

  if (features.length <= 6) {
    renderFeatures(features, 0.32, 9.36);
  } else {
    const half = Math.ceil(features.length / 2);
    renderFeatures(features.slice(0, half), 0.32, 4.5);
    renderFeatures(features.slice(half), 5.14, 4.5);
  }

  addFooter(slide);
}

// ─── Slide 10 — Non-Functional Requirements ──────────────────────────────────

function addNFRSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Non-Functional Requirements");

  const nf = DATA.non_functional || {};
  const nfrs = [
    { label: "Scalability",  value: nf.scalability  || "", color: C.accent    },
    { label: "Security",     value: nf.security     || "", color: C.danger    },
    { label: "Availability", value: nf.availability || "", color: C.success   },
    { label: "Performance",  value: nf.performance  || "", color: C.warning   },
    { label: "Compliance",   value: nf.compliance   || "", color: C.info      },
  ].filter(n => n.value);

  if (nfrs.length === 0) {
    slide.addText("Non-functional requirements not specified.", {
      x: 0.5, y: 2.5, w: 9, h: 0.5,
      fontSize: 13, color: C.muted, align: "center",
      fontFace: FONT_BODY, margin: 0, italic: true,
    });
    addFooter(slide);
    return;
  }

  const cardW = 4.52, cardH = 1.02, gap = 0.14;
  const cols   = [0.32, 5.14];
  const startY = 0.94;

  nfrs.forEach((nfr, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x   = cols[col];
    const y   = startY + row * (cardH + gap);

    slide.addShape("rect", {
      x, y, w: cardW, h: cardH,
      fill: { color: C.white }, line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    // Top colour accent
    slide.addShape("rect", {
      x, y, w: cardW, h: 0.28,
      fill: { color: nfr.color }, line: { color: nfr.color },
    });
    slide.addText(nfr.label.toUpperCase(), {
      x: x + 0.1, y: y + 0.04, w: cardW - 0.18, h: 0.20,
      fontSize: 8, bold: true, color: C.white,
      fontFace: FONT_BODY, charSpacing: 0.5, margin: 0,
    });
    slide.addText(nfr.value, {
      x: x + 0.1, y: y + 0.32, w: cardW - 0.18, h: cardH - 0.40,
      fontSize: 11.5, color: C.dark, fontFace: FONT_BODY,
      valign: "top", wrap: true, margin: 0,
    });
  });

  addFooter(slide);
}

// ─── Slide 11 — Implementation Roadmap ───────────────────────────────────────

function addRoadmapSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Implementation Roadmap");

  const phases = (DATA.roadmap || []).slice(0, 3);

  if (phases.length === 0) {
    slide.addText("Roadmap not defined.", {
      x: 0.5, y: 2.5, w: 9, h: 0.5,
      fontSize: 13, color: C.muted, align: "center",
      fontFace: FONT_BODY, margin: 0, italic: true,
    });
    addFooter(slide);
    return;
  }

  const phaseColors = [C.success, C.accent, C.info];
  // Available content height (below header, above footer)
  const startY  = 0.92;
  const endY    = H - 0.30;
  const phaseH  = endY - startY;
  const totalW  = W - 0.32 - 0.32;        // 9.36"
  const phaseW  = (totalW - 0.15 * (phases.length - 1)) / phases.length;
  const startX  = 0.32;

  phases.forEach((phase, i) => {
    const x     = startX + i * (phaseW + 0.15);
    const color = phaseColors[i] || C.accent;

    // Phase card background
    slide.addShape("rect", {
      x, y: startY, w: phaseW, h: phaseH,
      fill: { color: C.white }, line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    // Phase header
    slide.addShape("rect", {
      x, y: startY, w: phaseW, h: 0.58,
      fill: { color }, line: { color },
    });
    slide.addText(phase.phase || `Phase ${i + 1}`, {
      x: x + 0.1, y: startY + 0.04, w: phaseW - 0.14, h: 0.30,
      fontSize: 10, bold: true, color: C.white,
      fontFace: FONT_BODY, valign: "middle", margin: 0, wrap: true,
    });
    if (phase.duration) {
      slide.addText(phase.duration, {
        x: x + 0.1, y: startY + 0.34, w: phaseW - 0.14, h: 0.20,
        fontSize: 8.5, color: C.white, fontFace: FONT_BODY,
        italic: true, margin: 0,
      });
    }

    // Deliverables — max 5 to stay inside card
    const deliverables = (phase.deliverables || []).slice(0, 5);
    const delivH  = 0.48;
    const delivGap = 0.08;
    const delivStartY = startY + 0.66;

    deliverables.forEach((d, di) => {
      const dy = delivStartY + di * (delivH + delivGap);
      // Safety: don't draw outside the card
      if (dy + delivH > startY + phaseH - 0.04) return;

      slide.addShape("rect", {
        x: x + 0.1, y: dy, w: phaseW - 0.2, h: delivH,
        fill: { color: C.light }, line: { color: C.border, width: 0.5 },
      });
      // Small coloured dot
      slide.addShape("ellipse", {
        x: x + 0.16, y: dy + 0.14, w: 0.18, h: 0.18,
        fill: { color }, line: { color },
      });
      slide.addText(d, {
        x: x + 0.40, y: dy + 0.06, w: phaseW - 0.56, h: delivH - 0.10,
        fontSize: 9.5, color: C.dark, fontFace: FONT_BODY,
        valign: "middle", wrap: true, margin: 0,
      });
    });
  });

  addFooter(slide);
}

// ─── Slide 12 — Risks, Assumptions & Open Questions ──────────────────────────

function addRisksSlide(pres) {
  const risks       = DATA.risks          || [];
  const assumptions = DATA.assumptions    || [];
  const questions   = DATA.open_questions || [];
  if (!risks.length && !assumptions.length && !questions.length) return;

  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Risks, Assumptions & Open Questions");

  const sections = [
    { label: "Risks & Mitigation",   items: risks,       x: 0.32,  color: C.danger,  isRisk: true },
    { label: "Assumptions",          items: assumptions, x: 3.54,  color: C.success, isRisk: false },
    { label: "Open Questions",       items: questions,   x: 6.76,  color: C.info,    isRisk: false },
  ];

  const colW   = 3.06;
  const startY = 0.92;
  const colH   = H - startY - 0.30;

  sections.forEach(({ label, items, x, color, isRisk }) => {
    // Card background
    slide.addShape("rect", {
      x, y: startY, w: colW, h: colH,
      fill: { color: C.white }, line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    // Column header
    slide.addShape("rect", {
      x, y: startY, w: colW, h: 0.38,
      fill: { color }, line: { color },
    });
    slide.addText(label.toUpperCase(), {
      x: x + 0.1, y: startY, w: colW - 0.14, h: 0.38,
      fontSize: 9.5, bold: true, color: C.white,
      fontFace: FONT_BODY, valign: "middle", margin: 0, charSpacing: 0.3,
    });

    if (items.length === 0) {
      slide.addText("None identified.", {
        x: x + 0.1, y: startY + 0.44, w: colW - 0.18, h: 0.30,
        fontSize: 11, color: C.muted, italic: true, fontFace: FONT_BODY, margin: 0,
      });
      return;
    }

    if (isRisk) {
      // Risk + mitigation cards
      items.slice(0, 5).forEach((r, i) => {
        const riskText = typeof r === "string" ? r : (r.risk || "");
        const mitText  = typeof r === "object"  ? (r.mitigation || "") : "";
        const cardH    = mitText ? 0.76 : 0.44;
        const ry       = startY + 0.44 + i * (cardH + 0.08);
        if (ry + cardH > startY + colH - 0.06) return;

        slide.addShape("rect", {
          x: x + 0.1, y: ry, w: colW - 0.18, h: cardH,
          fill: { color: C.offwhite }, line: { color: C.border, width: 0.5 },
        });
        slide.addText(riskText, {
          x: x + 0.16, y: ry + 0.05, w: colW - 0.30, h: 0.30,
          fontSize: 10, bold: true, color: C.dark,
          fontFace: FONT_BODY, wrap: true, margin: 0,
        });
        if (mitText) {
          slide.addText(`→ ${mitText}`, {
            x: x + 0.16, y: ry + 0.36, w: colW - 0.30, h: 0.34,
            fontSize: 9.5, color: C.mutedDark,
            fontFace: FONT_BODY, italic: true, wrap: true, margin: 0,
          });
        }
      });
    } else {
      // ✅ FIXED: bulletList now uses bullet: true (not invalid object)
      bulletList(slide, items.slice(0, 7), x + 0.1, startY + 0.44, colW - 0.18, colH - 0.52,
        { fontSize: 11, paraSpaceAfter: 4 });
    }
  });

  addFooter(slide);
}

// ─── Slide 13 — Closing ───────────────────────────────────────────────────────

function addClosingSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.primary };

  // Decorative circles
  slide.addShape("ellipse", {
    x: 6.0, y: -0.9, w: 5.5, h: 5.5,
    fill: { color: C.accent, transparency: 85 },
    line: { color: C.accent, transparency: 80, width: 1 },
  });
  slide.addShape("ellipse", {
    x: -0.8, y: 3.5, w: 4.0, h: 4.0,
    fill: { color: C.accentAlt, transparency: 90 },
    line: { color: C.accentAlt, transparency: 85, width: 1 },
  });
  slide.addShape("ellipse", {
    x: 7.5, y: 3.8, w: 3.0, h: 3.0,
    fill: { color: C.accentMid, transparency: 92 },
    line: { color: C.accentMid, transparency: 88, width: 1 },
  });

  // Left accent bar
  slide.addShape("rect", {
    x: 0, y: 0, w: 0.32, h: H,
    fill: { color: C.accent }, line: { color: C.accent },
  });

  slide.addText("NEXT STEPS", {
    x: 0.55, y: 1.28, w: 7.5, h: 0.38,
    fontSize: 9.5, bold: true, color: C.accentAlt,
    fontFace: FONT_BODY, charSpacing: 3.5, margin: 0,
  });
  slide.addText("Review · Refine · Build", {
    x: 0.55, y: 1.70, w: 8.5, h: 1.30,
    fontSize: 40, bold: true, color: C.white,
    fontFace: FONT_TITLE, margin: 0,
  });
  // Lavender divider
  slide.addShape("rect", {
    x: 0.55, y: 3.06, w: 4.0, h: 0.04,
    fill: { color: C.accentAlt }, line: { color: C.accentAlt },
  });
  slide.addText(
    "This document was generated by the AI Solution Architect pipeline.\n" +
    "All outputs should be reviewed and validated by a qualified solution architect before implementation.",
    {
      x: 0.55, y: 3.2, w: 8.5, h: 1.05,
      fontSize: 12, color: C.accentAlt, fontFace: FONT_BODY,
      italic: true, margin: 0,
    }
  );

  // Footer
  slide.addShape("rect", {
    x: 0, y: H - 0.40, w: W, h: 0.40,
    fill: { color: "000000", transparency: 72 },
    line: { color: "000000", transparency: 72 },
  });
  slide.addText("CONFIDENTIAL  ·  AI Solution Architect", {
    x: 0.55, y: H - 0.36, w: 9, h: 0.30,
    fontSize: 8.5, color: C.accentAlt, fontFace: FONT_BODY, margin: 0,
  });
}


// ─── Main ─────────────────────────────────────────────────────────────────────

(async () => {
  log("[pptx-gen] ═══════════════════════════════════════════════════════════════");
  log("[pptx-gen] Starting PowerPoint generation pipeline...");
  log("[pptx-gen] Project:", DATA.project?.name || "Unknown");

  // ── Step 1: Generate draw.io XML from architecture JSON ──────────────────
  log("[pptx-gen] ─────────────────────────────────────────────────────────────");
  log("[pptx-gen] STEP 1: Generating draw.io XML from architecture JSON...");
  
  const archData = DATA.architecture || {};
  log("[pptx-gen] Architecture components:", (archData.components || []).length);
  log("[pptx-gen] Architecture connections:", (archData.connections || []).length);
  log("[pptx-gen] Diagram components:", (archData.diagram_components || []).length);
  log("[pptx-gen] Diagram connections:", (archData.diagram_connections || []).length);
  
  let drawioXml;
  try {
    drawioXml = generateDrawioXml(DATA);
    log(`[pptx-gen] ✓ draw.io XML generated (${drawioXml.length} chars)`);
    if (drawioXml.length < 200) {
      log("[pptx-gen] WARNING: XML is suspiciously small!");
    }
  } catch (err) {
    console.error(`[pptx-gen] FATAL: draw.io XML generation failed: ${err.message}`);
    process.exit(1);
  }

  // ── Step 2: Render draw.io XML to PNG via Puppeteer (local, no external API) ──
  log("[pptx-gen] ─────────────────────────────────────────────────────────────");
  log("[pptx-gen] STEP 2: Rendering diagram to PNG via local Puppeteer...");
  
  let pngBuffer;
  try {
    pngBuffer = await renderDrawioToPng(drawioXml, { width: 1400, height: 850 });
    log(`[pptx-gen] ✓ PNG render SUCCESS — ${pngBuffer.length} bytes`);
    
    if (pngBuffer.length < 500) {
      console.error("[pptx-gen] WARNING: PNG is very small, diagram may be empty!");
    }
  } catch (err) {
    console.error(`[pptx-gen] FATAL: Puppeteer diagram render failed: ${err.message}`);
    console.error(`[pptx-gen] Stack: ${err.stack}`);
    process.exit(1);
  }

  const diagramB64 = "data:image/png;base64," + pngBuffer.toString("base64");
  log(`[pptx-gen] ✓ PNG encoded as base64 (${diagramB64.length} chars)`);

  // ── Step 3: Build PPTX ───────────────────────────────────────────────────
  log("[pptx-gen] ─────────────────────────────────────────────────────────────");
  log("[pptx-gen] STEP 3: Building PPTX presentation...");
  
  const pres    = new pptxgen();
  pres.layout   = "LAYOUT_16x9";
  pres.title    = DATA.project?.name || "AI Solution Architecture";
  pres.author   = "AI Solution Architect";
  pres.subject  = "High-Level Architecture Document";

  log("[pptx-gen] Adding 13 slides...");
  if (_shouldInclude("Title")) addTitleSlide(pres);
  if (_shouldInclude("ExecSummary")) addExecSummarySlide(pres);
  if (_shouldInclude("Problem")) addProblemSlide(pres);
  if (_shouldInclude("Solution")) addSolutionSlide(pres);
  if (_shouldInclude("Diagram")) addDiagramSlide(pres, diagramB64);   // guaranteed non-null; we exited above if failed
  if (_shouldInclude("Components")) addComponentsSlide(pres);
  if (_shouldInclude("DataFlow")) addDataFlowSlide(pres);
  if (_shouldInclude("TechStack")) addTechStackSlide(pres);
  if (_shouldInclude("Features")) addFeaturesSlide(pres);
  if (_shouldInclude("NFR")) addNFRSlide(pres);
  if (_shouldInclude("Roadmap")) addRoadmapSlide(pres);
  if (_shouldInclude("Risks")) addRisksSlide(pres);
  // Closing slide will be added after any custom slides (insert custom slides before the final Closing)

  // Append any custom slides provided by the user
  try {
    const custom = DATA.custom_slides || [];
    if (Array.isArray(custom) && custom.length > 0) {
      for (const cs of custom) {
        try {
          const title = cs.title || "Custom";
          const bullets = cs.bullets || cs.content || [];
          const slide = pres.addSlide();
          pageBackground(slide);
          headerBand(slide, title);
          // If bullets is an array, render as bullet list; otherwise render as plain text
          if (Array.isArray(bullets)) {
            const items = bullets.map(b => typeof b === 'string' ? b : String(b));
            bulletList(slide, items, 0.6, 1.2, W - 1.2, 2.6, { fontSize: 12 });
          } else {
            slide.addText(String(bullets), { x:0.6, y:1.2, w:W-1.2, h:2, fontSize:14, color:C.dark, fontFace:FONT_BODY });
          }
        } catch (err) {
          console.error("[pptx-gen] Warning: failed to add custom slide:", err.message);
        }
      }
    }
  } catch (err) {
    console.error("[pptx-gen] Warning: custom slides processing failed:", err.message);
  }
  log("[pptx-gen] ✓ All slides added");
  // Add Closing slide last (after custom slides) if requested
  if (_shouldInclude("Closing")) addClosingSlide(pres);

  log("[pptx-gen] Writing PPTX file...");
  await pres.writeFile({ fileName: outputPath });
  log(`[pptx-gen] ✓ Done → ${outputPath}`);
  log("[pptx-gen] ═══════════════════════════════════════════════════════════════");
  process.exit(0);
})();