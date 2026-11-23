#!/usr/bin/env bash
# Chequeo antes de publicar: ¿el sitio está listo para salir?
#
#   bash tools/check-publicacion.sh
#
# 1. CAINCO_CONFIG (en index.html) vs. HTML estático:
#    - WhatsApp: todos los enlaces wa.me usan el número confirmado.
#    - Teléfono: tel: y JSON-LD "telephone" coinciden; el número visible aparece.
#    - Dirección: footer, JSON-LD (streetAddress/addressLocality/addressCountry) y enlace "Cómo llegar" bien codificado.
#    - Años de trayectoria visibles; sin foundingDate inventado.
#    - Nada "propuesto" o "pendiente" (p. ej. el email) aparece fuera de la config.
#    - Números viejos que ya no se usan.
# 2. JSON-LD parseable.
# 3. Rutas de imágenes (tools/actualizar_html.py --solo-verificar).
# 4. Lo que falta: datos no confirmados, placeholders visibles TODO_CAINCO y fotos a pedir.
#
# Salida: 0 = listo para publicar · 1 = hay errores (algo inconsistente o roto) · 2 = sin errores, pero con pendientes
set -uo pipefail
cd "$(dirname "$0")/.."

python3 - <<'PY'
import html, json, re, subprocess, sys, urllib.parse
from pathlib import Path

s = Path("index.html").read_text(encoding="utf-8")
errores, pendientes = [], []
ok = lambda msg: print("  ✔", msg)
def err(msg): errores.append(msg); print("  ✘", msg)

m = re.search(r"/\*CONFIG\*/(\{.*?\})/\*/CONFIG\*/", s, re.S)
if not m:
    print("✘ no encontré CAINCO_CONFIG (/*CONFIG*/ … /*/CONFIG*/) en index.html"); sys.exit(1)
try:
    CFG = json.loads(m.group(1))
except json.JSONDecodeError as e:
    print("✘ CAINCO_CONFIG no es JSON válido:", e); sys.exit(1)
fuera = s[:m.start()] + s[m.end():]           # el HTML sin el bloque de config
visible = re.sub(r"<!--.*?-->", "", fuera, flags=re.S)
texto = html.unescape(visible).replace("\xa0", " ")
conf = lambda k: CFG.get(k, {}).get("estado") == "confirmado" and CFG[k].get("valor")

ld = []
for b in re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S):
    try: ld.append(json.loads(b))
    except json.JSONDecodeError as e: err(f"JSON-LD inválido: {e}")
negocio = next((n for g in ld for n in g.get("@graph", [g]) if "LocalBusiness" in str(n.get("@type"))), {})

print("\n== WhatsApp")
if conf("whatsapp"):
    wa = CFG["whatsapp"]["valor"]
    links = re.findall(r'href="https://wa\.me/(\d*)', fuera)
    malos = sorted({n for n in links if n != wa})
    (err(f"enlaces wa.me con otro número: {', '.join(malos)}") if malos else ok(f"{len(links)} enlaces wa.me estáticos → {wa}"))
    (ok("el JS arma los enlaces con CAINCO_CONFIG.whatsapp") if re.search(r"WHATSAPP\s*=\s*window\.CAINCO_CONFIG\.whatsapp\.valor", fuera)
     else err("el JS no toma el número de CAINCO_CONFIG.whatsapp"))
    if conf("whatsapp_visible"):
        (ok(f"número visible «{CFG['whatsapp_visible']['valor']}»") if CFG["whatsapp_visible"]["valor"] in texto
         else err("no aparece el número de WhatsApp visible"))
else:
    pendientes.append("WhatsApp sin confirmar")

print("\n== Teléfono")
if conf("telefono"):
    tel = CFG["telefono"]["valor"]
    tels = re.findall(r'href="tel:([^"]*)"', fuera)
    if not tels: err("no hay ningún enlace tel:")
    malos = sorted({t for t in tels if t != tel})
    (err(f"enlaces tel: con otro número: {', '.join(malos)}") if malos else ok(f"{len(tels)} enlaces tel: → {tel}"))
    if not re.fullmatch(r"\+\d{8,15}", tel): err(f"tel: {tel} no está en formato internacional (+595…, sin espacios)")
    (ok("JSON-LD telephone") if negocio.get("telephone") == tel else err(f"JSON-LD telephone = {negocio.get('telephone')!r}, esperado {tel}"))
    if conf("telefono_visible"):
        (ok(f"número visible «{CFG['telefono_visible']['valor']}»") if CFG["telefono_visible"]["valor"] in texto
         else err("no aparece el teléfono visible"))
