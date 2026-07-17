"use strict";

const puppeteer = require("puppeteer");
const https = require("https");

/**
 * Renders a Mermaid diagram code into a PNG Buffer.
 * Tries local rendering via Puppeteer first. If it fails, falls back to mermaid.ink API.
 */
async function renderMermaidToPng(mermaidCode, opts = {}) {
  if (!mermaidCode || !mermaidCode.trim()) {
    throw new Error("mermaidRenderer: empty code");
  }

  console.error("[mermaidRenderer] Starting render...");
  
  // Try local Puppeteer rendering first
  if (!opts.forceFallback) {
    try {
      const pngBuffer = await _renderLocal(mermaidCode, opts);
      if (pngBuffer && pngBuffer.length >= 1000) {
        console.error("[mermaidRenderer] SUCCESS: rendered locally via Puppeteer");
        return pngBuffer;
      }
    } catch (err) {
      console.error("[mermaidRenderer] WARNING: local Puppeteer render failed:", err.message);
    }
  } else {
    console.error("[mermaidRenderer] Local render disabled via forceFallback option");
  }

  // Fallback to mermaid.ink
  console.error("[mermaidRenderer] Attempting fallback to mermaid.ink...");
  try {
    const pngBuffer = await _renderViaInk(mermaidCode);
    if (pngBuffer && pngBuffer.length >= 1000) {
      console.error("[mermaidRenderer] SUCCESS: rendered via mermaid.ink");
      return pngBuffer;
    }
  } catch (err) {
    console.error("[mermaidRenderer] FATAL: both local and mermaid.ink renders failed:", err.message);
    throw err;
  }
  
  throw new Error("mermaidRenderer: render returned empty/corrupted buffer");
}

async function _renderLocal(mermaidCode, opts) {
  const vpW = opts.width || 1400;
  const vpH = opts.height || 850;
  const tmo = opts.timeout || 60000;

  let browser;
  try {
    browser = await puppeteer.launch({
      headless: true,
      args: ["--no-sandbox", "--disable-setuid-sandbox", "--disable-dev-shm-usage", "--disable-gpu"],
    });
    const page = await browser.newPage();
    // Use deviceScaleFactor=2.0 for high resolution diagram screenshots
    await page.setViewport({ width: vpW, height: vpH, deviceScaleFactor: 2.0 });

    const html = _buildHtml(mermaidCode);
    await page.setContent(html, { waitUntil: "networkidle0", timeout: tmo });

    // Wait for the diagram-ready marker to be added to the DOM
    await page.waitForSelector("#diagram-ready", { timeout: tmo });

    const el = await page.$("#diagram-wrap");
    if (!el) throw new Error("mermaidRenderer: #diagram-wrap not found");

    const screenshotData = await el.screenshot({ type: "png", omitBackground: true });
    return Buffer.isBuffer(screenshotData) ? screenshotData : Buffer.from(screenshotData);
  } finally {
    if (browser) await browser.close().catch(() => {});
  }
}

function _renderViaInk(mermaidCode) {
  return new Promise((resolve, reject) => {
    // encode in base64url format
    const base64 = Buffer.from(mermaidCode).toString("base64url");
    const url = `https://mermaid.ink/img/${base64}`;

    const request = https.get(url, (res) => {
      if (res.statusCode !== 200) {
        reject(new Error(`mermaid.ink responded with status code ${res.statusCode}`));
        return;
      }

      const chunks = [];
      res.on("data", (chunk) => chunks.push(chunk));
      res.on("end", () => {
        resolve(Buffer.concat(chunks));
      });
    });

    request.on("error", (err) => reject(err));
    request.setTimeout(15000, () => {
      request.destroy();
      reject(new Error("mermaid.ink request timed out after 15 seconds"));
    });
  });
}

function _buildHtml(code) {
  return `<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
<style>
* { margin:0; padding:0; box-sizing:border-box; }
body { background:#FFFFFF; font-family: Arial, sans-serif; overflow:hidden; }
#diagram-wrap { display:inline-block; background:#FFFFFF; padding:40px; }
.mermaid { background:white; }
</style>
</head>
<body>
<div id="diagram-wrap">
  <pre class="mermaid">
${code}
  </pre>
</div>
<script>
try {
  mermaid.initialize({
    startOnLoad: true,
    theme: 'default',
    flowchart: {
      useMaxWidth: false,
      htmlLabels: true
    }
  });
  if (typeof mermaid.run === 'function') {
    mermaid.run().then(() => {
      const el = document.createElement("div");
      el.id = "diagram-ready";
      document.body.appendChild(el);
    }).catch(err => {
      console.error("mermaid.run error:", err);
      const el = document.createElement("div");
      el.id = "diagram-ready";
      document.body.appendChild(el);
    });
  } else {
    // For older versions, startOnLoad: true will trigger automatically
    // Wait for the SVG element to be created inside the .mermaid container
    const checkInterval = setInterval(() => {
      const svg = document.querySelector(".mermaid svg");
      if (svg) {
        clearInterval(checkInterval);
        const el = document.createElement("div");
        el.id = "diagram-ready";
        document.body.appendChild(el);
      }
    }, 100);
    // Timeout fallback
    setTimeout(() => {
      clearInterval(checkInterval);
      const el = document.createElement("div");
      el.id = "diagram-ready";
      document.body.appendChild(el);
    }, 5000);
  }
} catch(err) {
  console.error("Initialization error:", err);
  const el = document.createElement("div");
  el.id = "diagram-ready";
  document.body.appendChild(el);
}
</script>
</body>
</html>`;
}

module.exports = { renderMermaidToPng };
