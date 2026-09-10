#!/usr/bin/env node
/**
 * qr-cli  --  Node.js rendering core
 *
 * Accepts the same flag interface as rondomondo/qr-cli so that qr-skill.sh
 * works unchanged when Docker is unavailable.
 *
 * Input  : --key=value flags  OR  --json='{"key":"value"}'  OR  stdin JSON
 * Output : JSON  { success, meta, image: { base64, dataUri, filename } }
 *
 * Deps   : qr-code-styling  canvas  sharp  jsdom
 *
 * SANDBOX PATCHES (applied 2025-05 -- see bootstrap_node_backend.sh for why):
 *   1. canvas + jsdom added as explicit deps (canvas compiled locally via
 *      npm_config_nodedir=/usr to avoid nodejs.org header download).
 *   2. JSDOM subclassed to strip { resources: "usable" } -- prevents network
 *      fetches that hang in airgapped/sandboxed environments.
 *   3. stdin read guarded: only attempted when --data / --json not supplied,
 *      to avoid blocking when stdout is captured by a parent process.
 */

"use strict";

const fs      = require("fs");
const path    = require("path");
const { createCanvas, loadImage } = require("canvas");
const sharp   = require("sharp");
const QRCodeStyling = require("qr-code-styling");
const { JSDOM: _JSDOM } = require("jsdom");

// Subclass JSDOM to strip { resources: "usable" }, which triggers network
// fetches that hang in sandboxed/airgapped environments (e.g. Claude sandbox).
class JSDOM extends _JSDOM {
  constructor(html, opts = {}) {
    const safe = Object.assign({}, opts);
    delete safe.resources;
    super(html, safe);
  }
}

// --- Argument parsing --------------------------------------------------------

function parseArgs(argv) {
  const opts = {};
  let jsonBlob = null;

  for (const arg of argv.slice(2)) {
    if (arg.startsWith("--json=")) {
      jsonBlob = arg.slice(7);
      continue;
    }
    const m = arg.match(/^--([^=]+)=(.*)$/s);
    if (m) {
      // Support dot-notation keys like dotsOptions.type
      setNested(opts, m[1], m[2]);
    }
  }

  // Merge --json blob on top of flag opts (flags win)
  if (jsonBlob) {
    try {
      const base = JSON.parse(jsonBlob);
      mergeDeep(base, opts);
      return base;
    } catch (e) {
      die(`Invalid --json blob: ${e.message}`);
    }
  }

  // stdin JSON (non-TTY) -- only read if no --data or --json flags provided.
  // Guard is critical: without it, the process blocks forever when stdout is
  // captured by a parent process (e.g. python3 -m qr_cli via subprocess).
  if (!process.stdin.isTTY && !opts.data && !jsonBlob) {
    try {
      const raw = fs.readFileSync("/dev/stdin", "utf8").trim();
      if (raw) {
        const base = JSON.parse(raw);
        mergeDeep(base, opts);
        return base;
      }
    } catch (_) {}
  }

  return opts;
}

function setNested(obj, dotKey, value) {
  const parts = dotKey.split(".");
  let cur = obj;
  for (let i = 0; i < parts.length - 1; i++) {
    if (cur[parts[i]] === undefined) cur[parts[i]] = {};
    cur = cur[parts[i]];
  }
  cur[parts[parts.length - 1]] = value;
}

function mergeDeep(target, source) {
  for (const key of Object.keys(source)) {
    if (source[key] && typeof source[key] === "object" && !Array.isArray(source[key])) {
      if (!target[key]) target[key] = {};
      mergeDeep(target[key], source[key]);
    } else {
      target[key] = source[key];
    }
  }
}

// --- Helpers -----------------------------------------------------------------

function die(msg) {
  process.stdout.write(JSON.stringify({ success: false, error: msg }) + "\n");
  process.exit(1);
}

