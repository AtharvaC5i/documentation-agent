/**
 * BRD Document Builder — docx.js
 * Color scheme: Purple brand palette
 */

"use strict";

const fs = require("fs");
const path = require("path");

const {
  Document,
  Packer,
  Paragraph,
  TextRun,
  Table,
  TableRow,
  TableCell,
  Header,
  Footer,
  AlignmentType,
  HeadingLevel,
  BorderStyle,
  WidthType,
  ShadingType,
  VerticalAlign,
  PageNumber,
  PageBreak,
  NumberFormat,
  LevelFormat,
  TabStopPosition,
  TabStopType,
  PositionalTab,
  PositionalTabAlignment,
  PositionalTabRelativeTo,
  TableOfContents,
  ImageRun,
} = require("docx");

// ── Constants ──────────────────────────────────────────────────────────────

const PAGE_W_DXA = 12240;
const PAGE_H_DXA = 15840;
const MARGIN = 1440;
const CONTENT_W = PAGE_W_DXA - MARGIN * 2;

// ── Purple Brand Color Palette ─────────────────────────────────────────────

const NAVY = "4C1D95"; // C.purpleDim   — darkest, used for primary headings
const BLUE = "5B21B6"; // C.purple      — primary brand mid-tone
const ACCENT = "7C3AED"; // C.purpleMid   — accent borders, sub-headings
const MUTED = "A78BFA"; // C.purpleLight — muted labels, H3 text
const LIGHT = "A78BFA"; // C.purpleLight — footer/caption faint text
const WHITE = "FFFFFF";
const STRIPE = "EDE9FE"; // C.purpleFaint — alternate table row tint

const FONT = "Calibri";

// ── Header Logo ────────────────────────────────────────────────────────────
// ↓↓ Only touch these three lines ↓↓

const HEADER_LOGO_URL = path.join(__dirname, "logo.png");
const HEADER_LOGO_WIDTH = 80; // pixels
const HEADER_LOGO_HEIGHT = 30; // pixels

// ── Helpers ────────────────────────────────────────────────────────────────

function fontPt(n) {
  return Math.round(n * 2);
}
function twips(n) {
  return Math.round(n * 20);
}

function border(color = "C4B5FD", size = 4) {
  return { style: BorderStyle.SINGLE, size, color, space: 1 };
}

function noBorder() {
  return { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
}

function noAllBorders() {
  return {
    top: noBorder(),
    bottom: noBorder(),
    left: noBorder(),
    right: noBorder(),
  };
}

function shade(fill) {
  return { fill, type: ShadingType.CLEAR };
}

function cellMargins(top = 60, bottom = 60, left = 100, right = 100) {
  return { top, bottom, left, right };
}

function run(text, opts = {}) {
  return new TextRun({
    text: String(text),
    font: FONT,
    size: opts.size || fontPt(10.5),
    bold: opts.bold || false,
    italics: opts.italic || false,
    color: opts.color || "1A0533",
  });
}

function para(children, opts = {}) {
  return new Paragraph({
    children: Array.isArray(children) ? children : [children],
    alignment: opts.align || AlignmentType.LEFT,
    spacing: {
      before: opts.before !== undefined ? opts.before : 0,
      after: opts.after !== undefined ? opts.after : twips(6),
      line: opts.line !== undefined ? opts.line : twips(15.5),
      lineRule: "auto",
    },
    indent: opts.indent ? { left: opts.indent } : undefined,
  });
}

function heading1(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_1,
    children: [
      new TextRun({
        text,
        font: FONT,
        size: fontPt(14),
        bold: true,
        color: NAVY,
      }),
    ],
    spacing: { before: twips(16), after: twips(6) },
    border: { bottom: border("C4B5FD", 3) },
  });
}

function heading2(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_2,
    children: [
      new TextRun({
        text,
        font: FONT,
        size: fontPt(12),
        bold: true,
        color: ACCENT,
      }),
    ],
    spacing: { before: twips(12), after: twips(4) },
    border: {
      left: { style: BorderStyle.SINGLE, size: 14, color: BLUE, space: 6 },
    },
  });
}

