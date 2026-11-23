#!/usr/bin/env python3
"""
Conecta las fotos procesadas (tools/fotos.json) con index.html y sitemap.xml.

En index.html reemplaza:
  /*FOTOS*/ … /*/FOTOS*/                     → datos de dimensiones/anchos para el JS
  <!--foto:ID sizes="…" alt="…" [hero]--> … <!--/foto-->   → <picture> AVIF → WebP → JPG
  <!--preload-hero--> … <!--/preload-hero-->  → preload de la imagen LCP
El ID "HERO" se resuelve con "_hero" de tools/fotos-ajustes.json.

Idempotente: se puede correr las veces que haga falta.
"""
import datetime
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "index.html"
SITEMAP = ROOT / "sitemap.xml"
FOTOS = json.loads((ROOT / "tools" / "fotos.json").read_text(encoding="utf-8"))
AJ = json.loads((ROOT / "tools" / "fotos-ajustes.json").read_text(encoding="utf-8"))
HERO = AJ.get("_hero", {"id": "bano-01", "alt": "Mueble a medida de Cainco"})


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


def main():
    s = INDEX.read_text(encoding="utf-8")

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
        if real not in FOTOS:
            print(f"  ! foto {real} no está en fotos.json (¿descartada?)")
            return m.group(0).split("-->")[0] + "--><!--/foto-->"
        return f"<!--foto:{ident}{attrs}-->" + picture(real, a.get("sizes", "100vw"), alt, hero) + "<!--/foto-->"

    s = re.sub(r"<!--foto:([\w-]+)((?:(?!-->).)*)-->.*?<!--/foto-->", rep, s, flags=re.S)

    hid = HERO["id"]
    pre = (f'<link rel="preload" as="image" type="image/avif" imagesrcset="{srcset(hid, "avif")}" '
           f'imagesizes="100vw" fetchpriority="high">')
    s = re.sub(r"<!--preload-hero-->.*?<!--/preload-hero-->",
               lambda m: f"<!--preload-hero-->\n{pre}\n<!--/preload-hero-->", s, flags=re.S)
    s = re.sub(r'(<span class="hero-cap" id="hero-cap">).*?(</span>)',
               lambda m: m.group(1) + html.escape(HERO.get("cap", "Trabajo real de Cainco")) + m.group(2), s)
    INDEX.write_text(s, encoding="utf-8")

    hoy = datetime.date.today().isoformat()
    imgs = ["og-image.jpg"] + [f"img/{k}.jpg" for k in sorted(FOTOS)]
    sm = ['<?xml version="1.0" encoding="UTF-8"?>',
          '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"',
          '        xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">',
          "  <url>", "    <loc>https://cainco.com.py/</loc>", f"    <lastmod>{hoy}</lastmod>"]
    sm += [f"    <image:image><image:loc>https://cainco.com.py/{p}</image:loc></image:image>" for p in imgs]
    sm += ["  </url>", "</urlset>", ""]
    SITEMAP.write_text("\n".join(sm), encoding="utf-8")
    print(f"index.html y sitemap.xml actualizados ({len(FOTOS)} fotos, hero: {hid})")


if __name__ == "__main__":
    main()
