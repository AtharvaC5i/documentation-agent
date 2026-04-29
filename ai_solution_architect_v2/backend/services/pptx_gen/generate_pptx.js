/**
 * generate_pptx.js  —  AI Solution Architect · PowerPoint Generator
 *
 * Changes in this version:
 *  - Logo added to top-left of every slide (content slides + title + closing)
 *  - Slide titles are now centered in the header band
 *  - Improved visual presentation across all slides
 *
 * Usage: node generate_pptx.js <input.json> <output.pptx>
 */

"use strict";

const fs = require("fs");
const pptxgen = require("pptxgenjs");
const { generateDrawioXml } = require("./drawioGenerator");
const { renderDrawioToPng } = require("./drawioRenderer");
const path = require("path");

// ─── CLI ─────────────────────────────────────────────────────────────────────
const [, , inputPath, outputPath] = process.argv;
if (!inputPath || !outputPath) {
  console.error("Usage: node generate_pptx.js <input.json> <output.pptx>");
  process.exit(1);
}

const DATA = JSON.parse(fs.readFileSync(inputPath, "utf8"));

// ─── Logo Placeholder ─────────────────────────────────────────────────────────
// Replace "logo.png" with the actual path to your logo file.
// The logo is placed in the top-left of every slide.
const image_logo = path.join(__dirname, "logo.png"); // Ensure this path points to your logo image file

// ─── Brand Design System ─────────────────────────────────────────────────────
const C = {
  purpleDim: "4C1D95",
  purple: "5B21B6",
  purpleMid: "7C3AED",
  purpleLight: "A78BFA",
  purpleFaint: "EDE9FE",
  pageBg: "F5F3FF",
  white: "FFFFFF",
  offwhite: "FAFAFE",
  text: "1E1B4B",
  textMuted: "6B7280",
  textFaint: "9CA3AF",
  border: "C4B5FD",
  borderMid: "A78BFA",
  success: "10B981",
  warning: "D97706",
  error: "EF4444",
  info: "2563EB",
};

const FONT_TITLE = "Georgia";
const FONT_BODY = "Calibri";

// Slide canvas (16:9 inches)
const W = 10;
const H = 5.625;

// Logo dimensions and position (top-left, inside the header band)
const LOGO_X = 0.22;
const LOGO_Y = 0.12;
const LOGO_W = 0.56;
const LOGO_H = 0.56;

// ─── Utilities ────────────────────────────────────────────────────────────────
function log(msg) {
  console.error(msg);
}

function _shouldInclude(key) {
  try {
    const sel = DATA.selected_slides;
    if (!sel || !Array.isArray(sel) || sel.length === 0) return true;
    return sel.includes(key);
  } catch (e) {
    return true;
  }
}

const mkShadow = () => ({
  type: "outer",
  blur: 12,
  offset: 4,
  angle: 135,
  color: "000000",
  opacity: 0.1,
});

const mkShadowStrong = () => ({
  type: "outer",
  blur: 18,
  offset: 5,
  angle: 135,
  color: "000000",
  opacity: 0.15,
});

// ─── Logo Helper ──────────────────────────────────────────────────────────────
/**
 * Adds the logo image to the top-left of any slide.
 * Falls back silently if the logo file is missing.
 */
function addLogo(slide, opts = {}) {
  const x = opts.x !== undefined ? opts.x : LOGO_X;
  const y = opts.y !== undefined ? opts.y : LOGO_Y;
  const w = opts.w !== undefined ? opts.w : LOGO_W;
  const h = opts.h !== undefined ? opts.h : LOGO_H;

  try {
    if (fs.existsSync(image_logo)) {
      slide.addImage({
        path: image_logo,
        x,
        y,
        w,
        h,
        sizing: { type: "contain", w, h },
      });
    }
  } catch (e) {
    // Logo file not found — skip silently
  }
}

// ─── Layout Helpers ───────────────────────────────────────────────────────────

/** Light lavender page canvas */
function pageBackground(slide) {
  slide.background = { color: C.pageBg };
}

/**
 * Header band with CENTERED title and logo on the left.
 * Height increased slightly to 0.88" for more breathing room.
 */
function headerBand(slide, title, subtitle) {
  const BAND_H = subtitle ? 1.0 : 0.88;

  // Main purple band
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: W,
    h: BAND_H,
    fill: { color: C.purple },
    line: { color: C.purple },
  });

  // Bottom accent line on the band (purpleMid)
  slide.addShape("rect", {
    x: 0,
    y: BAND_H - 0.05,
    w: W,
    h: 0.05,
    fill: { color: C.purpleMid },
    line: { color: C.purpleMid },
  });

  // Decorative orb — top right
  slide.addShape("ellipse", {
    x: 8.2,
    y: -0.7,
    w: 2.4,
    h: 2.4,
    fill: { color: C.purpleLight, transparency: 84 },
    line: { color: C.purpleLight, transparency: 80, width: 1 },
  });

  // Small secondary orb
  slide.addShape("ellipse", {
    x: 7.2,
    y: -0.2,
    w: 1.2,
    h: 1.2,
    fill: { color: C.purpleFaint, transparency: 80 },
    line: { color: C.purpleFaint, transparency: 78, width: 1 },
  });

  // Logo (top-left inside band)
  addLogo(slide, { x: LOGO_X, y: (BAND_H - LOGO_H) / 2, w: LOGO_W, h: LOGO_H });

  // Centered title text
  // Reserve left space for logo (LOGO_X + LOGO_W + padding = ~0.92")
  const titleX = LOGO_X + LOGO_W + 0.14;
  const titleW = W - titleX - 0.3;

  slide.addText(title, {
    x: titleX,
    y: subtitle ? 0.1 : (BAND_H - 0.48) / 2,
    w: titleW,
    h: 0.48,
    fontSize: 20,
    bold: true,
    color: C.white,
    fontFace: FONT_TITLE,
    align: "center",
    valign: "middle",
    margin: 0,
  });

  if (subtitle) {
    slide.addText(subtitle, {
      x: titleX,
      y: BAND_H - 0.32,
      w: titleW,
      h: 0.26,
      fontSize: 9,
      color: C.purpleLight,
      fontFace: FONT_BODY,
      italic: true,
      align: "center",
      valign: "top",
      margin: 0,
    });
  }

  // Left vertical accent strip (runs full slide height, behind logo area)
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: 0.06,
    h: H,
    fill: { color: C.purpleMid },
    line: { color: C.purpleMid },
  });
}

/**
 * White card — cleaner drop shadow, slightly larger radius feel via thicker border.
 */