function heading3(text) {
  return new Paragraph({
    heading: HeadingLevel.HEADING_3,
    children: [
      new TextRun({
        text,
        font: FONT,
        size: fontPt(10.5),
        bold: true,
        color: MUTED,
      }),
    ],
    spacing: { before: twips(8), after: twips(3) },
  });
}

function bullet(text, level = 0) {
  return new Paragraph({
    numbering: { reference: "bullets", level },
    children: parseInline(text),
    spacing: { before: 0, after: twips(3), line: twips(14), lineRule: "auto" },
  });
}

function hrule(color = "C4B5FD") {
  return new Paragraph({
    children: [new TextRun({ text: "", font: FONT })],
    border: { bottom: { style: BorderStyle.SINGLE, size: 4, color, space: 1 } },
    spacing: { before: twips(4), after: twips(4) },
  });
}

// ── Inline markdown parser ─────────────────────────────────────────────────

function parseInline(text, baseColor) {
  const color = baseColor || "1A0533";
  const runs = [];
  const re = /(\*\*\*[^*]+\*\*\*|\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`|[^*`]+)/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const tok = m[0];
    if (tok.startsWith("***") && tok.endsWith("***") && tok.length > 6) {
      runs.push(
        new TextRun({
          text: tok.slice(3, -3),
          font: FONT,
          size: fontPt(10.5),
          bold: true,
          italics: true,
          color,
        }),
      );
    } else if (tok.startsWith("**") && tok.endsWith("**") && tok.length > 4) {
      runs.push(
        new TextRun({
          text: tok.slice(2, -2),
          font: FONT,
          size: fontPt(10.5),
          bold: true,
          color,
        }),
      );
    } else if (tok.startsWith("*") && tok.endsWith("*") && tok.length > 2) {
      runs.push(
        new TextRun({
          text: tok.slice(1, -1),
          font: FONT,
          size: fontPt(10.5),
          italics: true,
          color,
        }),
      );
    } else if (tok.startsWith("`") && tok.endsWith("`") && tok.length > 2) {
      runs.push(
        new TextRun({
          text: tok.slice(1, -1),
          font: "Consolas",
          size: fontPt(9),
          color: "4C1D95",
        }),
      );
    } else {
      runs.push(
        new TextRun({ text: tok, font: FONT, size: fontPt(10.5), color }),
      );
    }
  }
  return runs.length > 0
    ? runs
    : [new TextRun({ text, font: FONT, size: fontPt(10.5), color })];
}

// ── Markdown content parser ────────────────────────────────────────────────

