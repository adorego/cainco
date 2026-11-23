#!/usr/bin/env bash
# Chequeo antes de publicar: ¿el sitio está listo para salir?
#
#   bash tools/check-publicacion.sh
#
# 1. CAINCO_CONFIG (en index.html): cada entrada con estado "confirmado" | "propuesto" | "falta".
# 2. Config vs. HTML estático:
#    - WhatsApp (obligatorio y confirmado): todos los enlaces wa.me usan ese número.
#    - Teléfono: tel: y JSON-LD "telephone" coinciden; el número visible aparece.
#    - Dirección: footer, JSON-LD (streetAddress/addressLocality/addressCountry) y enlace "Cómo llegar" bien codificado.
#    - Años de trayectoria visibles; sin foundingDate inventado.
#    - data-cfg="clave": la clave existe y no está en "falta".
#    - data-requires="clave": si el dato está en "falta", el elemento sale oculto (atributo hidden).
#    - Ningún email en el HTML servido (ni en comentarios ni en la config) y ningún número viejo.
# 3. Ningún TODO_CAINCO visible (texto, atributos, JSON-LD o strings del JS; los comentarios no cuentan).
# 4. JSON-LD parseable y rutas de imágenes (tools/actualizar_html.py --solo-verificar).
# 5. Avisos (no bloquean): datos en "falta" (ocultos) y fotos a reemplazar.
#
# Salida: 1 = errores (imágenes rotas, TODO visible, falta WhatsApp, inconsistencias)
#         2 = sin errores, pero quedan valores "propuesto": no se publica hasta que el cliente los confirme
#         0 = listo para publicar
set -uo pipefail
cd "$(dirname "$0")/.."

python3 - <<'PY'
import html, json, re, subprocess, sys, urllib.parse
from pathlib import Path

s = Path("index.html").read_text(encoding="utf-8")
errores, avisos = [], []
ok = lambda msg: print("  ✔", msg)
def err(msg): errores.append(msg); print("  ✘", msg)
ESTADOS = ("confirmado", "propuesto", "falta")

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
por_estado = lambda e: [k for k, v in CFG.items() if v.get("estado") == e]

print("== CAINCO_CONFIG")
malos = [f"{k}={v.get('estado')!r}" for k, v in CFG.items() if v.get("estado") not in ESTADOS]
(err("estados inválidos (usar confirmado | propuesto | falta): " + ", ".join(malos)) if malos
 else ok(f"{len(CFG)} entradas: {len(por_estado('confirmado'))} confirmadas, {len(por_estado('propuesto'))} propuestas, {len(por_estado('falta'))} en falta"))
if not conf("whatsapp"):
    err("falta el WhatsApp confirmado (CAINCO_CONFIG.whatsapp): sin eso no hay embudo")

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

print("\n== Trayectoria")
if conf("anios_trayectoria"):
    v = CFG["anios_trayectoria"]["valor"]
    (ok(f"«{v}» visible") if v in texto else err(f"no aparece «{v}» en el sitio"))
    if "foundingDate" in negocio: err("JSON-LD tiene foundingDate: solo si se confirma el año exacto")

print("\n== Textos de la config (data-cfg) y datos que faltan (data-requires)")
etiquetas = lambda attr: re.findall(r"<[a-z][^>]*\s" + attr + r'="([^"]*)"[^>]*>', visible)
usadas = set()
for k in etiquetas("data-cfg"):
    usadas.add(k)
    if k not in CFG: err(f'data-cfg="{k}" no existe en CAINCO_CONFIG')
    elif CFG[k].get("estado") == "falta": err(f'data-cfg="{k}" muestra un dato que está en "falta"')
for k in por_estado("propuesto"):
    if k not in usadas: avisos.append(f"«{k}» está propuesto pero ningún elemento lo marca con data-cfg")
n_req = 0
for tag in re.findall(r'<[a-z][^>]*\sdata-requires(?:-any)?="[^"]*"[^>]*>', visible):
    n_req += 1
    claves = re.search(r'data-requires(?:-any)?="([^"]*)"', tag).group(1).split()
    for k in claves:
        if k not in CFG: err(f'data-requires="{k}" no existe en CAINCO_CONFIG')
    faltan = [k for k in claves if CFG.get(k, {}).get("estado") == "falta"]
    cualquiera = "data-requires-any=" in tag
    oculto_debe = (len(faltan) == len(claves)) if cualquiera else bool(faltan)
    if oculto_debe and not re.search(r"\shidden(?=[\s>=])", tag):
        err(f"elemento con data-requires {claves} se vería sin el dato: falta el atributo hidden")