function ensureHex(color) {
  if (!color) return color;
  color = String(color).trim();
  if (/^#[0-9a-fA-F]{3,8}$/.test(color)) return color;
  if (/^[0-9a-fA-F]{6}$/.test(color)) return `#${color}`;
  if (/^[0-9a-fA-F]{3}$/.test(color)) return `#${color}`;
  return color; // pass through named colours (browser env) or unknowns
}

// --- Build QRCodeStyling config ----------------------------------------------

function buildConfig(opts) {
  const width  = parseInt(opts.width  || opts.size || 300, 10);
  const height = parseInt(opts.height || opts.size || width, 10);

  const cfg = {
    width,
    height,
    type: "canvas",
    data: opts.data || "https://example.com",
    margin: parseInt(opts.margin || 0, 10),
    qrOptions: {
      errorCorrectionLevel: opts?.qrOptions?.errorCorrectionLevel || "Q",
    },
    dotsOptions: {
      type:  opts?.dotsOptions?.type  || "square",
      color: ensureHex(opts?.dotsOptions?.color) || "#000000",
    },
    backgroundOptions: {
      color: ensureHex(opts?.backgroundOptions?.color) || "#ffffff",
    },
  };

  // Corner square options
  if (opts.cornersSquareOptions) {
    cfg.cornersSquareOptions = {
      type:  opts.cornersSquareOptions.type  || undefined,
      color: ensureHex(opts.cornersSquareOptions.color) || cfg.dotsOptions.color,
    };
  }

  // Corner dot options
  if (opts.cornersDotOptions) {
    cfg.cornersDotOptions = {
      type:  opts.cornersDotOptions.type  || undefined,
      color: ensureHex(opts.cornersDotOptions.color) || cfg.dotsOptions.color,
    };
  }

  // Image / logo embedding
  if (opts.image) {
    cfg.image = opts.image;
    cfg.imageOptions = {
      margin:      parseInt(opts?.imageOptions?.margin      || 10, 10),
      crossOrigin: opts?.imageOptions?.crossOrigin || "anonymous",
      hideBackgroundDots: true,
    };
  }

  return cfg;
}

// --- Render ------------------------------------------------------------------

async function render(opts) {
  const t0  = Date.now();
  const fmt = (opts.format || "png").toLowerCase().replace("jpeg", "jpg");

  const cfg = buildConfig(opts);

  // Pass jsdom + node-canvas so qr-code-styling works outside a browser.
  // jsdom is our sandbox-safe subclass that strips the { resources: "usable" }
  // option to prevent network fetches.
  cfg.jsdom      = JSDOM;
  cfg.nodeCanvas = { createCanvas, loadImage };

  const qr = new QRCodeStyling(cfg);

  const rawPngBuf = await qr.getRawData("png");
  if (!rawPngBuf) die("Render failed: getRawData returned null");

  const border = parseInt(opts.border || 0, 10);
  let rawPng = Buffer.isBuffer(rawPngBuf) ? rawPngBuf : Buffer.from(rawPngBuf);

  // Apply border padding via sharp
  if (border > 0) {
    const bg = ensureHex(opts?.backgroundOptions?.color) || "#ffffff";
    rawPng = await sharp(rawPng)
      .extend({
        top: border, bottom: border, left: border, right: border,
        background: bg,
      })
      .png()
      .toBuffer();
  }

  // Convert to target format
  let outBuf;
  let mimeType;
  const finalW = cfg.width  + border * 2;
  const finalH = cfg.height + border * 2;

  if (fmt === "svg") {
    // SVG output: re-render via qr-code-styling SVG factory
    const svgData = await qr.getRawData("svg");
    outBuf   = Buffer.isBuffer(svgData) ? svgData : Buffer.from(String(svgData));
    mimeType = "image/svg+xml";
  } else if (fmt === "jpg") {
    outBuf   = await sharp(rawPng).jpeg({ quality: 90 }).toBuffer();
    mimeType = "image/jpeg";
  } else if (fmt === "webp") {
    outBuf   = await sharp(rawPng).webp({ quality: 90 }).toBuffer();
    mimeType = "image/webp";
  } else {
    outBuf   = rawPng;
    mimeType = "image/png";
  }

  const b64      = outBuf.toString("base64");
  const dataUri  = `data:${mimeType};base64,${b64}`;
  const filename = opts.filename || `qr.${fmt === "jpg" ? "jpg" : fmt}`;
  const elapsed  = Date.now() - t0;

  return {
    success: true,
    meta: {
      format:   fmt,
      width:    finalW,
      height:   finalH,
      dotsColor:  cfg.dotsOptions.color,
      bgColor:    cfg.backgroundOptions.color,
      dotsType:   cfg.dotsOptions.type,
      errorLevel: cfg.qrOptions.errorCorrectionLevel,
      elapsed_ms: elapsed,
    },
    image: {
      base64:   b64,
      dataUri,
      filename,
      mimeType,
      size_bytes: outBuf.length,
    },
  };
}

// --- Main --------------------------------------------------------------------

(async () => {
  const opts = parseArgs(process.argv);

  if (!opts.data) {
    die("Missing required --data= argument");
  }

  try {
    const result = await render(opts);
    process.stdout.write(JSON.stringify(result) + "\n");
  } catch (err) {
    die(err.message || String(err));
  }
})();