function parseMarkdown(content, sectionName) {
  const elements = [];
  if (!content) return elements;

  let lines = content.split("\n");
  if (lines[0]) {
    const first = lines[0].trim();
    if (/^#{1,3}\s+/.test(first)) {
      const headingText = first
        .replace(/^#{1,3}\s+/, "")
        .trim()
        .toLowerCase();
      if (headingText === (sectionName || "").trim().toLowerCase()) {
        lines = lines.slice(1);
      }
    }
  }

  let i = 0;
  while (i < lines.length) {
    const line = lines[i];
    const stripped = line.trim();

    if (!stripped) {
      i++;
      continue;
    }

    if (stripped.startsWith("|") && stripped.includes("|", 1)) {
      const tableLines = [];
      while (i < lines.length && lines[i].trim().startsWith("|")) {
        const l = lines[i].trim();
        if (!l.replace(/[\s|:-]/g, "")) {
          i++;
          continue;
        }
        tableLines.push(l);
        i++;
      }
      if (tableLines.length > 0) elements.push(...buildTable(tableLines));
      continue;
    }

    if (stripped.startsWith("#### ") || stripped.startsWith("##### ")) {
      elements.push(heading3(stripped.replace(/^#{4,5}\s+/, "")));
    } else if (stripped.startsWith("### ")) {
      elements.push(heading3(stripped.slice(4)));
    } else if (stripped.startsWith("## ")) {
      elements.push(heading2(stripped.slice(3)));
    } else if (stripped.startsWith("# ")) {
      elements.push(heading1(stripped.slice(2)));
    } else if (stripped.startsWith("- ") || stripped.startsWith("* ")) {
      elements.push(bullet(stripped.slice(2)));
    } else if (/^\d+\.\s/.test(stripped)) {
      const text = stripped.replace(/^\d+\.\s/, "");
      elements.push(
        new Paragraph({
          numbering: { reference: "numbers", level: 0 },
          children: parseInline(text),
          spacing: {
            before: 0,
            after: twips(3),
            line: twips(14),
            lineRule: "auto",
          },
        }),
      );
    } else if (stripped === "---" || stripped === "***" || stripped === "___") {
      elements.push(hrule());
    } else if (stripped.includes("###") || stripped.includes("## ")) {
      const parts = stripped.split(/(#{2,4}\s+[^\n#]+)/);
      for (const part of parts) {
        const p = part.trim();
        if (!p) continue;
        if (p.startsWith("### ")) elements.push(heading3(p.slice(4)));
        else if (p.startsWith("## ")) elements.push(heading2(p.slice(3)));
        else if (p.startsWith("#### ")) elements.push(heading3(p.slice(5)));
        else if (p.length > 0) {
          elements.push(
            new Paragraph({
              children: parseInline(p),
              spacing: {
                before: 0,
                after: twips(6),
                line: twips(15.5),
                lineRule: "auto",
              },
            }),
          );
        }
      }
    } else {
      elements.push(
        new Paragraph({
          children: parseInline(stripped),
          spacing: {
            before: 0,
            after: twips(6),
            line: twips(15.5),
            lineRule: "auto",
          },
        }),
      );
    }
    i++;
  }
  return elements;
}

// ── Table builder ──────────────────────────────────────────────────────────

function buildTable(tableLines) {
  if (tableLines.length === 0) return [];

  const rows = tableLines.map((line) =>
    line
      .replace(/^\||\|$/g, "")
      .split("|")
      .map((c) => c.trim()),
  );

  const cols = Math.max(...rows.map((r) => r.length));
  const colWidths = distributeColWidths(cols, CONTENT_W);

  const tableRows = rows.map((rowData, ri) => {
    const isHeader = ri === 0;
    const fill = isHeader ? NAVY : ri % 2 === 1 ? STRIPE : WHITE;
    const cells = [];

    for (let ci = 0; ci < cols; ci++) {
      const text = rowData[ci] || "";
      cells.push(
        new TableCell({
          width: { size: colWidths[ci], type: WidthType.DXA },
          shading: shade(fill),
          margins: cellMargins(80, 80, 120, 120),
          verticalAlign: VerticalAlign.CENTER,
          borders: isHeader
            ? {
                bottom: border(ACCENT, 6),
                top: noBorder(),
                left: noBorder(),
                right: noBorder(),
              }
            : noAllBorders(),
          children: [
            new Paragraph({
              children: [
                new TextRun({
                  text: text.length > 200 ? text.slice(0, 197) + "…" : text,
                  font: FONT,
                  size: fontPt(9.5),
                  bold: isHeader,
                  color: isHeader ? WHITE : "2D1B69",
                }),
              ],
              spacing: { before: 0, after: 0 },
              alignment: AlignmentType.LEFT,
            }),
          ],
        }),
      );
    }

    return new TableRow({ children: cells, cantSplit: true });
  });

  return [
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: colWidths,
      rows: tableRows,
    }),
    new Paragraph({
      children: [new TextRun("")],
      spacing: { before: 0, after: twips(8) },
    }),
  ];
}

function distributeColWidths(cols, totalWidth) {
  const presets = {
    2: [0.32, 0.68],
    3: [0.15, 0.5, 0.35],
    4: [0.1, 0.42, 0.22, 0.26],
    5: [0.1, 0.32, 0.18, 0.2, 0.2],
    6: [0.09, 0.28, 0.13, 0.16, 0.18, 0.16],
    7: [0.08, 0.25, 0.13, 0.14, 0.14, 0.13, 0.13],
  };
  const ratios = presets[cols] || Array(cols).fill(1 / cols);
  const widths = ratios.slice(0, cols).map((r) => Math.round(totalWidth * r));
  const sum = widths.reduce((a, b) => a + b, 0);
  widths[widths.length - 1] += totalWidth - sum;
  return widths;
}

// ── Cover page ─────────────────────────────────────────────────────────────

function buildCoverPage(meta) {
  const items = [];

  items.push(
    new Paragraph({
      children: [new TextRun({ text: "", font: FONT })],
      border: {
        top: { style: BorderStyle.SINGLE, size: 36, color: BLUE, space: 0 },
      },
      spacing: { before: 0, after: twips(48) },
    }),
  );

  items.push(
    new Paragraph({
      children: [
        new TextRun({
          text: (meta.project_name || "Project").toUpperCase(),
          font: FONT,
          size: fontPt(28),
          bold: true,
          color: NAVY,
        }),
      ],
      spacing: { before: 0, after: twips(4) },
    }),
  );

  items.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "BUSINESS REQUIREMENTS DOCUMENT",
          font: FONT,
          size: fontPt(11),
          bold: true,
          color: ACCENT,
        }),
      ],
      spacing: { before: 0, after: twips(0) },
    }),
  );

  items.push(
    new Paragraph({
      children: [new TextRun({ text: "", font: FONT })],
      border: {
        bottom: { style: BorderStyle.SINGLE, size: 10, color: BLUE, space: 1 },
      },
      spacing: { before: twips(12), after: twips(12) },
    }),
  );

  if (meta.description) {
    items.push(
      new Paragraph({
        children: [
          new TextRun({
            text: meta.description,
            font: FONT,
            size: fontPt(11),
            italics: true,
            color: MUTED,
          }),
        ],
        spacing: { before: 0, after: twips(28) },
      }),
    );
  }

  const metaRows = [];
  if (meta.client_name) metaRows.push(["Client", meta.client_name]);
  if (meta.team) metaRows.push(["Prepared By", meta.team]);
  metaRows.push([
    "Date",
    new Date().toLocaleDateString("en-IN", {
      day: "numeric",
      month: "long",
      year: "numeric",
    }),
  ]);
  metaRows.push(["Version", `v${meta.version || 1}.0 — DRAFT`]);
  metaRows.push(["Classification", "Confidential"]);

  const LW = Math.round(CONTENT_W * 0.22);
  const VW = CONTENT_W - LW;

  const metaTblRows = metaRows.map(([label, value], i) => {
    const isLast = i === metaRows.length - 1;
    const bdr = isLast
      ? noAllBorders()
      : {
          top: noBorder(),
          left: noBorder(),
          right: noBorder(),
          bottom: {
            style: BorderStyle.SINGLE,
            size: 2,
            color: "DDD6FE",
            space: 0,
          },
        };
    return new TableRow({
      children: [
        new TableCell({
          width: { size: LW, type: WidthType.DXA },
          shading: shade("F5F3FF"),
          borders: bdr,
          margins: cellMargins(70, 70, 200, 100),
          children: [
            new Paragraph({
              children: [
                new TextRun({
                  text: label.toUpperCase(),
                  font: FONT,
                  size: fontPt(7.5),
                  bold: true,
                  color: LIGHT,
                }),
              ],
              spacing: { before: 0, after: 0 },
            }),
          ],
        }),
        new TableCell({
          width: { size: VW, type: WidthType.DXA },
          shading: shade("F5F3FF"),
          borders: bdr,
          margins: cellMargins(70, 70, 100, 100),
          children: [
            new Paragraph({
              children: [
                new TextRun({
                  text: value,
                  font: FONT,
                  size: fontPt(10.5),
                  color: NAVY,
                }),
              ],
              spacing: { before: 0, after: 0 },
            }),
          ],
        }),
      ],
    });
  });

  items.push(
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: [
        Math.round(CONTENT_W * 0.005),
        CONTENT_W - Math.round(CONTENT_W * 0.005),
      ],
      rows: [
        new TableRow({
          children: [
            new TableCell({
              width: {
                size: Math.round(CONTENT_W * 0.005),
                type: WidthType.DXA,
              },
              shading: shade(BLUE),
              borders: noAllBorders(),
              margins: cellMargins(0, 0, 0, 0),
              children: [new Paragraph({ children: [new TextRun("")] })],
            }),
            new TableCell({
              width: {
                size: CONTENT_W - Math.round(CONTENT_W * 0.005),
                type: WidthType.DXA,
              },
              shading: shade("F5F3FF"),
              borders: noAllBorders(),
              margins: cellMargins(0, 0, 0, 0),
              children: [
                new Table({
                  width: {
                    size: CONTENT_W - Math.round(CONTENT_W * 0.005),
                    type: WidthType.DXA,
                  },
                  columnWidths: [LW, VW],
                  rows: metaTblRows,
                }),
              ],
            }),
          ],
        }),
      ],
    }),
  );

  return items;
}