function card(slide, x, y, w, h, label, value, accentColor) {
  const ac = accentColor || C.purpleMid;

  slide.addShape("rect", {
    x,
    y,
    w,
    h,
    fill: { color: C.white },
    line: { color: C.border, width: 0.75 },
    shadow: mkShadow(),
  });
  // Top accent stripe (instead of left — cleaner look)
  slide.addShape("rect", {
    x,
    y,
    w,
    h: 0.06,
    fill: { color: ac },
    line: { color: ac },
  });

  if (label) {
    slide.addText(label.toUpperCase(), {
      x: x + 0.14,
      y: y + 0.12,
      w: w - 0.22,
      h: 0.22,
      fontSize: 7.5,
      bold: true,
      color: ac,
      fontFace: FONT_BODY,
      charSpacing: 0.8,
      margin: 0,
    });
  }
  if (value) {
    slide.addText(value, {
      x: x + 0.14,
      y: y + (label ? 0.38 : 0.14),
      w: w - 0.22,
      h: h - (label ? 0.46 : 0.22),
      fontSize: 11,
      color: C.text,
      fontFace: FONT_BODY,
      valign: "top",
      margin: 0,
      wrap: true,
    });
  }
}

/** Bullet list with proper PptxGenJS bullet syntax */
function bulletList(slide, items, x, y, w, h, opts = {}) {
  if (!items || items.length === 0) return;
  const richText = items.map((item, i) => {
    const text =
      typeof item === "string"
        ? item
        : item.risk ||
          item.phase ||
          item.step ||
          item.description ||
          JSON.stringify(item);
    return {
      text,
      options: {
        bullet: { type: "bullet", characterCode: "2022", indent: 10 },
        breakLine: i < items.length - 1,
        fontSize: opts.fontSize || 11.5,
        color: opts.color || C.text,
        fontFace: FONT_BODY,
      },
    };
  });
  slide.addText(richText, {
    x,
    y,
    w,
    h,
    valign: "top",
    margin: [4, 6, 4, 14],
    paraSpaceAfter: opts.paraSpaceAfter !== undefined ? opts.paraSpaceAfter : 6,
    lineSpacingMultiple: 1.1,
  });
}

/** Small ALL-CAPS section label */
function sectionLabel(slide, text, x, y, w) {
  // Subtle underline bar
  slide.addShape("rect", {
    x,
    y: y + 0.21,
    w: Math.min(w, 1.8),
    h: 0.03,
    fill: { color: C.purpleLight },
    line: { color: C.purpleLight },
  });
  slide.addText(text.toUpperCase(), {
    x,
    y,
    w,
    h: 0.24,
    fontSize: 8,
    bold: true,
    color: C.purpleMid,
    fontFace: FONT_BODY,
    charSpacing: 0.8,
    margin: 0,
  });
}

/** Footer strip */
function addFooter(slide, text) {
  slide.addShape("rect", {
    x: 0.06,
    y: H - 0.24,
    w: W - 0.06,
    h: 0.24,
    fill: { color: C.purpleFaint },
    line: { color: C.border, width: 0.5 },
  });
  slide.addText(text || "AI Solution Architect  ·  Confidential", {
    x: 0.24,
    y: H - 0.23,
    w: W - 0.5,
    h: 0.2,
    fontSize: 7.5,
    color: C.textMuted,
    fontFace: FONT_BODY,
    italic: true,
    margin: 0,
  });
}

// ─── Slide 1 — Title ──────────────────────────────────────────────────────────
function addTitleSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.purpleDim };

  // Decorative orbs
  slide.addShape("ellipse", {
    x: 6.0,
    y: -1.6,
    w: 6.5,
    h: 6.5,
    fill: { color: C.purple, transparency: 80 },
    line: { color: C.purple, transparency: 76, width: 1 },
  });
  slide.addShape("ellipse", {
    x: 7.8,
    y: 3.0,
    w: 3.6,
    h: 3.6,
    fill: { color: C.purpleMid, transparency: 86 },
    line: { color: C.purpleMid, transparency: 83, width: 1 },
  });
  slide.addShape("ellipse", {
    x: -1.2,
    y: 3.2,
    w: 4.5,
    h: 4.5,
    fill: { color: C.purpleLight, transparency: 88 },
    line: { color: C.purpleLight, transparency: 85, width: 1 },
  });
  // Small top-left accent dot
  slide.addShape("ellipse", {
    x: 0.55,
    y: 0.18,
    w: 0.7,
    h: 0.7,
    fill: { color: C.purpleLight, transparency: 72 },
    line: { color: C.purpleLight, transparency: 70, width: 1 },
  });

  // Left accent bar
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: 0.32,
    h: H,
    fill: { color: C.purpleMid },
    line: { color: C.purpleMid },
  });

  // Logo — top left, slightly larger on title slide
  addLogo(slide, { x: 0.52, y: 0.22, w: 0.7, h: 0.7 });

  const name = DATA.project?.name || "Solution Architecture";
  const tagline =
    DATA.project?.tagline || "High-Level Architecture & Implementation Plan";
  const context = DATA.project?.client_context || "";

  // Eyebrow
  slide.addText("AI SOLUTION ARCHITECT", {
    x: 0.55,
    y: 1.08,
    w: 7.5,
    h: 0.36,
    fontSize: 9,
    bold: true,
    color: C.purpleLight,
    fontFace: FONT_BODY,
    charSpacing: 4.5,
    margin: 0,
  });
  // Main title — centered
  slide.addText(name, {
    x: 0.55,
    y: 1.52,
    w: 8.8,
    h: 1.9,
    fontSize: 42,
    bold: true,
    color: C.white,
    fontFace: FONT_TITLE,
    align: "center",
    valign: "top",
    margin: 0,
  });
  // Divider
  slide.addShape("rect", {
    x: 2.5,
    y: 3.44,
    w: 5.0,
    h: 0.05,
    fill: { color: C.purpleLight },
    line: { color: C.purpleLight },
  });
  // Tagline — centered
  slide.addText(tagline, {
    x: 0.55,
    y: 3.58,
    w: 8.8,
    h: 0.66,
    fontSize: 15,
    color: C.purpleLight,
    fontFace: FONT_BODY,
    italic: true,
    align: "center",
    margin: 0,
  });
  if (context) {
    slide.addText(context, {
      x: 0.55,
      y: 4.28,
      w: 8.8,
      h: 0.44,
      fontSize: 10.5,
      color: C.white,
      fontFace: FONT_BODY,
      align: "center",
      transparency: 18,
      margin: 0,
    });
  }
  // Confidential footer
  slide.addShape("rect", {
    x: 0,
    y: H - 0.42,
    w: W,
    h: 0.42,
    fill: { color: "000000", transparency: 65 },
    line: { color: "000000", transparency: 65 },
  });
  slide.addText("CONFIDENTIAL  ·  Generated by AI Solution Architect", {
    x: 0.55,
    y: H - 0.38,
    w: 9,
    h: 0.32,
    fontSize: 8,
    color: C.purpleLight,
    fontFace: FONT_BODY,
    align: "center",
    margin: 0,
    charSpacing: 0.5,
  });
}