ok(f"{len(usadas)} claves marcadas con data-cfg · {n_req} elementos con data-requires revisados")

print("\n== Email y datos viejos")
emails = sorted(set(re.findall(r"[\w.+-]+@[\w-]+\.[\w.-]*[a-z]", s, re.I)))
(err("hay emails en el HTML servido (también cuentan comentarios y la config): " + ", ".join(emails)) if emails
 else ok("ningún email en el HTML servido"))
if "mailto:" in s: err("hay un enlace mailto:")
for viejo in ["981429324", "981 429 324", "981&nbsp;429&nbsp;324"]:
    if viejo in s: err(f"queda un dato viejo: {viejo}")

print("\n== Rutas de imágenes")
r = subprocess.run([sys.executable, "tools/actualizar_html.py", "--solo-verificar"], capture_output=True, text=True)
print("  " + r.stdout.strip().replace("\n", "\n  "))
if r.returncode: errores.append("rutas de imágenes rotas")

print("\n== TODO visibles")
sin_scripts = re.sub(r"<script\b(?![^>]*ld\+json)[^>]*>.*?</script>", "", visible, flags=re.S)   # el JSON-LD sí cuenta
js = "\n".join(re.findall(r"<script\b(?![^>]*ld\+json)[^>]*>(.*?)</script>", visible, re.S))
js = re.sub(r"/\*.*?\*/", "", js, flags=re.S)
js = re.sub(r"(?m)(^|[^:\"'])//[^\n]*", r"\1", js)                                          # comentarios de JS (no URLs)
hallados = [("HTML", m) for m in re.findall(r"[^<>\n]{0,40}TODO_CAINCO[^<>\n]{0,60}", sin_scripts)]
hallados += [("JS", m) for m in re.findall(r"[^\n]{0,40}TODO_CAINCO[^\n]{0,60}", js)]
hallados += [("HTML", "elemento con class=\"todo\"")] * len(re.findall(r'class="[^"]*\btodo\b', sin_scripts))
for d, t in hallados: err(f"TODO visible ({d}): {t.strip()}")
if not hallados: ok("ningún TODO_CAINCO visible (texto, atributos, JSON-LD ni strings del JS)")
print(f"  ({len(re.findall('TODO_CAINCO', s))} marcas TODO_CAINCO en comentarios del código, no se ven)")

print("\n== Valores propuestos (el cliente tiene que confirmarlos)")
for k in por_estado("propuesto"):
    v = CFG[k]["valor"]
    print(f"  · {k}: {' / '.join(v) if isinstance(v, list) else v}")

print("\n== Datos en falta (ocultos, no bloquean)")
for k in por_estado("falta"):
    avisos.append(f"{k}: falta" + (f" ({CFG[k]['nota']})" if CFG[k].get("nota") else ""))
    print(f"  · {k}")

print("\n== Fotos a pedir (tools/reporte-fotos.md)")
rep = Path("tools/reporte-fotos.md")
if rep.exists():
    fotos = re.findall(r"^\|\s*\d+\s*\|\s*`([\w-]+)`.*\*\*(descartar|pedir original)\*\*", rep.read_text(encoding="utf-8"), re.M)
    for f, v in fotos: print(f"  · {f}: {v}")
    if fotos: avisos.append(f"{len(fotos)} fotos para reemplazar: " + ", ".join(f for f, _ in fotos))

prop = por_estado("propuesto")
print("\n" + "=" * 60)
if errores:
    print(f"✘ {len(errores)} ERROR(ES):"); [print("  -", e) for e in errores]
if avisos:
    print(f"⚠ {len(avisos)} AVISO(S) (no bloquean):"); [print("  -", a) for a in avisos]
if prop:
    print(f"… {len(prop)} VALOR(ES) PROPUESTO(S) sin confirmar: {', '.join(prop)}")
if errores: print("✘ NO PUBLICAR: hay errores (salida 1)")
elif prop: print("… NO PUBLICAR TODAVÍA: faltan confirmaciones del cliente (salida 2)")
else: print("✔ Listo para publicar (salida 0)")
sys.exit(1 if errores else 2 if prop else 0)
PY