// ── Table of Contents ──────────────────────────────────────────────────────

function buildTOC(sections) {
  const elements = [];

  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "Table of Contents",
          font: FONT,
          size: fontPt(14),
          bold: true,
          color: NAVY,
        }),
      ],
      spacing: { before: 0, after: twips(4) },
    }),
  );

  elements.push(hrule(BLUE));

  let page = 3;
  const pageMemo = sections.map((sec) => {
    const p = page;
    page += Math.max(
      1,
      Math.round((sec.content || "").split(/\s+/).length / 300),
    );
    return p;
  });

  const LW = CONTENT_W - 900;
  const RW = 900;

  const tocRows = sections.map(
    (sec, i) =>
      new TableRow({
        children: [
          new TableCell({
            width: { size: LW, type: WidthType.DXA },
            shading: shade(i % 2 === 0 ? STRIPE : WHITE),
            borders: noAllBorders(),
            margins: cellMargins(60, 60, 150, 60),
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: `${i + 1}.  `,
                    font: FONT,
                    size: fontPt(10.5),
                    bold: true,
                    color: ACCENT,
                  }),
                  new TextRun({
                    text: sec.name || "",
                    font: FONT,
                    size: fontPt(10.5),
                    color: NAVY,
                  }),
                ],
                spacing: { before: 0, after: 0 },
              }),
            ],
          }),
          new TableCell({
            width: { size: RW, type: WidthType.DXA },
            shading: shade(i % 2 === 0 ? STRIPE : WHITE),
            borders: noAllBorders(),
            margins: cellMargins(60, 60, 60, 120),
            children: [
              new Paragraph({
                children: [
                  new TextRun({
                    text: String(pageMemo[i]),
                    font: FONT,
                    size: fontPt(10.5),
                    color: MUTED,
                  }),
                ],
                alignment: AlignmentType.RIGHT,
                spacing: { before: 0, after: 0 },
              }),
            ],
          }),
        ],
      }),
  );

  elements.push(
    new Table({
      width: { size: CONTENT_W, type: WidthType.DXA },
      columnWidths: [LW, RW],
      rows: tocRows,
    }),
  );
  elements.push(hrule("C4B5FD"));

  elements.push(
    new Paragraph({
      children: [
        new TextRun({
          text: "Page numbers are approximate estimates.",
          font: FONT,
          size: fontPt(8.5),
          italics: true,
          color: LIGHT,
        }),
      ],
      spacing: { before: twips(3), after: 0 },
    }),
  );

  return elements;
}

