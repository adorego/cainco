// Lighthouse móvil N veces sobre el sitio servido localmente (gzip + caché, como un hosting estático) → mediana.
// Uso (ver tools/lighthouse.sh): CAINCO_ROOT=/repo node lighthouse.mjs [carpeta-salida] [corridas]
import lighthouse from "lighthouse";
import * as chromeLauncher from "chrome-launcher";
import { chromium } from "playwright";
import http from "node:http";
import zlib from "node:zlib";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.env.CAINCO_ROOT);
const OUT = path.resolve(process.argv[2] || path.join(ROOT, "tools", ".verificacion"));
const N = +(process.argv[3] || 3);
fs.mkdirSync(OUT, { recursive: true });

const MIME = { ".html": "text/html; charset=utf-8", ".jpg": "image/jpeg", ".webp": "image/webp", ".avif": "image/avif", ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon", ".xml": "application/xml", ".txt": "text/plain", ".webmanifest": "application/manifest+json" };
const TEXTO = new Set([".html", ".svg", ".xml", ".txt", ".webmanifest"]);
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, "http://x").pathname);
  if (p.endsWith("/")) p += "index.html";
  const f = path.join(ROOT, p), ext = path.extname(f);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || p.includes("_originales") || p.includes("/tools/")) { res.writeHead(404); return res.end("404"); }
  const h = { "content-type": MIME[ext] || "application/octet-stream", "cache-control": ext === ".html" ? "no-cache" : "public, max-age=31536000, immutable" };
  if (TEXTO.has(ext) && /gzip/.test(req.headers["accept-encoding"] || "")) {
    res.writeHead(200, { ...h, "content-encoding": "gzip" }); fs.createReadStream(f).pipe(zlib.createGzip()).pipe(res);
  } else { res.writeHead(200, h); fs.createReadStream(f).pipe(res); }
}).listen(0);
const URL_ = `http://localhost:${server.address().port}/`;

const chrome = await chromeLauncher.launch({ chromePath: chromium.executablePath(), chromeFlags: ["--headless=new", "--no-sandbox", "--disable-gpu"] });
const CATS = ["performance", "accessibility", "best-practices", "seo"];
const runs = [];
for (let i = 1; i <= N; i++) {
  const r = await lighthouse(URL_, { port: chrome.port, output: ["json", "html"], logLevel: "error", onlyCategories: CATS, formFactor: "mobile" });
  const lhr = r.lhr;
  const s = Object.fromEntries(CATS.map(c => [c, Math.round(lhr.categories[c].score * 100)]));
  s.lcp = lhr.audits["largest-contentful-paint"].numericValue; s.cls = lhr.audits["cumulative-layout-shift"].numericValue;
  s.tbt = lhr.audits["total-blocking-time"].numericValue; s.fcp = lhr.audits["first-contentful-paint"].numericValue;
  runs.push({ s, lhr });
  fs.writeFileSync(path.join(OUT, `lighthouse-movil-${i}.html`), r.report[1]);
  console.log(`corrida ${i}: ` + CATS.map(c => `${c} ${s[c]}`).join(" · ") + ` · LCP ${(s.lcp / 1000).toFixed(2)} s · CLS ${s.cls.toFixed(3)} · TBT ${Math.round(s.tbt)} ms`);
}
await chrome.kill(); server.close();

const med = k => { const v = runs.map(r => r.s[k]).sort((a, b) => a - b); return v[Math.floor(v.length / 2)]; };
const M = Object.fromEntries([...CATS, "lcp", "cls", "tbt", "fcp"].map(k => [k, med(k)]));
console.log(`\nMEDIANA (${N} corridas): ` + CATS.map(c => `${c} ${M[c]}`).join(" · ") + ` · FCP ${(M.fcp / 1000).toFixed(2)} s · LCP ${(M.lcp / 1000).toFixed(2)} s · CLS ${M.cls.toFixed(3)} · TBT ${Math.round(M.tbt)} ms`);
fs.writeFileSync(path.join(OUT, "lighthouse-mediana.json"), JSON.stringify({ mediana: M, corridas: runs.map(r => r.s) }, null, 2));

// Lo que bajó del objetivo: auditorías que fallan en la corrida mediana de esa categoría
const META = { performance: 90, accessibility: 95, "best-practices": 95, seo: 95 };
let mal = 0;
for (const c of CATS) {
  if (M[c] >= META[c]) continue;
  mal++;
  const lhr = runs.find(r => r.s[c] === M[c]).lhr;
  console.log(`\n✘ ${c} ${M[c]} < ${META[c]}. Auditorías con problemas:`);
  for (const ref of lhr.categories[c].auditRefs) {
    const a = lhr.audits[ref.id];
    if (a.score !== null && a.score < 0.9 && ref.weight > 0) console.log(`  - ${a.id}: ${a.title} ${a.displayValue ? "(" + a.displayValue + ")" : ""}`);
  }
}
console.log(mal ? `\n${mal} categoría(s) bajo el objetivo` : "\n✔ Todas las categorías en objetivo (perf ≥ 90, resto ≥ 95)");
process.exit(mal ? 1 : 0);
