#!/usr/bin/env python3
"""
Conecta las fotos procesadas (tools/fotos.json) con index.html y sitemap.xml.

En index.html reemplaza:
  /*FOTOS*/ … /*/FOTOS*/                     → datos de dimensiones/anchos para el JS
  <!--foto:ID sizes="…" alt="…" [hero]--> … <!--/foto-->   → <picture> AVIF → WebP → JPG
  <!--preload-hero--> … <!--/preload-hero-->  → preload de la imagen LCP
El ID "HERO" se resuelve con "_hero" de tools/fotos-ajustes.json.

Fotos descartadas: se leen del veredicto "descartar" en tools/reporte-fotos.md
(y de "decision": "descartar" en fotos-ajustes.json). Quedan fuera de FOTOS,
del sitemap y no se pueden usar en el HTML.

Antes de escribir, verifica todas las rutas locales del HTML resultante
(src, srcset, href, imagesrcset, og:image, JSON-LD, preload, galería/lightbox).
Si algo apunta a una foto descartada o a un archivo que no existe en el repo,
no escribe nada y termina con error.

Uso:
  python3 tools/actualizar_html.py                 # actualiza y verifica
  python3 tools/actualizar_html.py --solo-verificar  # solo verifica el HTML actual

Idempotente: se puede correr las veces que haga falta.
"""
import datetime
import html
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
REPORTE = ROOT / "tools" / "reporte-fotos.md"
DOMINIO = "https://cainco.com.py/"
FORMATOS = ("avif", "webp", "jpg")

AJ = json.loads((ROOT / "tools" / "fotos-ajustes.json").read_text(encoding="utf-8"))
HERO = AJ.get("_hero", {"id": "bano-01", "alt": "Mueble a medida de Cainco"})


def descartadas():
    """IDs con veredicto 'descartar' en el reporte (+ los marcados en fotos-ajustes.json)."""
    ids = {k for k, v in AJ.items() if isinstance(v, dict) and v.get("decision") == "descartar"}
    if REPORTE.exists():
        for m in re.finditer(r"^\|\s*\d+\s*\|\s*`([\w-]+)`\s*\|.*\*\*descartar\*\*", REPORTE.read_text(encoding="utf-8"), re.M):
            ids.add(m.group(1))
    else:
        print(f"  ! no existe {REPORTE.relative_to(ROOT)}: solo uso las decisiones de fotos-ajustes.json")
    return ids


DESCARTADAS = descartadas()
FOTOS = {k: v for k, v in json.loads((ROOT / "tools" / "fotos.json").read_text(encoding="utf-8")).items()
         if k not in DESCARTADAS}


def srcset(ident, ext):
    return ", ".join(f"img/{ident}-{w}.{ext} {w}w" for w in FOTOS[ident]["widths"])


def picture(ident, sizes, alt, hero=False):
    f = FOTOS[ident]
    fb = 1024 if 1024 in f["widths"] else f["widths"][-1]
    h = round(f["h"] * fb / f["w"])
    extra = ' fetchpriority="high" decoding="async"' if hero else ' loading="lazy" decoding="async"'
    return (f'<picture><source type="image/avif" srcset="{srcset(ident, "avif")}" sizes="{sizes}">'
            f'<source type="image/webp" srcset="{srcset(ident, "webp")}" sizes="{sizes}">'
            f'<img src="img/{ident}-{fb}.jpg" srcset="{srcset(ident, "jpg")}" sizes="{sizes}" '
            f'width="{fb}" height="{h}" alt="{html.escape(alt, quote=True)}"{extra}></picture>')


def variantes_faltantes(ident):
    """Archivos que el JS/HTML pide para una foto y no existen en img/."""
    if ident not in FOTOS:
        return [f"img/{ident}-*.(avif|webp|jpg) (no está en fotos.json)"]
    return [p for w in FOTOS[ident]["widths"] for ext in FORMATOS
            if not (ROOT / (p := f"img/{ident}-{w}.{ext}")).is_file()]


# ---------------------------------------------------------------- verificación
RUTA = re.compile(r"(?<![\w$}/.-])(?:" + re.escape(DOMINIO) + r")?((?:img/)?[\w-][\w./-]*\.(?:avif|webp|jpe?g|png|svg|ico|webmanifest|gif))\b")