// ── Header logo fetch ──────────────────────────────────────────────────────

async function fetchImageBuffer(url) {
  const https = require("https");
  const http = require("http");
  const client = url.startsWith("https") ? https : http;
  return new Promise((resolve, reject) => {
    client
      .get(url, (res) => {
        const chunks = [];
        res.on("data", (chunk) => chunks.push(chunk));
        res.on("end", () => resolve(Buffer.concat(chunks)));
        res.on("error", reject);
      })
      .on("error", reject);
  });
}

// ── Header & Footer ────────────────────────────────────────────────────────

function buildHeader(projectName, logoBuffer) {
  const logoChild = logoBuffer
    ? new ImageRun({
        data: logoBuffer,
        transformation: {
          width: HEADER_LOGO_WIDTH,
          height: HEADER_LOGO_HEIGHT,
        },
      })
    : new TextRun({
        text: projectName,
        font: FONT,
        size: fontPt(8.5),
        bold: true,
        color: NAVY,
      });

  return new Header({
    children: [
      new Paragraph({
        children: [
          logoChild,
          new TextRun({ text: "\t", font: FONT }),
          new TextRun({
            text: "Business Requirements Document",
            font: FONT,
            size: fontPt(8.5),
            color: MUTED,
          }),
        ],
        tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }],
        border: {
          bottom: { style: BorderStyle.SINGLE, size: 6, color: BLUE, space: 1 },
        },
        spacing: { before: 0, after: twips(3) },
      }),
    ],
  });
}

