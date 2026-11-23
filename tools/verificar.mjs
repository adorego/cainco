// Verificación automática del sitio con Playwright.
// Uso:  CAINCO_ROOT=/ruta/al/repo node verificar.mjs [carpeta-salida]
//       (copiar este archivo a una carpeta con `npm i playwright`; ver tools/verificar.sh)
// - Capturas 390×844 y 1440×900, claro y oscuro
// - Flujo completo del formulario (perfil hogar y empresa) y contenido del enlace de WhatsApp
// - Errores de consola, imágenes que no cargan, JSON-LD parseable, desbordes horizontales
import { chromium } from "playwright";
import http from "node:http";
import fs from "node:fs";
import path from "node:path";

const ROOT = path.resolve(process.env.CAINCO_ROOT || path.join(path.dirname(new URL(import.meta.url).pathname), ".."));
const OUT = path.resolve(process.argv[2] || path.join(ROOT, "tools", ".verificacion"));
fs.mkdirSync(OUT, { recursive: true });

const MIME = { ".html": "text/html; charset=utf-8", ".jpg": "image/jpeg", ".webp": "image/webp", ".avif": "image/avif", ".png": "image/png", ".svg": "image/svg+xml", ".ico": "image/x-icon", ".xml": "application/xml", ".txt": "text/plain", ".webmanifest": "application/manifest+json" };
const server = http.createServer((req, res) => {
  let p = decodeURIComponent(new URL(req.url, "http://x").pathname);
  if (p.endsWith("/")) p += "index.html";
  const f = path.join(ROOT, p);
  if (!f.startsWith(ROOT) || !fs.existsSync(f) || p.includes("_originales")) { res.writeHead(404); return res.end("404"); }
  res.writeHead(200, { "content-type": MIME[path.extname(f)] || "application/octet-stream", "cache-control": "max-age=3600" });
  fs.createReadStream(f).pipe(res);
}).listen(0);
const BASE = `http://127.0.0.1:${server.address().port}/`;
console.log("sirviendo", BASE);

const browser = await chromium.launch();
const problemas = [];
const ok = (cond, msg) => { if (!cond) problemas.push(msg); console.log(cond ? "  ✔" : "  ✘", msg); };

async function nueva(vp, scheme) {
  const ctx = await browser.newContext({ viewport: vp, colorScheme: scheme, deviceScaleFactor: vp.width < 500 ? 2 : 1, hasTouch: vp.width < 500, isMobile: vp.width < 500 });
  // capturar window.open (el formulario abre WhatsApp)
  await ctx.addInitScript(() => { window.__abiertos = []; window.open = (u) => { window.__abiertos.push(u); return null; }; });
  const page = await ctx.newPage();
  const errores = [];
  page.on("console", m => { if (m.type() === "error") errores.push(m.text()); });
  page.on("pageerror", e => errores.push(String(e)));
  page.on("requestfailed", r => errores.push("falló " + r.url()));
  page.on("response", r => { if (r.status() >= 400 && r.url().startsWith(BASE)) errores.push(r.status() + " " + r.url()); });
  return { ctx, page, errores };
}

async function scrollTodo(page) {
  await page.evaluate(async () => {
    for (let y = 0; y < document.body.scrollHeight; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 60)); }
    window.scrollTo(0, 0);
  });
  await page.waitForLoadState("networkidle");
}

// 1) Capturas + controles generales
for (const [nombre, vp] of [["movil", { width: 390, height: 844 }], ["escritorio", { width: 1440, height: 900 }]]) {
  for (const scheme of ["light", "dark"]) {
    console.log(`\n== ${nombre} · ${scheme}`);
    const { ctx, page, errores } = await nueva(vp, scheme);
    await page.goto(BASE + "?debug=1", { waitUntil: "networkidle" });
    await page.screenshot({ path: path.join(OUT, `${nombre}-${scheme}-hero.png`) });
    await scrollTodo(page);
    if (await page.locator("#more").isVisible()) await page.locator("#more").click();
    await scrollTodo(page);
    await page.screenshot({ path: path.join(OUT, `${nombre}-${scheme}-full.png`), fullPage: true });
    // capturas por sección (más fáciles de revisar que la página entera)
    const secs = await page.evaluate(() => [...document.querySelectorAll("main > section[id], main > section, footer")].map((s, i) => s.id || `s${i}`));
    let n = 0;
    for (const el of await page.locator("main > section, footer").all()) {
      if (!(await el.isVisible())) { n++; continue; }
      const id = secs[n++];
      await el.screenshot({ path: path.join(OUT, `sec-${nombre}-${scheme}-${String(n).padStart(2, "0")}-${id}.png`) });
    }
    const rotas = await page.evaluate(() => [...document.images].filter(i => i.getAttribute("src") && i.complete && i.naturalWidth === 0).map(i => i.currentSrc || i.src));
    ok(rotas.length === 0, `imágenes que cargan (${rotas.length} rotas ${rotas.slice(0, 3).join(", ")})`);
    const sinDim = await page.evaluate(() => [...document.images].filter(i => !i.getAttribute("width") || !i.getAttribute("height")).length);
    ok(sinDim === 0, `todas las <img> con width/height (${sinDim} sin dimensiones)`);
    const ancho = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(ancho <= 0, `sin scroll horizontal (sobra ${ancho}px)`);
    const ld = await page.evaluate(() => [...document.querySelectorAll('script[type="application/ld+json"]')].map(s => { try { JSON.parse(s.textContent); return "ok"; } catch (e) { return String(e); } }));
    ok(ld.length >= 2 && ld.every(x => x === "ok"), `JSON-LD válido (${ld.join(", ")})`);
    // CTA visible: en móvil, después de bajar, la barra fija tiene que aparecer
    if (nombre === "movil") {
      await page.evaluate(() => window.scrollTo(0, document.querySelector("#servicios").offsetTop));
      await page.waitForTimeout(500);
      ok(await page.evaluate(() => document.body.classList.contains("bar-on")), "barra CTA móvil visible al bajar");
      await page.screenshot({ path: path.join(OUT, `${nombre}-${scheme}-scroll.png`) });
    }
    ok(errores.length === 0, `consola sin errores ${errores.slice(0, 3).join(" | ")}`);
    await ctx.close();
  }
}