else:
    pendientes.append("teléfono sin confirmar")

print("\n== Dirección")
if conf("direccion"):
    d = CFG["direccion"]["valor"]
    calle = d.split(",")[0].strip()
    (ok(f"footer: «{calle}»") if calle in texto else err(f"la dirección «{calle}» no aparece en el sitio"))
    a = negocio.get("address", {})
    (ok("JSON-LD streetAddress / addressLocality / addressCountry")
     if (a.get("streetAddress"), a.get("addressLocality"), a.get("addressCountry")) == (calle, "Asunción", "PY")
     else err(f"JSON-LD address no coincide: {a}"))
    maps = "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(d, safe=".")
    hrefs = [html.unescape(h) for h in re.findall(r'href="(https://www\.google\.com/maps/[^"]*)"', fuera)]
    (ok("enlace «Cómo llegar» con la dirección codificada") if maps in hrefs and "Cómo llegar" in texto
     else err(f"falta el enlace «Cómo llegar» a {maps}"))
    if negocio.get("hasMap") and negocio["hasMap"] != maps: err("JSON-LD hasMap no coincide con la dirección")
    if "geo" in negocio: err("JSON-LD tiene coordenadas (geo): no inventarlas")
else:
    pendientes.append("dirección sin confirmar")

print("\n== Trayectoria")
if conf("anios_trayectoria"):
    v = CFG["anios_trayectoria"]["valor"]
    (ok(f"«{v}» visible") if v in texto else err(f"no aparece «{v}» en el sitio"))
    if "foundingDate" in s and "foundingDate" not in json.dumps(CFG): err("hay foundingDate: solo si se confirma el año exacto")

print("\n== Datos no confirmados (no deben publicarse)")
for k, v in CFG.items():
    if v.get("estado") != "confirmado":
        pendientes.append(f"config «{k}» en estado {v.get('estado')}" + (f": {v['nota']}" if v.get("nota") else "") + " (no se publica; no bloquea)")
        val = (v.get("valor") or "").strip()
        if val and val in fuera:
            err(f"«{k}» ({v['estado']}) aparece en el HTML fuera de la config: {val}")
        else:
            ok(f"«{k}» ({v['estado']}) no aparece en el sitio")
for viejo in ["981429324", "981 429 324", "981&nbsp;429&nbsp;324", "contacto@cainco.com.py"]:
    if viejo in s: err(f"queda un dato viejo: {viejo}")
if re.search(r'href="mailto:', fuera) and not conf("email"): err("hay un mailto: con el email sin confirmar")

print("\n== Rutas de imágenes")
r = subprocess.run([sys.executable, "tools/actualizar_html.py", "--solo-verificar"], capture_output=True, text=True)
print("  " + r.stdout.strip().replace("\n", "\n  "))
if r.returncode: errores.append("rutas de imágenes rotas")

print("\n== Placeholders visibles (bloquean la publicación)")
todos_visibles = re.findall(r'<span class="todo">(.*?)</span>', visible, re.S)
for t in todos_visibles: print("  ·", re.sub(r"<[^>]+>|\s+", " ", t).strip())
if todos_visibles: pendientes.append(f"{len(todos_visibles)} placeholders TODO_CAINCO visibles en la página")
n_todo = len(re.findall("TODO_CAINCO", s))
print(f"  ({n_todo} marcas TODO_CAINCO en total en index.html, contando comentarios)")

print("\n== Fotos a pedir (tools/reporte-fotos.md)")
rep = Path("tools/reporte-fotos.md")
if rep.exists():
    fotos = re.findall(r"^\|\s*\d+\s*\|\s*`([\w-]+)`.*\*\*(descartar|pedir original)\*\*", rep.read_text(encoding="utf-8"), re.M)
    for f, v in fotos: print(f"  · {f}: {v}")
    if fotos: pendientes.append(f"{len(fotos)} fotos para reemplazar (no bloquea)")

print("\n" + "=" * 60)
if errores:
    print(f"✘ {len(errores)} ERROR(ES):"); [print("  -", e) for e in errores]
if pendientes:
    print(f"… {len(pendientes)} PENDIENTE(S):"); [print("  -", p) for p in pendientes]
bloquea = [p for p in pendientes if "no bloquea" not in p]
if not errores and not bloquea: print("✔ Listo para publicar")
sys.exit(1 if errores else 2 if bloquea else 0)
PY