function buildFooter(clientName) {
  return new Footer({
    children: [
      new Paragraph({
        children: [
          new TextRun({
            text: `© ${new Date().getFullYear()}  ${clientName}  ·  Confidential`,
            font: FONT,
            size: fontPt(8.5),
            color: MUTED,
          }),
          new TextRun({ text: "\t", font: FONT }),
          new TextRun({
            text: "Page ",
            font: FONT,
            size: fontPt(8.5),
            color: MUTED,
          }),
          new TextRun({
            children: [PageNumber.CURRENT],
            font: FONT,
            size: fontPt(8.5),
            color: MUTED,
          }),
          new TextRun({
            text: " of ",
            font: FONT,
            size: fontPt(8.5),
            color: MUTED,
          }),
          new TextRun({
            children: [PageNumber.TOTAL_PAGES],
            font: FONT,
            size: fontPt(8.5),
            color: MUTED,
          }),
        ],
        tabStops: [{ type: TabStopType.RIGHT, position: CONTENT_W }],
        border: {
          top: {
            style: BorderStyle.SINGLE,
            size: 4,
            color: "C4B5FD",
            space: 1,
          },
        },
        spacing: { before: twips(3), after: 0 },
      }),
    ],
  });
}

// ── Main builder ───────────────────────────────────────────────────────────