// 2) Flujo del formulario
for (const perfil of ["hogar", "empresa"]) {
  console.log(`\n== formulario · ${perfil}`);
  const { ctx, page, errores } = await nueva({ width: 390, height: 844 }, "light");
  await page.goto(BASE + `?perfil=${perfil}&utm_source=instagram&utm_medium=paid&utm_campaign=prueba_${perfil}`, { waitUntil: "networkidle" });
  ok(await page.evaluate(() => document.documentElement.dataset.perfil) === perfil, "perfil tomado de la URL");
  const preset = await page.evaluate(() => document.querySelector("input[name=cliente]:checked")?.value);
  ok(preset === (perfil === "hogar" ? "Hogar" : "Empresa"), `tipo de cliente preseleccionado (${preset})`);
  // CTA contextual de servicio → preselecciona proyecto
  const svc = perfil === "hogar" ? "svc_cocina" : "svc_oficina";
  await page.locator(`[data-cta=${svc}]`).click();
  const proy = await page.evaluate(() => document.querySelector("input[name=proyecto]:checked")?.value);
  ok(proy === (perfil === "hogar" ? "Cocina" : "Oficina"), `CTA de servicio preselecciona proyecto (${proy})`);
  // Validación: paso 2 vacío no avanza
  await page.locator('.q-step[data-step="1"] [data-next]').click();
  await page.locator('.q-step[data-step="2"] [data-next]').click();
  ok(await page.locator("#e-zona").isVisible(), "validación amable en paso 2");
  await page.fill("#q-zona", "Asunción, Villa Morra");
  await page.selectOption("#q-etapa", { index: 2 });
  await page.selectOption("#q-plazo", { index: 3 });
  await page.fill("#q-med", "3,20 m × 2,60 m");
  await page.fill("#q-com", "Prueba automática");
  if (perfil === "empresa") { await page.fill("#q-empresa", "ACME SA"); await page.fill("#q-cant", "12 puestos"); }
  await page.screenshot({ path: path.join(OUT, `form-${perfil}-paso2.png`), fullPage: false });
  await page.locator('.q-step[data-step="2"] [data-next]').click();
  await page.fill("#q-nombre", "Ana Prueba");
  await page.fill("#q-tel", "0981 123 456");
  await page.locator('.q-step[data-step="3"] button[type=submit]').click();
  const url = await page.evaluate(() => window.__abiertos[0] || "");
  const txt = decodeURIComponent((url.split("text=")[1] || ""));
  console.log("   " + txt.replace(/\n/g, "\n   "));
  ok(url.startsWith("https://wa.me/595981429324?text="), "abre wa.me con el número de Cainco");
  for (const s of ["Asunción, Villa Morra", "Ana Prueba", "0981 123 456", "3,20 m", "Prueba automática", "utm_source=instagram", "utm_medium=paid", `utm_campaign=prueba_${perfil}`, `perfil=${perfil}`, proy])
    ok(txt.includes(s), `mensaje incluye «${s}»`);
  if (perfil === "empresa") ok(txt.includes("ACME SA") && txt.includes("12 puestos"), "mensaje incluye empresa y cantidad");
  await page.screenshot({ path: path.join(OUT, `form-${perfil}-enviado.png`) });
  ok(errores.length === 0, `consola sin errores ${errores.join(" | ")}`);
  await ctx.close();
}

// 3) Teclado: acordeón y lightbox
{
  console.log("\n== teclado");
  const { ctx, page } = await nueva({ width: 1440, height: 900 }, "light");
  await page.goto(BASE, { waitUntil: "networkidle" });
  await page.locator("#faq summary").first().focus();
  await page.keyboard.press("Enter");
  ok(await page.evaluate(() => document.querySelector("#faq details").open), "FAQ se abre con Enter");
  await page.locator(".tile").first().focus();
  await page.keyboard.press("Enter");
  ok(await page.locator("#lb").isVisible(), "lightbox se abre con Enter");
  await page.keyboard.press("ArrowRight");
  await page.keyboard.press("Escape");
  ok(await page.locator("#lb").isHidden(), "lightbox se cierra con Escape");
  ok(await page.evaluate(() => document.activeElement.classList.contains("tile")), "el foco vuelve a la foto");
  await ctx.close();
}

await browser.close();
server.close();
console.log(problemas.length ? `\n${problemas.length} PROBLEMAS:\n- ` + problemas.join("\n- ") : "\nTodo OK");
process.exit(problemas.length ? 1 : 0);