// ─── Slide 2 — Executive Summary ─────────────────────────────────────────────
function addExecSummarySlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Executive Summary");

  const BAND_H = 0.88;
  const a = DATA.alignment || {};
  const sol = DATA.proposed_solution || {};
  const goals = a.goals || [];
  const metrics = a.success_metrics || [];
  const bizVal = a.business_value || "";
  const solSum = sol.summary || "";

  const bannerText = solSum || bizVal;
  if (bannerText) {
    slide.addShape("rect", {
      x: 0.3,
      y: BAND_H + 0.1,
      w: W - 0.5,
      h: 0.78,
      fill: { color: C.purpleFaint },
      line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    // Left accent bar on banner
    slide.addShape("rect", {
      x: 0.3,
      y: BAND_H + 0.1,
      w: 0.07,
      h: 0.78,
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(bannerText, {
      x: 0.5,
      y: BAND_H + 0.14,
      w: W - 0.74,
      h: 0.68,
      fontSize: 12.5,
      color: C.purpleDim,
      fontFace: FONT_BODY,
      bold: true,
      align: "center",
      valign: "middle",
      margin: [0, 8, 0, 8],
      wrap: true,
    });
  }

  const contentY = BAND_H + (bannerText ? 0.98 : 0.14);
  const col2Start = 5.0;
  const dividerX = 4.86;

  sectionLabel(slide, "Strategic Goals", 0.4, contentY, 4.0);
  if (goals.length > 0) {
    bulletList(slide, goals.slice(0, 5), 0.4, contentY + 0.28, 4.0, 3.0, {
      fontSize: 11,
    });
  } else {
    slide.addText("No goals defined.", {
      x: 0.4,
      y: contentY + 0.28,
      w: 4.0,
      h: 0.36,
      fontSize: 11,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
  }

  // Vertical divider
  slide.addShape("rect", {
    x: dividerX,
    y: contentY,
    w: 0.02,
    h: H - contentY - 0.28,
    fill: { color: C.border },
    line: { color: C.border },
  });

  sectionLabel(slide, "Success Metrics", col2Start, contentY, 5.0);
  if (metrics.length > 0) {
    bulletList(
      slide,
      metrics.slice(0, 5),
      col2Start,
      contentY + 0.28,
      4.8,
      3.0,
      { fontSize: 11 },
    );
  } else {
    slide.addText("No metrics defined.", {
      x: col2Start,
      y: contentY + 0.28,
      w: 4.8,
      h: 0.36,
      fontSize: 11,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
  }

  if (bizVal && solSum) {
    slide.addText(`Business Value: ${bizVal}`, {
      x: 0.4,
      y: H - 0.48,
      w: W - 0.58,
      h: 0.26,
      fontSize: 9,
      color: C.textMuted,
      fontFace: FONT_BODY,
      italic: true,
      margin: 0,
    });
  }

  addFooter(slide);
}

// ─── Slide 3 — Problem Statement ─────────────────────────────────────────────
function addProblemSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Problem Statement & Business Context");

  const BAND_H = 0.88;
  const ps = DATA.problem_statement || {};
  const pains = ps.current_pain_points || [];
  const impact = ps.impact || "";
  const rootCause = ps.root_cause || "";

  sectionLabel(slide, "Current Pain Points", 0.4, BAND_H + 0.1, 9.2);

  if (pains.length > 0) {
    const cardW = 4.44,
      cardH = 0.74,
      gapY = 0.1;
    const cols = [0.3, 5.18];
    const startY = BAND_H + 0.38;
    const accentCycle = [C.purple, C.purpleMid, C.purpleLight];

    pains.slice(0, 6).forEach((pain, i) => {
      const col = i % 2;
      const row = Math.floor(i / 2);
      const x = cols[col];
      const y = startY + row * (cardH + gapY);
      const ac = accentCycle[i % 3];

      slide.addShape("rect", {
        x,
        y,
        w: cardW,
        h: cardH,
        fill: { color: C.white },
        line: { color: C.border, width: 0.75 },
        shadow: mkShadow(),
      });
      // Top accent stripe
      slide.addShape("rect", {
        x,
        y,
        w: cardW,
        h: 0.05,
        fill: { color: ac },
        line: { color: ac },
      });
      // Numbered bubble
      slide.addShape("ellipse", {
        x: x + 0.12,
        y: y + 0.18,
        w: 0.38,
        h: 0.38,
        fill: { color: ac },
        line: { color: ac },
      });
      slide.addText(String(i + 1), {
        x: x + 0.12,
        y: y + 0.18,
        w: 0.38,
        h: 0.38,
        fontSize: 10,
        bold: true,
        color: C.white,
        fontFace: FONT_BODY,
        align: "center",
        valign: "middle",
        margin: 0,
      });
      slide.addText(pain, {
        x: x + 0.62,
        y: y + 0.14,
        w: cardW - 0.76,
        h: cardH - 0.22,
        fontSize: 10.5,
        color: C.text,
        fontFace: FONT_BODY,
        valign: "middle",
        wrap: true,
        margin: 0,
      });
    });
  } else {
    slide.addText("No pain points specified.", {
      x: 0.4,
      y: BAND_H + 0.38,
      w: 9,
      h: 0.4,
      fontSize: 12,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
  }

  if (impact) {
    card(slide, 0.3, 4.1, 4.44, 1.1, "Business Impact", impact, C.error);
  }
  if (rootCause) {
    card(slide, 5.18, 4.1, 4.44, 1.1, "Root Cause", rootCause, C.warning);
  }

  addFooter(slide);
}

// ─── Slide 4 — Proposed Solution Overview ────────────────────────────────────
function addSolutionSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Proposed Solution Overview");

  const BAND_H = 0.88;
  const sol = DATA.proposed_solution || {};
  const arch = DATA.architecture || {};
  const diff = sol.key_differentiators || [];
  const approach = sol.approach || "";
  const summary = sol.summary || "";

  if (summary) {
    slide.addShape("rect", {
      x: 0.3,
      y: BAND_H + 0.1,
      w: W - 0.5,
      h: 0.74,
      fill: { color: C.purpleFaint },
      line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    slide.addShape("rect", {
      x: 0.3,
      y: BAND_H + 0.1,
      w: 0.07,
      h: 0.74,
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(summary, {
      x: 0.5,
      y: BAND_H + 0.14,
      w: W - 0.74,
      h: 0.64,
      fontSize: 12,
      color: C.purpleDim,
      bold: true,
      fontFace: FONT_BODY,
      align: "center",
      valign: "middle",
      margin: [0, 4, 0, 4],
      wrap: true,
    });
  }

  const contentY = BAND_H + (summary ? 0.94 : 0.14);

  sectionLabel(slide, "Key Differentiators", 0.4, contentY, 5.2);
  if (diff.length > 0) {
    bulletList(slide, diff.slice(0, 5), 0.4, contentY + 0.28, 5.2, 2.4, {
      fontSize: 11,
    });
  } else {
    slide.addText("No differentiators specified.", {
      x: 0.4,
      y: contentY + 0.28,
      w: 5.2,
      h: 0.36,
      fontSize: 11,
      color: C.textMuted,
      italic: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
  }

  if (approach) {
    card(slide, 5.98, contentY, 3.66, 2.6, "Approach", approach, C.purpleMid);
  }

  if (arch.pattern) {
    slide.addShape("rect", {
      x: 0.3,
      y: 4.42,
      w: W - 0.5,
      h: 0.82,
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    slide.addShape("rect", {
      x: 0.3,
      y: 4.42,
      w: 0.07,
      h: 0.82,
      fill: { color: C.purpleLight },
      line: { color: C.purpleLight },
    });
    slide.addText("ARCHITECTURE PATTERN", {
      x: 0.5,
      y: 4.48,
      w: 3.8,
      h: 0.22,
      fontSize: 7.5,
      bold: true,
      color: C.purpleLight,
      fontFace: FONT_BODY,
      charSpacing: 0.6,
      margin: 0,
    });
    slide.addText(arch.pattern, {
      x: 0.5,
      y: 4.72,
      w: W - 0.72,
      h: 0.42,
      fontSize: 13,
      color: C.purple,
      bold: true,
      fontFace: FONT_BODY,
      margin: 0,
    });
  }

  addFooter(slide);
}

// ─── Slide 5 — Architecture Diagram ──────────────────────────────────────────
function addDiagramSlide(pres, imgBase64) {
  const slide = pres.addSlide();
  slide.background = { color: C.purpleDim };

  // Left accent strip
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: 0.07,
    h: H,
    fill: { color: C.purpleMid },
    line: { color: C.purpleMid },
  });
  // Header band
  slide.addShape("rect", {
    x: 0.07,
    y: 0,
    w: W - 0.07,
    h: 0.82,
    fill: { color: C.purple },
    line: { color: C.purple },
  });
  // Bottom highlight on band
  slide.addShape("rect", {
    x: 0.07,
    y: 0.77,
    w: W - 0.07,
    h: 0.05,
    fill: { color: C.purpleMid },
    line: { color: C.purpleMid },
  });
  // Decorative orb
  slide.addShape("ellipse", {
    x: 8.2,
    y: -0.6,
    w: 2.6,
    h: 2.6,
    fill: { color: C.purpleLight, transparency: 84 },
    line: { color: C.purpleLight, transparency: 82, width: 1 },
  });

  // Logo
  addLogo(slide, { x: LOGO_X, y: (0.82 - LOGO_H) / 2, w: LOGO_W, h: LOGO_H });

  slide.addText("HIGH-LEVEL ARCHITECTURE DIAGRAM", {
    x: LOGO_X + LOGO_W + 0.14,
    y: 0.14,
    w: W - (LOGO_X + LOGO_W + 0.14) - 0.3,
    h: 0.54,
    fontSize: 18,
    bold: true,
    color: C.white,
    fontFace: FONT_TITLE,
    align: "center",
    valign: "middle",
    margin: 0,
  });

  slide.addImage({
    data: imgBase64,
    x: 0.2,
    y: 0.9,
    w: W - 0.32,
    h: 4.4,
    sizing: { type: "contain", w: W - 0.32, h: 4.4 },
  });

  slide.addText(
    "Architecture diagram rendered via draw.io  ·  AI Solution Architect",
    {
      x: 0.4,
      y: H - 0.3,
      w: W - 0.5,
      h: 0.24,
      fontSize: 7.5,
      color: C.purpleLight,
      fontFace: FONT_BODY,
      italic: true,
      align: "center",
      margin: 0,
    },
  );
}

// ─── Slide 6 — Component Breakdown ───────────────────────────────────────────
function addComponentsSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Component Breakdown");

  const BAND_H = 0.88;
  const arch = DATA.architecture || {};
  const components = arch.components || [];

  if (components.length === 0) {
    const pairs = [
      ["Frontend", arch.frontend],
      ["Backend", arch.backend],
      ["AI Layer", arch.ai_layer],
      ["Data Store", arch.data_store],
      ["Hosting", arch.hosting],
    ].filter(([, v]) => v);

    const colW = 4.5,
      colH = 0.9,
      gap = 0.12;
    const cols = [0.3, 5.18];
    pairs.forEach(([label, value], i) => {
      card(
        slide,
        cols[i % 2],
        BAND_H + 0.1 + Math.floor(i / 2) * (colH + gap),
        colW,
        colH,
        label,
        value,
      );
    });
    addFooter(slide);
    return;
  }

  const maxComp = 8;
  const shown = components.slice(0, maxComp);
  const colW = 4.5,
    colH = 1.04,
    gap = 0.1;
  const cols = [0.3, 5.18];
  const startY = BAND_H + 0.08;

  shown.forEach((comp, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = cols[col];
    const y = startY + row * (colH + gap);
    const ac = col === 0 ? C.purple : C.purpleMid;

    slide.addShape("rect", {
      x,
      y,
      w: colW,
      h: colH,
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    // Top accent stripe
    slide.addShape("rect", {
      x,
      y,
      w: colW,
      h: 0.05,
      fill: { color: ac },
      line: { color: ac },
    });

    const compName = comp.name || comp.label || comp.id || "Component";
    const compRole = comp.role || "";
    const compTech = comp.technology || "";

    slide.addText(compName, {
      x: x + 0.14,
      y: y + 0.1,
      w: colW - 0.24,
      h: 0.26,
      fontSize: 11.5,
      bold: true,
      color: C.purpleDim,
      fontFace: FONT_BODY,
      margin: 0,
    });
    if (compTech) {
      const badgeW = Math.min(compTech.length * 0.082 + 0.28, colW - 0.28);
      slide.addShape("rect", {
        x: x + 0.14,
        y: y + 0.38,
        w: badgeW,
        h: 0.22,
        fill: { color: C.purpleFaint },
        line: { color: C.border, width: 0.5 },
      });
      slide.addText(compTech, {
        x: x + 0.18,
        y: y + 0.4,
        w: badgeW - 0.08,
        h: 0.18,
        fontSize: 8.5,
        color: ac,
        bold: true,
        fontFace: FONT_BODY,
        margin: 0,
      });
    }
    if (compRole) {
      slide.addText(compRole, {
        x: x + 0.14,
        y: y + (compTech ? 0.65 : 0.38),
        w: colW - 0.24,
        h: 0.32,
        fontSize: 10,
        color: C.textMuted,
        fontFace: FONT_BODY,
        margin: 0,
        wrap: true,
      });
    }
  });

  if (components.length > maxComp) {
    slide.addText(
      `+ ${components.length - maxComp} more components — see architecture JSON`,
      {
        x: 0.3,
        y: H - 0.44,
        w: W - 0.5,
        h: 0.24,
        fontSize: 9,
        color: C.textMuted,
        italic: true,
        fontFace: FONT_BODY,
        margin: 0,
      },
    );
  }

  addFooter(slide);
}

// ─── Slide 7 — Data Flow ──────────────────────────────────────────────────────
function addDataFlowSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Data Flow & System Flow");

  const BAND_H = 0.88;
  const steps = (DATA.data_flow || []).slice(0, 8);

  if (steps.length === 0) {
    slide.addText("No data flow steps defined in the architecture JSON.", {
      x: 0.5,
      y: 2.5,
      w: 9,
      h: 0.5,
      fontSize: 13,
      color: C.textMuted,
      align: "center",
      fontFace: FONT_BODY,
      margin: 0,
      italic: true,
    });
    addFooter(slide);
    return;
  }

  const stepH = 0.56;
  const gapY = 0.08;
  const startY = BAND_H + 0.1;

  if (steps.length <= 4) {
    steps.forEach((step, i) => {
      const label =
        typeof step === "string"
          ? step
          : step.step || step.description || JSON.stringify(step);
      const y = startY + i * (stepH + gapY);
      const ac = i % 2 === 0 ? C.purple : C.purpleMid;

      slide.addShape("rect", {
        x: 0.7,
        y,
        w: 8.9,
        h: stepH,
        fill: { color: i % 2 === 0 ? C.white : C.purpleFaint },
        line: { color: C.border, width: 0.5 },
        shadow: mkShadow(),
      });
      // Top accent stripe
      slide.addShape("rect", {
        x: 0.7,
        y,
        w: 8.9,
        h: 0.04,
        fill: { color: ac },
        line: { color: ac },
      });
      // Step bubble
      slide.addShape("ellipse", {
        x: 0.26,
        y: y + 0.09,
        w: 0.42,
        h: 0.42,
        fill: { color: ac },
        line: { color: ac },
      });
      slide.addText(String(i + 1), {
        x: 0.26,
        y: y + 0.09,
        w: 0.42,
        h: 0.42,
        fontSize: 11,
        bold: true,
        color: C.white,
        fontFace: FONT_BODY,
        align: "center",
        valign: "middle",
        margin: 0,
      });
      slide.addText(label, {
        x: 0.9,
        y: y + 0.1,
        w: 8.5,
        h: 0.36,
        fontSize: 11.5,
        color: C.text,
        fontFace: FONT_BODY,
        valign: "middle",
        margin: 0,
        wrap: true,
      });
      // Dotted connector
      if (i < steps.length - 1) {
        slide.addShape("line", {
          x: 0.47,
          y: y + stepH,
          w: 0,
          h: gapY,
          line: { color: C.purpleLight, width: 1.5, dashType: "sysDot" },
        });
      }
    });
  } else {
    const half = Math.ceil(steps.length / 2);
    const xBases = [0.3, 5.18];
    [steps.slice(0, half), steps.slice(half)].forEach((col, colIdx) => {
      col.forEach((step, rowIdx) => {
        const globalIdx = colIdx === 0 ? rowIdx : half + rowIdx;
        const label =
          typeof step === "string"
            ? step
            : step.step || step.description || JSON.stringify(step);
        const xBase = xBases[colIdx];
        const y = startY + rowIdx * (stepH + gapY);
        const ac = globalIdx % 2 === 0 ? C.purple : C.purpleMid;

        slide.addShape("rect", {
          x: xBase + 0.44,
          y,
          w: 4.28,
          h: stepH,
          fill: { color: globalIdx % 2 === 0 ? C.white : C.purpleFaint },
          line: { color: C.border, width: 0.5 },
          shadow: mkShadow(),
        });
        slide.addShape("rect", {
          x: xBase + 0.44,
          y,
          w: 4.28,
          h: 0.04,
          fill: { color: ac },
          line: { color: ac },
        });
        slide.addShape("ellipse", {
          x: xBase + 0.08,
          y: y + 0.1,
          w: 0.36,
          h: 0.36,
          fill: { color: ac },
          line: { color: ac },
        });
        slide.addText(String(globalIdx + 1), {
          x: xBase + 0.08,
          y: y + 0.1,
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
        slide.addText(label, {
          x: xBase + 0.58,
          y: y + 0.1,
          w: 3.92,
          h: 0.36,
          fontSize: 10.5,
          color: C.text,
          fontFace: FONT_BODY,
          valign: "middle",
          margin: 0,
          wrap: true,
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

  const BAND_H = 0.88;
  const ts = DATA.technology_stack || {};
  const layerDefs = [
    { label: "Frontend", items: ts.frontend || [], color: C.purple },
    { label: "Backend", items: ts.backend || [], color: C.purpleMid },
    { label: "AI / ML", items: ts.ai_ml || [], color: C.success },
    { label: "Data", items: ts.data || [], color: C.warning },
    {
      label: "Infrastructure",
      items: ts.infrastructure || [],
      color: C.purpleLight,
    },
    { label: "Security", items: ts.security || [], color: C.error },
  ].filter((l) => l.items.length > 0);

  if (layerDefs.length === 0) {
    slide.addText("No technology stack defined.", {
      x: 0.5,
      y: 2.5,
      w: 9,
      h: 0.5,
      fontSize: 13,
      color: C.textMuted,
      align: "center",
      fontFace: FONT_BODY,
      margin: 0,
      italic: true,
    });
    addFooter(slide);
    return;
  }

  const colW = 3.02,
    boxH = 1.5,
    gap = 0.12;
  const cols = [0.3, 3.5, 6.68];
  let col = 0,
    row = 0;

  layerDefs.forEach((layer) => {
    const x = cols[col];
    const y = BAND_H + 0.08 + row * (boxH + gap);

    slide.addShape("rect", {
      x,
      y,
      w: colW,
      h: boxH,
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    // Coloured header band
    slide.addShape("rect", {
      x,
      y,
      w: colW,
      h: 0.38,
      fill: { color: layer.color },
      line: { color: layer.color },
    });
    slide.addText(layer.label.toUpperCase(), {
      x: x + 0.1,
      y: y + 0.07,
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
    // Tech items
    const techItems = layer.items.slice(0, 5);
    const richItems = techItems.map((t, ti) => ({
      text: t + (ti < techItems.length - 1 ? "  ·  " : ""),
      options: { fontSize: 10.5, color: C.text, fontFace: FONT_BODY },
    }));
    slide.addText(richItems, {
      x: x + 0.1,
      y: y + 0.42,
      w: colW - 0.18,
      h: boxH - 0.52,
      valign: "top",
      wrap: true,
      margin: [2, 4, 2, 4],
      lineSpacingMultiple: 1.15,
    });

    col++;
    if (col >= 3) {
      col = 0;
      row++;
    }
  });

  addFooter(slide);
}

// ─── Slide 9 — Key Features & Capabilities ────────────────────────────────────
function addFeaturesSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Key Features & Capabilities");

  const BAND_H = 0.88;
  const sol = DATA.proposed_solution || {};
  const diff = sol.key_differentiators || [];
  const goals = DATA.alignment?.goals || [];

  const seen = new Set();
  const features = [...diff, ...goals].filter((f) => {
    const key = String(f).trim().toLowerCase();
    if (seen.has(key)) return false;
    seen.add(key);
    return Boolean(f);
  });

  if (features.length === 0) {
    slide.addText("No features or capabilities defined.", {
      x: 0.5,
      y: 2.5,
      w: 9,
      h: 0.5,
      fontSize: 13,
      color: C.textMuted,
      align: "center",
      fontFace: FONT_BODY,
      margin: 0,
      italic: true,
    });
    addFooter(slide);
    return;
  }

  const accentCycle = [C.purple, C.purpleMid, C.purpleLight];

  const renderFeatures = (items, xBase, colW) => {
    items.slice(0, 6).forEach((item, i) => {
      const y = BAND_H + 0.1 + i * 0.76;
      const ac = accentCycle[i % 3];

      slide.addShape("rect", {
        x: xBase,
        y,
        w: colW,
        h: 0.66,
        fill: { color: i % 2 === 0 ? C.white : C.offwhite },
        line: { color: C.border, width: 0.75 },
        shadow: mkShadow(),
      });
      // Top stripe
      slide.addShape("rect", {
        x: xBase,
        y,
        w: colW,
        h: 0.05,
        fill: { color: ac },
        line: { color: ac },
      });
      // Index number
      slide.addShape("ellipse", {
        x: xBase + 0.1,
        y: y + 0.14,
        w: 0.36,
        h: 0.36,
        fill: { color: ac },
        line: { color: ac },
      });
      slide.addText(String(i + 1), {
        x: xBase + 0.1,
        y: y + 0.14,
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
      slide.addText(item, {
        x: xBase + 0.56,
        y: y + 0.1,
        w: colW - 0.66,
        h: 0.46,
        fontSize: 11,
        color: C.text,
        fontFace: FONT_BODY,
        valign: "middle",
        margin: 0,
        wrap: true,
      });
    });
  };

  if (features.length <= 6) {
    renderFeatures(features, 0.3, 9.38);
  } else {
    const half = Math.ceil(features.length / 2);
    renderFeatures(features.slice(0, half), 0.3, 4.52);
    renderFeatures(features.slice(half), 5.14, 4.52);
  }

  addFooter(slide);
}

// ─── Slide 10 — Non-Functional Requirements ──────────────────────────────────
function addNFRSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Non-Functional Requirements");

  const BAND_H = 0.88;
  const nf = DATA.non_functional || {};
  const nfrs = [
    { label: "Scalability", value: nf.scalability || "", color: C.purple },
    { label: "Security", value: nf.security || "", color: C.error },
    { label: "Availability", value: nf.availability || "", color: C.success },
    { label: "Performance", value: nf.performance || "", color: C.warning },
    { label: "Compliance", value: nf.compliance || "", color: C.purpleMid },
  ].filter((n) => n.value);

  if (nfrs.length === 0) {
    slide.addText("Non-functional requirements not specified.", {
      x: 0.5,
      y: 2.5,
      w: 9,
      h: 0.5,
      fontSize: 13,
      color: C.textMuted,
      align: "center",
      fontFace: FONT_BODY,
      margin: 0,
      italic: true,
    });
    addFooter(slide);
    return;
  }

  const cardW = 4.52,
    cardH = 1.08,
    gap = 0.14;
  const cols = [0.3, 5.12];
  const startY = BAND_H + 0.08;

  nfrs.forEach((nfr, i) => {
    const col = i % 2;
    const row = Math.floor(i / 2);
    const x = cols[col];
    const y = startY + row * (cardH + gap);

    slide.addShape("rect", {
      x,
      y,
      w: cardW,
      h: cardH,
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    // Coloured top band
    slide.addShape("rect", {
      x,
      y,
      w: cardW,
      h: 0.34,
      fill: { color: nfr.color },
      line: { color: nfr.color },
    });
    slide.addText(nfr.label.toUpperCase(), {
      x: x + 0.1,
      y: y + 0.06,
      w: cardW - 0.18,
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
      y: y + 0.38,
      w: cardW - 0.22,
      h: cardH - 0.46,
      fontSize: 11,
      color: C.text,
      fontFace: FONT_BODY,
      valign: "top",
      wrap: true,
      margin: 0,
    });
  });

  addFooter(slide);
}

// ─── Slide 11 — Implementation Roadmap ───────────────────────────────────────
function addRoadmapSlide(pres) {
  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Implementation Roadmap");

  const BAND_H = 0.88;
  const phases = (DATA.roadmap || []).slice(0, 3);

  if (phases.length === 0) {
    slide.addText("Roadmap not defined.", {
      x: 0.5,
      y: 2.5,
      w: 9,
      h: 0.5,
      fontSize: 13,
      color: C.textMuted,
      align: "center",
      fontFace: FONT_BODY,
      margin: 0,
      italic: true,
    });
    addFooter(slide);
    return;
  }

  const phaseColors = [C.success, C.purple, C.info];
  const startY = BAND_H + 0.08;
  const endY = H - 0.28;
  const phaseH = endY - startY;
  const totalW = W - 0.62;
  const phaseW = (totalW - 0.16 * (phases.length - 1)) / phases.length;
  const startX = 0.3;

  phases.forEach((phase, i) => {
    const x = startX + i * (phaseW + 0.16);
    const color = phaseColors[i] || C.purple;

    slide.addShape("rect", {
      x,
      y: startY,
      w: phaseW,
      h: phaseH,
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
      shadow: mkShadowStrong(),
    });
    // Phase header
    slide.addShape("rect", {
      x,
      y: startY,
      w: phaseW,
      h: 0.64,
      fill: { color },
      line: { color },
    });
    slide.addText(phase.phase || `Phase ${i + 1}`, {
      x: x + 0.1,
      y: startY + 0.04,
      w: phaseW - 0.14,
      h: 0.32,
      fontSize: 9.5,
      bold: true,
      color: C.white,
      fontFace: FONT_BODY,
      align: "center",
      valign: "middle",
      margin: 0,
      wrap: true,
    });
    if (phase.duration) {
      slide.addText(phase.duration, {
        x: x + 0.1,
        y: startY + 0.38,
        w: phaseW - 0.14,
        h: 0.22,
        fontSize: 8.5,
        color: C.white,
        fontFace: FONT_BODY,
        italic: true,
        align: "center",
        margin: 0,
      });
    }

    const deliverables = (phase.deliverables || []).slice(0, 5);
    const delivH = 0.5;
    const delivGap = 0.08;
    const delivStartY = startY + 0.72;

    deliverables.forEach((d, di) => {
      const dy = delivStartY + di * (delivH + delivGap);
      if (dy + delivH > startY + phaseH - 0.06) return;

      slide.addShape("rect", {
        x: x + 0.1,
        y: dy,
        w: phaseW - 0.2,
        h: delivH,
        fill: { color: C.purpleFaint },
        line: { color: C.border, width: 0.5 },
      });
      // Coloured dot
      slide.addShape("ellipse", {
        x: x + 0.18,
        y: dy + 0.16,
        w: 0.18,
        h: 0.18,
        fill: { color },
        line: { color },
      });
      slide.addText(d, {
        x: x + 0.42,
        y: dy + 0.06,
        w: phaseW - 0.58,
        h: delivH - 0.1,
        fontSize: 9.5,
        color: C.text,
        fontFace: FONT_BODY,
        valign: "middle",
        wrap: true,
        margin: 0,
      });
    });
  });

  addFooter(slide);
}

// ─── Slide 12 — Risks, Assumptions & Open Questions ──────────────────────────
function addRisksSlide(pres) {
  const risks = DATA.risks || [];
  const assumptions = DATA.assumptions || [];
  const questions = DATA.open_questions || [];
  if (!risks.length && !assumptions.length && !questions.length) return;

  const slide = pres.addSlide();
  pageBackground(slide);
  headerBand(slide, "Risks, Assumptions & Open Questions");

  const BAND_H = 0.88;
  const sections = [
    {
      label: "Risks & Mitigation",
      items: risks,
      x: 0.28,
      color: C.error,
      isRisk: true,
    },
    {
      label: "Assumptions",
      items: assumptions,
      x: 3.5,
      color: C.success,
      isRisk: false,
    },
    {
      label: "Open Questions",
      items: questions,
      x: 6.72,
      color: C.purpleMid,
      isRisk: false,
    },
  ];

  const colW = 3.06;
  const startY = BAND_H + 0.08;
  const colH = H - startY - 0.28;

  sections.forEach(({ label, items, x, color, isRisk }) => {
    slide.addShape("rect", {
      x,
      y: startY,
      w: colW,
      h: colH,
      fill: { color: C.white },
      line: { color: C.border, width: 0.75 },
      shadow: mkShadow(),
    });
    // Header
    slide.addShape("rect", {
      x,
      y: startY,
      w: colW,
      h: 0.42,
      fill: { color },
      line: { color },
    });
    slide.addText(label.toUpperCase(), {
      x: x + 0.1,
      y: startY,
      w: colW - 0.14,
      h: 0.42,
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
        y: startY + 0.5,
        w: colW - 0.18,
        h: 0.3,
        fontSize: 10.5,
        color: C.textMuted,
        italic: true,
        fontFace: FONT_BODY,
        margin: 0,
      });
      return;
    }

    if (isRisk) {
      items.slice(0, 5).forEach((r, i) => {
        const riskText = typeof r === "string" ? r : r.risk || "";
        const mitText = typeof r === "object" ? r.mitigation || "" : "";
        const rCardH = mitText ? 0.82 : 0.48;
        const ry = startY + 0.5 + i * (rCardH + 0.08);
        if (ry + rCardH > startY + colH - 0.06) return;

        slide.addShape("rect", {
          x: x + 0.1,
          y: ry,
          w: colW - 0.18,
          h: rCardH,
          fill: { color: C.offwhite },
          line: { color: C.border, width: 0.5 },
        });
        // Red left accent
        slide.addShape("rect", {
          x: x + 0.1,
          y: ry,
          w: 0.05,
          h: rCardH,
          fill: { color: C.error },
          line: { color: C.error },
        });
        slide.addText(riskText, {
          x: x + 0.2,
          y: ry + 0.06,
          w: colW - 0.32,
          h: 0.3,
          fontSize: 9.5,
          bold: true,
          color: C.text,
          fontFace: FONT_BODY,
          wrap: true,
          margin: 0,
        });
        if (mitText) {
          slide.addText(`→ ${mitText}`, {
            x: x + 0.2,
            y: ry + 0.4,
            w: colW - 0.32,
            h: 0.36,
            fontSize: 9,
            color: C.textMuted,
            fontFace: FONT_BODY,
            italic: true,
            wrap: true,
            margin: 0,
          });
        }
      });
    } else {
      bulletList(
        slide,
        items.slice(0, 7),
        x + 0.1,
        startY + 0.5,
        colW - 0.18,
        colH - 0.56,
        {
          fontSize: 10.5,
          paraSpaceAfter: 4,
        },
      );
    }
  });

  addFooter(slide);
}

// ─── Slide 13 — Closing / Next Steps ─────────────────────────────────────────
function addClosingSlide(pres) {
  const slide = pres.addSlide();
  slide.background = { color: C.purpleDim };

  // Decorative orbs
  slide.addShape("ellipse", {
    x: 5.6,
    y: -1.2,
    w: 6.5,
    h: 6.5,
    fill: { color: C.purple, transparency: 80 },
    line: { color: C.purple, transparency: 76, width: 1 },
  });
  slide.addShape("ellipse", {
    x: -1.2,
    y: 3.2,
    w: 4.5,
    h: 4.5,
    fill: { color: C.purpleLight, transparency: 88 },
    line: { color: C.purpleLight, transparency: 85, width: 1 },
  });
  slide.addShape("ellipse", {
    x: 7.2,
    y: 3.4,
    w: 3.6,
    h: 3.6,
    fill: { color: C.purpleMid, transparency: 86 },
    line: { color: C.purpleMid, transparency: 83, width: 1 },
  });

  // Left accent bar
  slide.addShape("rect", {
    x: 0,
    y: 0,
    w: 0.32,
    h: H,
    fill: { color: C.purpleMid },
    line: { color: C.purpleMid },
  });

  // Logo — top left (on dark slide, logo should be light version)
  addLogo(slide, { x: 0.48, y: 0.22, w: 0.66, h: 0.66 });

  // Eyebrow
  slide.addText("NEXT STEPS", {
    x: 0.55,
    y: 1.28,
    w: 8.8,
    h: 0.36,
    fontSize: 9,
    bold: true,
    color: C.purpleLight,
    fontFace: FONT_BODY,
    charSpacing: 4.5,
    align: "center",
    margin: 0,
  });
  // Main heading — centered
  slide.addText("Review · Refine · Build", {
    x: 0.55,
    y: 1.72,
    w: 8.8,
    h: 1.3,
    fontSize: 42,
    bold: true,
    color: C.white,
    fontFace: FONT_TITLE,
    align: "center",
    margin: 0,
  });
  // Divider — centered
  slide.addShape("rect", {
    x: 2.5,
    y: 3.1,
    w: 5.0,
    h: 0.05,
    fill: { color: C.purpleLight },
    line: { color: C.purpleLight },
  });
  // Disclaimer
  slide.addText(
    "This document was generated by the AI Solution Architect pipeline.\n" +
      "All outputs should be reviewed and validated by a qualified solution architect before implementation.",
    {
      x: 0.55,
      y: 3.24,
      w: 8.8,
      h: 1.1,
      fontSize: 11.5,
      color: C.purpleLight,
      fontFace: FONT_BODY,
      italic: true,
      align: "center",
      margin: 0,
    },
  );
  // Confidential footer
  slide.addShape("rect", {
    x: 0,
    y: H - 0.42,
    w: W,
    h: 0.42,
    fill: { color: "000000", transparency: 65 },
    line: { color: "000000", transparency: 65 },
  });
  slide.addText("CONFIDENTIAL  ·  AI Solution Architect", {
    x: 0.55,
    y: H - 0.38,
    w: 9,
    h: 0.32,
    fontSize: 8,
    color: C.purpleLight,
    fontFace: FONT_BODY,
    align: "center",
    margin: 0,
    charSpacing: 0.5,
  });
}

// ─── Main ─────────────────────────────────────────────────────────────────────
(async () => {
  log(
    "[pptx-gen] ═══════════════════════════════════════════════════════════════",
  );
  log("[pptx-gen] Starting PowerPoint generation pipeline...");
  log("[pptx-gen] Project:", DATA.project?.name || "Unknown");

  log(
    "[pptx-gen] ─────────────────────────────────────────────────────────────",
  );
  log("[pptx-gen] STEP 1: Generating draw.io XML from architecture JSON...");

  const archData = DATA.architecture || {};
  log(
    "[pptx-gen] Architecture components:",
    (archData.components || []).length,
  );
  log(
    "[pptx-gen] Architecture connections:",
    (archData.connections || []).length,
  );
  log(
    "[pptx-gen] Diagram components:",
    (archData.diagram_components || []).length,
  );
  log(
    "[pptx-gen] Diagram connections:",
    (archData.diagram_connections || []).length,
  );

  let drawioXml;
  try {
    drawioXml = generateDrawioXml(DATA);
    log(`[pptx-gen] ✓ draw.io XML generated (${drawioXml.length} chars)`);
    if (drawioXml.length < 200) {
      log(
        "[pptx-gen] WARNING: XML is suspiciously small — diagram may be empty.",
      );
    }
  } catch (err) {
    console.error(
      `[pptx-gen] FATAL: draw.io XML generation failed: ${err.message}`,
    );
    process.exit(1);
  }

  log(
    "[pptx-gen] ─────────────────────────────────────────────────────────────",
  );
  log("[pptx-gen] STEP 2: Rendering diagram to PNG via local Puppeteer...");

  let pngBuffer;
  try {
    pngBuffer = await renderDrawioToPng(drawioXml, {
      width: 1400,
      height: 850,
    });
    log(`[pptx-gen] ✓ PNG render SUCCESS — ${pngBuffer.length} bytes`);
    if (pngBuffer.length < 500) {
      console.error(
        "[pptx-gen] WARNING: PNG is very small — diagram may be blank.",
      );
    }
  } catch (err) {
    console.error(`[pptx-gen] FATAL: Puppeteer render failed: ${err.message}`);
    console.error(`[pptx-gen] Stack: ${err.stack}`);
    process.exit(1);
  }

  const diagramB64 = "data:image/png;base64," + pngBuffer.toString("base64");
  log(`[pptx-gen] ✓ PNG encoded as base64 (${diagramB64.length} chars)`);

  log(
    "[pptx-gen] ─────────────────────────────────────────────────────────────",
  );
  log("[pptx-gen] STEP 3: Building PPTX presentation...");

  const pres = new pptxgen();
  pres.layout = "LAYOUT_16x9";
  pres.title = DATA.project?.name || "AI Solution Architecture";
  pres.author = "AI Solution Architect";
  pres.subject = "High-Level Architecture Document";

  log("[pptx-gen] Adding slides...");
  if (_shouldInclude("Title")) addTitleSlide(pres);
  if (_shouldInclude("ExecSummary")) addExecSummarySlide(pres);
  if (_shouldInclude("Problem")) addProblemSlide(pres);
  if (_shouldInclude("Solution")) addSolutionSlide(pres);
  if (_shouldInclude("Diagram")) addDiagramSlide(pres, diagramB64);
  if (_shouldInclude("Components")) addComponentsSlide(pres);
  if (_shouldInclude("DataFlow")) addDataFlowSlide(pres);
  if (_shouldInclude("TechStack")) addTechStackSlide(pres);
  if (_shouldInclude("Features")) addFeaturesSlide(pres);
  if (_shouldInclude("NFR")) addNFRSlide(pres);
  if (_shouldInclude("Roadmap")) addRoadmapSlide(pres);
  if (_shouldInclude("Risks")) addRisksSlide(pres);

  // ── Custom slides ──────────────────────────────────────────────────────────
  try {
    const custom = DATA.custom_slides || [];
    if (Array.isArray(custom) && custom.length > 0) {
      for (const cs of custom) {
        try {
          const title = cs.title || "Custom";
          const bullets = cs.bullets || cs.content || [];
          const cSlide = pres.addSlide();
          pageBackground(cSlide);
          headerBand(cSlide, title);
          if (Array.isArray(bullets)) {
            const items = bullets.map((b) =>
              typeof b === "string" ? b : String(b),
            );
            bulletList(cSlide, items, 0.6, 1.02, W - 1.2, 2.6, {
              fontSize: 11.5,
            });
          } else {
            cSlide.addText(String(bullets), {
              x: 0.6,
              y: 1.02,
              w: W - 1.2,
              h: 2.0,
              fontSize: 13.5,
              color: C.text,
              fontFace: FONT_BODY,
            });
          }
          addFooter(cSlide);
        } catch (err) {
          console.error(
            "[pptx-gen] Warning: failed to add custom slide:",
            err.message,
          );
        }
      }
    }
  } catch (err) {
    console.error(
      "[pptx-gen] Warning: custom slides processing failed:",
      err.message,
    );
  }

  if (_shouldInclude("Closing")) addClosingSlide(pres);

  log("[pptx-gen] ✓ All slides added");
  log("[pptx-gen] Writing PPTX file...");
  await pres.writeFile({ fileName: outputPath });
  log(`[pptx-gen] ✓ Done → ${outputPath}`);
  log(
    "[pptx-gen] ═══════════════════════════════════════════════════════════════",
  );
  process.exit(0);
})();