async function buildDocument(data) {
  const meta = data.metadata || {};
  const sections = data.sections || [];

  const projectName = meta.project_name || "Project";
  const clientName = meta.client_name || "Client";

  // Fetch logo — falls back to project name text if URL is placeholder or fetch fails
  let logoBuffer = null;
  try {
    logoBuffer = fs.readFileSync(HEADER_LOGO_URL);
  } catch (e) {
    console.warn("Logo file not found, using text fallback:", e.message);
  }

  const coverChildren = [
    ...buildCoverPage(meta),
    new Paragraph({ children: [new PageBreak()] }),
  ];
  const tocChildren = [
    ...buildTOC(sections),
    new Paragraph({ children: [new PageBreak()] }),
  ];
  const contentChildren = [];

  sections.forEach((sec, idx) => {
    if (idx > 0)
      contentChildren.push(new Paragraph({ children: [new PageBreak()] }));
    contentChildren.push(heading1(sec.name || `Section ${idx + 1}`));
    parseMarkdown(sec.content || "", sec.name).forEach((el) =>
      contentChildren.push(el),
    );

    if (sec.quality_pct && sec.req_count) {
      contentChildren.push(
        new Paragraph({
          children: [
            new TextRun({
              text: `[ Quality: ${sec.quality_pct}  ·  Requirements used: ${sec.req_count} ]`,
              font: FONT,
              size: fontPt(7.5),
              italics: true,
              color: LIGHT,
            }),
          ],
          spacing: { before: twips(8), after: 0 },
        }),
      );
    }
  });

  const doc = new Document({
    numbering: {
      config: [
        {
          reference: "bullets",
          levels: [
            {
              level: 0,
              format: LevelFormat.BULLET,
              text: "\u2022",
              alignment: AlignmentType.LEFT,
              style: {
                paragraph: {
                  indent: { left: 720, hanging: 360 },
                  spacing: { before: 0, after: twips(3) },
                },
                run: { font: FONT, size: fontPt(10.5) },
              },
            },
          ],
        },
        {
          reference: "numbers",
          levels: [
            {
              level: 0,
              format: LevelFormat.DECIMAL,
              text: "%1.",
              alignment: AlignmentType.LEFT,
              style: {
                paragraph: {
                  indent: { left: 720, hanging: 360 },
                  spacing: { before: 0, after: twips(3) },
                },
                run: { font: FONT, size: fontPt(10.5) },
              },
            },
          ],
        },
      ],
    },
    styles: {
      default: {
        document: { run: { font: FONT, size: fontPt(10.5), color: "1A0533" } },
      },
      paragraphStyles: [
        {
          id: "Heading1",
          name: "Heading 1",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: fontPt(14), bold: true, font: FONT, color: NAVY },
          paragraph: {
            spacing: { before: twips(16), after: twips(6) },
            outlineLevel: 0,
            keepNext: true,
          },
        },
        {
          id: "Heading2",
          name: "Heading 2",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: fontPt(12), bold: true, font: FONT, color: ACCENT },
          paragraph: {
            spacing: { before: twips(12), after: twips(4) },
            outlineLevel: 1,
            keepNext: true,
          },
        },
        {
          id: "Heading3",
          name: "Heading 3",
          basedOn: "Normal",
          next: "Normal",
          quickFormat: true,
          run: { size: fontPt(10.5), bold: true, font: FONT, color: MUTED },
          paragraph: {
            spacing: { before: twips(8), after: twips(3) },
            outlineLevel: 2,
            keepNext: true,
          },
        },
      ],
    },
    sections: [
      {
        properties: {
          page: {
            size: { width: PAGE_W_DXA, height: PAGE_H_DXA },
            margin: {
              top: MARGIN,
              right: MARGIN,
              bottom: MARGIN,
              left: MARGIN,
            },
          },
          titlePage: false,
        },
        headers: { default: buildHeader(projectName, logoBuffer) },
        footers: { default: buildFooter(clientName) },
        children: coverChildren,
      },
      {
        properties: {
          page: {
            size: { width: PAGE_W_DXA, height: PAGE_H_DXA },
            margin: { top: 1200, right: MARGIN, bottom: 1200, left: MARGIN },
            pageNumbers: { start: 2, formatType: NumberFormat.DECIMAL },
          },
        },
        headers: { default: buildHeader(projectName, logoBuffer) },
        footers: { default: buildFooter(clientName) },
        children: [...tocChildren, ...contentChildren],
      },
    ],
  });

  return doc;
}

// ── Entry point ────────────────────────────────────────────────────────────

const [, , inputFile, outputFile] = process.argv;
if (!inputFile || !outputFile) {
  console.error("Usage: node build_brd.js <input.json> <output.docx>");
  process.exit(1);
}

const data = JSON.parse(fs.readFileSync(inputFile, "utf8"));

buildDocument(data)
  .then((doc) => {
    return Packer.toBuffer(doc);
  })
  .then((buffer) => {
    fs.writeFileSync(outputFile, buffer);
    console.log(`OK:${outputFile}`);
  })
  .catch((err) => {
    console.error("ERROR:" + err.message);
    process.exit(1);
  });
