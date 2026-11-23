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
// Datos de contacto: se leen de CAINCO_CONFIG (index.html), la misma fuente que usa el sitio
const CFG = JSON.parse(fs.readFileSync(path.join(ROOT, "index.html"), "utf8").match(/\/\*CONFIG\*\/(\{[\s\S]*?\})\/\*\/CONFIG\*\//)[1]);
const WA = CFG.whatsapp.valor, TEL = CFG.telefono.valor;
console.log("WhatsApp", WA, "· tel", TEL);

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
    // Página limpia: sin TODO, sin modo revisión y sin bloques de datos que faltan
    const limpio = await page.evaluate(() => ({
      todo: (document.body.innerText.match(/TODO_CAINCO/g) || []).length + document.querySelectorAll(".todo").length,
      rev: document.querySelectorAll("[data-rev], .rev-bar").length,
      faltan: [...document.querySelectorAll("[data-requires], [data-requires-any]")].filter(e => e.checkVisibility && e.checkVisibility()).map(e => e.dataset.requires || e.dataset.requiresAny)
    }));
    ok(limpio.todo === 0 && limpio.rev === 0, `sin TODO ni marcas de revisión visibles (${limpio.todo} TODO, ${limpio.rev} marcas)`);
    ok(limpio.faltan.length === 0, `datos en "falta" ocultos (visibles: ${limpio.faltan.join(", ") || "ninguno"})`);
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
  ok(url.startsWith(`https://wa.me/${WA}?text=`), `formulario abre wa.me/${WA}`);
  for (const s of ["Asunción, Villa Morra", "Ana Prueba", "0981 123 456", "3,20 m", "Prueba automática", "utm_source=instagram", "utm_medium=paid", `utm_campaign=prueba_${perfil}`, `perfil=${perfil}`, proy])
    ok(txt.includes(s), `mensaje incluye «${s}»`);
  if (perfil === "empresa") ok(txt.includes("ACME SA") && txt.includes("12 puestos"), "mensaje incluye empresa y cantidad");
  await page.screenshot({ path: path.join(OUT, `form-${perfil}-enviado.png`) });
  // Resto de los enlaces de WhatsApp: el href estático y el que arma el JS al hacer clic
  const estaticos = await page.evaluate(() => [...document.querySelectorAll('a[href*="wa.me"]')].map(a => a.getAttribute("href")));
  ok(estaticos.length >= 3 && estaticos.every(h => h.startsWith(`https://wa.me/${WA}`)), `${estaticos.length} enlaces wa.me apuntan a ${WA}`);
  const clics = await page.evaluate(() => {
    document.addEventListener("click", e => { if (e.target.closest('a[href*="wa.me"]')) e.preventDefault(); }); // no navegar
    return ["#wa-float", '[data-cta="cierre_wa"]', '[data-cta="footer_wa"]'].map(sel => { const a = document.querySelector(sel); a.click(); return [sel, a.href]; });
  });
  for (const [sel, href] of clics) {
    const t = decodeURIComponent(href.split("text=")[1] || "");
    ok(href.startsWith(`https://wa.me/${WA}?text=`) && t.startsWith("Hola Cainco") && t.includes(`perfil=${perfil}`) && t.includes("utm_source=instagram") && t.includes(`utm_campaign=prueba_${perfil}`),
      `${sel} → wa.me/${WA} con saludo, perfil y UTM («${t.replace(/\n+/g, " ⏎ ")}»)`);
  }
  // Barra móvil y CTAs contextuales llevan al formulario, que termina en el mismo wa.me (probado arriba)
  const destinos = await page.evaluate(() => ["#mbar a", "[data-cta=svc_cocina]", "[data-cta=svc_oficina]", "[data-cta=empresas]", "[data-cta=header]"].map(s => document.querySelector(s)?.getAttribute("href")));
  ok(destinos.every(h => h === "#presupuesto"), `barra móvil y CTAs contextuales → #presupuesto (${destinos.join(", ")})`);
  // tel: en móvil: formato internacional y área táctil cómoda
  const tels = await page.evaluate(() => [...document.querySelectorAll('a[href^="tel:"]')].map(a => { a.scrollIntoView(); const r = a.getBoundingClientRect(); return [a.getAttribute("href"), Math.round(r.height), Math.round(r.width)]; }));
  ok(tels.length >= 1 && tels.every(([h, alto]) => h === `tel:${TEL}` && alto >= 44), `enlaces tel: → ${TEL}, ≥44px de alto (${tels.map(t => t.join(" ")).join(" | ")})`);
  const mapa = await page.locator("footer a", { hasText: "Cómo llegar" }).getAttribute("href");
  ok(mapa === "https://www.google.com/maps/search/?api=1&query=" + encodeURIComponent(CFG.direccion.valor), `«Cómo llegar» → ${mapa}`);
  const fuente = await (await page.request.get(BASE)).text();   // el HTML servido ("ver código fuente")
  ok(!/[\w.+-]+@cainco\.com\.py/i.test(fuente) && !(await page.evaluate(() => document.body.innerText.includes("@"))), "ningún email en el HTML servido ni en la página");
  ok(errores.length === 0, `consola sin errores ${errores.join(" | ")}`);
  await ctx.close();
}

// 2b) Modo revisión (?revision=1): textos propuestos subrayados con su clave
for (const [nombre, vp] of [["movil", { width: 390, height: 844 }], ["escritorio", { width: 1440, height: 900 }]]) {
  console.log(`\n== revisión · ${nombre}`);
  const { ctx, page, errores } = await nueva(vp, "light");
  await page.goto(BASE + "?revision=1", { waitUntil: "networkidle" });
  const propuestos = Object.keys(CFG).filter(k => CFG[k].estado === "propuesto");
  const r = await page.evaluate(() => ({
    bar: !!document.querySelector(".rev-bar"),
    marcas: [...document.querySelectorAll("[data-rev]")].map(e => e.dataset.cfg),
    todo: (document.body.innerText.match(/TODO_CAINCO/g) || []).length
  }));
  ok(r.bar, "aparece el aviso de modo revisión");
  const sinMarca = propuestos.filter(k => !r.marcas.includes(k));
  ok(r.marcas.length > 0 && sinMarca.length === 0, `${r.marcas.length} textos marcados, todas las claves propuestas presentes (sin marca: ${sinMarca.join(", ") || "ninguna"})`);
  ok(r.todo === 0, "sin TODO visibles en modo revisión");
  await page.screenshot({ path: path.join(OUT, `rev-${nombre}-hero.png`) });
  // tooltip: foco en un texto propuesto
  const t = page.locator("#proceso [data-rev][tabindex]").first();
  await t.scrollIntoViewIfNeeded(); await t.focus(); await page.waitForTimeout(150);
  await page.locator("#proceso").screenshot({ path: path.join(OUT, `rev-${nombre}-proceso-tooltip.png`) });
  for (const id of ["faq", "empresas"]) await page.locator("#" + id).screenshot({ path: path.join(OUT, `rev-${nombre}-${id}.png`) });
  await page.locator("footer").screenshot({ path: path.join(OUT, `rev-${nombre}-footer.png`) });
  const ancho = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  ok(ancho <= 0, `sin scroll horizontal en revisión (sobra ${ancho}px)`);
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
