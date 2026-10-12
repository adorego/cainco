"""Genera WebP, og-image.jpg e íconos. Uso: python3 tools/generar_assets.py . Archivo.ttf (fuente de github.com/google/fonts, ofl/archivo)"""
import glob, os, sys
from PIL import Image, ImageDraw, ImageFilter, ImageFont

REPO, FONT = sys.argv[1], sys.argv[2]
os.chdir(REPO)
INK, OAK, BG, STONE = (28, 32, 35), (160, 106, 52), (239, 240, 237), (35, 39, 42)
OAK_DARK = (211, 155, 94)

# 1. WebP (máx 1400 px, q78) + variante de 640 px de ancho
for jpg in sorted(glob.glob("img/*.jpg")):
    im = Image.open(jpg).convert("RGB")
    base = jpg[:-4]
    full = im.copy()
    full.thumbnail((1400, 1400), Image.LANCZOS)
    full.save(base + ".webp", "WEBP", quality=78, method=6)
    if im.width > 640:
        small = im.resize((640, round(im.height * 640 / im.width)), Image.LANCZOS)
        small.save(base + "-640.webp", "WEBP", quality=74, method=6)

# Logo: la "C" de tres tablones + tablón roble (viewBox 48x48)
LOGO = [((4, 4, 40, 8), "b"), ((4, 4, 8, 40), "b"), ((4, 36, 40, 8), "b"), ((16, 20, 20, 8), "a")]

def draw_logo(d, x0, y0, size, ink, oak):
    k = size / 48
    for (x, y, w, h), c in LOGO:
        d.rectangle([x0 + x * k, y0 + y * k, x0 + (x + w) * k - 1, y0 + (y + h) * k - 1], fill=oak if c == "a" else ink)

def icon(size, pad_ratio, bg=BG):
    """Logo centrado sobre fondo claro; pad_ratio deja zona segura para máscaras."""
    s = size * 4  # supersampling
    im = Image.new("RGB", (s, s), bg)
    logo = s * (1 - 2 * pad_ratio)
    draw_logo(ImageDraw.Draw(im), (s - logo) / 2, (s - logo) / 2, logo, INK, OAK)
    return im.resize((size, size), Image.LANCZOS)

# 2. Íconos
icon(180, 0.14).save("apple-touch-icon.png", optimize=True)
icon(192, 0.18).save("icon-192.png", optimize=True)
icon(512, 0.18).save("icon-512.png", optimize=True)
icon(32, 0.04).save("favicon.ico", sizes=[(16, 16), (32, 32)])

with open("favicon.svg", "w", encoding="utf-8") as f:
    f.write(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48">'
        "<style>.b{fill:#1c2023}.a{fill:#a06a34}"
        "@media (prefers-color-scheme:dark){.b{fill:#ebeae4}.a{fill:#d39b5e}}</style>"
        + "".join(f'<rect class="{c}" x="{x}" y="{y}" width="{w}" height="{h}"/>' for (x, y, w, h), c in LOGO)
        + "</svg>\n"
    )

# 3. OG image 1200x630 — todo lo importante dentro del cuadrado central (x 285–915)
W, H = 1200, 630
photo = Image.open("img/comercial-01.jpg").convert("RGB")
scale = W / photo.width
photo = photo.resize((W, round(photo.height * scale)), Image.LANCZOS)
top = round(420 * scale)  # percheros arriba, mesas exhibidoras de madera abajo
og = photo.crop((0, top, W, top + H))

# Oscurecer: velo general + centro más denso para que el texto se lea
shade = Image.new("L", (W, H), 0)
sd = ImageDraw.Draw(shade)
sd.ellipse([W / 2 - 430, H / 2 - 330, W / 2 + 430, H / 2 + 360], fill=255)
shade = shade.filter(ImageFilter.GaussianBlur(110))
dark = Image.new("RGB", (W, H), (14, 16, 17))
og = Image.blend(og, dark, 0.35)
og = Image.composite(dark, og, shade.point(lambda v: int(v * 0.82)))
d = ImageDraw.Draw(og)

def font(size, wght, wdth):
    f = ImageFont.truetype(FONT, size)
    f.set_variation_by_axes([wght, wdth])
    return f

def centered(text, y, f, fill, tracking=0):
    widths = [d.textlength(ch, font=f) for ch in text]
    total = sum(widths) + tracking * (len(text) - 1)
    x = (W - total) / 2
    for ch, w in zip(text, widths):
        d.text((x, y), ch, font=f, fill=fill)
        x += w + tracking

logo = 112
lx, ly = (W - logo) / 2, 92
d.rectangle([lx - 14, ly - 14, lx + logo + 14, ly + logo + 14], fill=BG)
draw_logo(d, lx, ly, logo, INK, OAK)

centered("CAINCO", 248, font(84, 900, 125), (235, 234, 228), tracking=8)
centered("MUEBLES A MEDIDA", 352, font(46, 850, 108), OAK_DARK, tracking=2)
d.line([(W / 2 - 60, 438), (W / 2 + 60, 438)], fill=(235, 234, 228), width=2)
centered("Cocinas · Placares · Oficinas · Locales", 458, font(28, 500, 100), (220, 220, 214))
centered("cainco.com.py", 540, font(24, 600, 110), (190, 192, 186), tracking=2)

og.save("og-image.jpg", "JPEG", quality=84, optimize=True, progressive=True)
print("og-image.jpg", os.path.getsize("og-image.jpg") // 1024, "KB")