def verificar(s):
    errores = []

    def err(msg):
        errores.append(msg)

    # 1) rutas literales en todo el HTML: src/srcset/href/imagesrcset/og:image/twitter:image/JSON-LD
    usadas = {}
    for n, linea in enumerate(s.splitlines(), 1):
        for m in RUTA.finditer(linea):
            usadas.setdefault(m.group(1), n)
    for ruta, n in sorted(usadas.items(), key=lambda x: x[1]):
        if "_originales" in ruta:
            err(f"línea {n}: {ruta} apunta a los originales (no se publican)")
        elif not (ROOT / ruta).is_file():
            err(f"línea {n}: {ruta} no existe")
        m = re.match(r"img/([a-z]+-\d+)(?:-\d+)?\.", ruta)
        if m and m.group(1) in DESCARTADAS:
            err(f"línea {n}: {ruta} es de una foto descartada ({m.group(1)})")

    # 2) marcadores <!--foto:ID--> y hero
    for m in re.finditer(r"<!--foto:([\w-]+)", s):
        ident = HERO["id"] if m.group(1) == "HERO" else m.group(1)
        if ident in DESCARTADAS:
            err(f"marcador foto:{m.group(1)} usa {ident}, que está descartada")
        for f in variantes_faltantes(ident):
            err(f"marcador foto:{m.group(1)}: falta {f}")

    # 3) galería y lightbox: el JS arma las rutas desde FOTOS con los ids de W
    bloque = re.search(r"const W = \[(.*?)\n\]", s, re.S)
    if not bloque:
        err("no encontré el array de la galería (const W = [ … ])")
    else:
        for m in re.finditer(r'^\s*\["([\w-]+)",', bloque.group(1), re.M):  # las líneas comentadas con // no cuentan
            ident = m.group(1)
            if ident in DESCARTADAS:
                err(f"galería: {ident} está descartada; sacala o comentala con TODO_CAINCO")
            for f in variantes_faltantes(ident):
                err(f"galería/lightbox: {ident}: falta {f}")

    # 4) datos FOTOS embebidos: no deben incluir descartadas
    datos = re.search(r"/\*FOTOS\*/const FOTOS = (\{.*?\});/\*/FOTOS\*/", s, re.S)
    if datos:
        for ident in json.loads(datos.group(1)):
            if ident in DESCARTADAS:
                err(f"FOTOS (JS) incluye {ident}, que está descartada")
            for f in variantes_faltantes(ident):
                err(f"FOTOS (JS): {ident}: falta {f}")

    # 5) íconos del manifest
    man = ROOT / "site.webmanifest"
    if man.is_file():
        for icon in json.loads(man.read_text(encoding="utf-8")).get("icons", []):
            if not (ROOT / icon["src"].lstrip("/")).is_file():
                err(f"site.webmanifest: {icon['src']} no existe")

    return errores, len(usadas)


def main():
    solo_verificar = "--solo-verificar" in sys.argv
    s = INDEX.read_text(encoding="utf-8")

    if not solo_verificar:
        data = {k: {"w": v["w"], "h": v["h"], "widths": v["widths"], "score": v.get("score", 0)} for k, v in FOTOS.items()}
        s = re.sub(r"/\*FOTOS\*/.*?/\*/FOTOS\*/",
                   lambda m: "/*FOTOS*/const FOTOS = " + json.dumps(data, separators=(",", ":")) + ";/*/FOTOS*/",
                   s, flags=re.S)

        def rep(m):
            ident, attrs = m.group(1), m.group(2)
            a = dict(re.findall(r'(\w+)="([^"]*)"', attrs))
            hero = " hero" in attrs
            real = HERO["id"] if ident == "HERO" else ident
            alt = HERO["alt"] if ident == "HERO" else a.get("alt", "")
            if real not in FOTOS:  # la verificación de abajo lo reporta como error
                return m.group(0)
            return f"<!--foto:{ident}{attrs}-->" + picture(real, a.get("sizes", "100vw"), alt, hero) + "<!--/foto-->"

        s = re.sub(r"<!--foto:([\w-]+)((?:(?!-->).)*)-->.*?<!--/foto-->", rep, s, flags=re.S)

        hid = HERO["id"]
        if hid in FOTOS:
            pre = (f'<link rel="preload" as="image" type="image/avif" href="img/{hid}-1024.avif" imagesrcset="{srcset(hid, "avif")}" '
                   f'imagesizes="100vw" fetchpriority="high">')
            s = re.sub(r"<!--preload-hero-->.*?<!--/preload-hero-->",
                       lambda m: f"<!--preload-hero-->\n{pre}\n<!--/preload-hero-->", s, flags=re.S)
        s = re.sub(r'(<span class="hero-cap" id="hero-cap">).*?(</span>)',
                   lambda m: m.group(1) + html.escape(HERO.get("cap", "Trabajo real de Cainco")) + m.group(2), s)

    errores, n = verificar(s)
    if errores:
        print(f"ERROR: {len(errores)} referencia(s) rota(s) en index.html" + ("" if solo_verificar else " — no se escribió nada:"))
        for e in errores:
            print("  ✗", e)
        sys.exit(1)

    if solo_verificar:
        print(f"OK: {n} rutas distintas verificadas en index.html, ninguna rota (descartadas: {', '.join(sorted(DESCARTADAS)) or 'ninguna'})")
        return

    INDEX.write_text(s, encoding="utf-8")

    hoy = datetime.date.today().isoformat()
    imgs = ["og-image.jpg"] + [f"img/{k}.jpg" for k in sorted(FOTOS)]
    faltan = [p for p in imgs if not (ROOT / p).is_file()]
    if faltan:
        print("ERROR: el sitemap apuntaría a archivos que no existen:", ", ".join(faltan))
        sys.exit(1)
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
          '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
          "  <url>", f"    <loc>{DOMINIO}</loc>", f"    <lastmod>{hoy}</lastmod>"]
    sm += [f"    <image:image><image:loc>{DOMINIO}{p}</image:loc></image:image>" for p in imgs]
    sm += ["  </url>", "</urlset>", ""]
    SITEMAP.write_text("\n".join(sm), encoding="utf-8")
    print(f"index.html y sitemap.xml actualizados ({len(FOTOS)} fotos, hero: {HERO['id']}, "
          f"descartadas: {', '.join(sorted(DESCARTADAS)) or 'ninguna'}); {n} rutas verificadas, ninguna rota")


if __name__ == "__main__":
    main()
