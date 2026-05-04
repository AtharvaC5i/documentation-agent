"use strict";

const fs = require("fs");
const path = require("path");

const imageLogo = path.join(__dirname, "logo.png");
const imageLogoWhite = path.join(__dirname, "logo_white.png");

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
const HDRH = 0.76;
const BODY_Y = 0.86;
const BODY_H = H - BODY_Y - 0.36;

function log(msg) {
  console.error(msg);
}

function sanitize(val) {
  if (val == null) return "";
  return String(val)
    .replace(/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/g, "")
    .trim();
}

function R(slide, x, y, w, h, opts) {
  if (w > 0.001 && h > 0.001) slide.addShape("rect", { x, y, w, h, ...opts });
}

function E(slide, x, y, w, h, opts) {
  if (w > 0.001 && h > 0.001)
    slide.addShape("ellipse", { x, y, w, h, ...opts });
}

function clampH(h, min = 0.2) {
  return Math.max(min || 0.2, h);
}

function addLogo(slide, x, y, w, h) {
  try {
    const logoPath = fs.existsSync(imageLogoWhite)
      ? imageLogoWhite
      : fs.existsSync(imageLogo)
        ? imageLogo
        : null;
    if (logoPath) {
      slide.addImage({
        path: logoPath,
        x,
        y,
        w,
        h,
        sizing: { type: "contain", w, h },
      });
    }
  } catch (e) {
    log(`[custom-slide] logo skipped: ${e.message}`);
  }
}

function contentChrome(slide, title, DATA) {
  slide.background = { color: C.pageBg };

  R(slide, 0, 0, 0.055, H, {
    fill: { color: C.purple },
    line: { color: C.purple },
  });

  addLogo(slide, W - 1.22, 0.1, 1.14, 0.54);

  slide.addText(sanitize(title), {
    x: 0.18,
    y: 0.12,
    w: W - 1.48,
    h: 0.52,
    fontSize: 20,
    bold: true,
    color: C.text,
    fontFace: FONT_TITLE,
    align: "left",
    valign: "middle",
    margin: 0,
  });

  R(slide, 0, HDRH, W, 0.06, {
    fill: { color: C.purple },
    line: { color: C.purple },
  });

  R(slide, 0, H - 0.28, W, 0.02, {
    fill: { color: C.border },
    line: { color: C.border },
  });

  const pn = sanitize(DATA?.project?.name || "AI Solution Architect");

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

function card(slide, x, y, w, h, label, value) {
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

function addCustomSlide(pres, cs, DATA, ctx = {}) {
  if (!cs || !cs.title) {
    log(`[custom-slide] skipped — missing title`);
    return;
  }

  const slide = pres.addSlide();
  contentChrome(slide, cs.title, DATA);

  const type = (cs.type || "bullets").toLowerCase().trim();
  log(`[custom-slide] rendering slide "${cs.title}" as type="${type}"`);

  const bullets = Array.isArray(cs.bullets) ? cs.bullets : [];
  const items = Array.isArray(cs.items) ? cs.items : bullets;
  const columns = Array.isArray(cs.columns) ? cs.columns : null;
  const cards = Array.isArray(cs.cards) ? cs.cards : null;

  // two-column
  if (type === "two-column" && columns && columns.length >= 2) {
    const colW = (W - 0.54) / 2;
    columns.slice(0, 2).forEach((col, ci) => {
      const x = ci === 0 ? 0.18 : 0.18 + colW + 0.18;
      sectionLabel(slide, col.heading || `Column ${ci + 1}`, x, BODY_Y, colW);
      bulletList(
        slide,
        (col.bullets || col.items || []).slice(0, 8),
        x,
        BODY_Y + 0.32,
        colW,
        BODY_H - 0.32,
      );
    });
    return;
  }

  // cards
  if ((type === "cards" || type === "card-grid") && cards && cards.length > 0) {
    const count = Math.min(cards.length, 6);
    const perRow = count <= 2 ? 2 : count <= 4 ? 2 : 3;
    const rows = Math.ceil(count / perRow);
    const cW = (W - 0.36 - 0.12 * (perRow - 1)) / perRow;
    const cH = (BODY_H - 0.12 * (rows - 1)) / rows;

    cards.slice(0, count).forEach((c, i) => {
      const col = i % perRow;
      const row = Math.floor(i / perRow);
      const x = 0.18 + col * (cW + 0.12);
      const y = BODY_Y + row * (cH + 0.12);
      card(
        slide,
        x,
        y,
        cW,
        cH,
        c.label || c.title,
        c.value || c.body || c.text,
      );
    });
    return;
  }

  // table
  if (type === "table" && Array.isArray(cs.rows) && cs.rows.length > 0) {
    const headers = cs.headers || Object.keys(cs.rows[0] || {});
    const colCount = headers.length;
    const colW = (W - 0.36) / colCount;
    const rowH = 0.38;

    headers.forEach((hdr, ci) => {
      R(slide, 0.18 + ci * colW, BODY_Y, colW, rowH, {
        fill: { color: C.purple },
        line: { color: C.purple },
      });
      slide.addText(sanitize(hdr).toUpperCase(), {
        x: 0.22 + ci * colW,
        y: BODY_Y + 0.06,
        w: colW - 0.08,
        h: rowH - 0.1,
        fontSize: 9,
        bold: true,
        color: C.white,
        fontFace: FONT_BODY,
        align: "center",
        margin: 0,
      });
    });

    cs.rows.slice(0, 9).forEach((row, ri) => {
      const rowY = BODY_Y + rowH + ri * rowH;
      const isAlt = ri % 2 === 1;
      headers.forEach((hdr, ci) => {
        R(slide, 0.18 + ci * colW, rowY, colW, rowH, {
          fill: { color: isAlt ? C.purpleFaint : C.white },
          line: { color: C.border, width: 0.5 },
        });
        slide.addText(sanitize(row[hdr] ?? ""), {
          x: 0.22 + ci * colW,
          y: rowY + 0.06,
          w: colW - 0.08,
          h: rowH - 0.1,
          fontSize: 9.5,
          color: C.textDark,
          fontFace: FONT_BODY,
          valign: "middle",
          wrap: true,
          margin: 0,
        });
      });
    });
    return;
  }

  // default bullets (fallback for unknown or missing type)
  if (cs.summary) {
    R(slide, 0.18, BODY_Y, W - 0.28, 0.6, {
      fill: { color: C.purpleFaint },
      line: { color: C.border, width: 0.75 },
    });
    R(slide, 0.18, BODY_Y, 0.06, 0.6, {
      fill: { color: C.purple },
      line: { color: C.purple },
    });
    slide.addText(sanitize(cs.summary), {
      x: 0.36,
      y: BODY_Y + 0.06,
      w: W - 0.62,
      h: 0.48,
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

  const listY = BODY_Y + (cs.summary ? 0.7 : 0);
  bulletList(
    slide,
    items.slice(0, 10),
    0.18,
    listY,
    W - 0.36,
    BODY_H - (cs.summary ? 0.7 : 0),
  );
}

module.exports = { addCustomSlide };
