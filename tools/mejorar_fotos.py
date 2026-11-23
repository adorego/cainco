#!/usr/bin/env python3
"""
Pipeline de mejora de fotos de trabajos de Cainco (idempotente).

Reglas: NO se usa IA generativa que agregue/quite/rediseñe objetos ni cambie
materiales. Solo: super-resolución (Real-ESRGAN, restauración, no generación de
contenido nuevo), limpieza de artefactos, color/exposición, enderezado,
recorte y nitidez moderada.

Fuente de verdad: img/_originales/<id>.jpg (nunca se sobrescriben).
Si falta un original, se copia desde img/<id>.jpg la primera vez.

Uso:
  python tools/mejorar_fotos.py              # todo: diagnóstico + mejora + export + QC
  python tools/mejorar_fotos.py --solo-diagnostico
  python tools/mejorar_fotos.py --ids cocina-01 bano-02
  python tools/mejorar_fotos.py --forzar     # reprocesa aunque exista caché

Requiere (venv): torch (CPU alcanza), opencv-python-headless, pillow>=11 (AVIF), numpy.
Pesos: RealESRGAN_x4plus.pth y RealESRGAN_x2plus.pth en $CAINCO_SR_DIR
(por defecto ~/.cache/cainco-sr). tools/hd.sh los descarga si faltan.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import math
import os
import shutil
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent.parent
IMG = ROOT / "img"
ORIG = IMG / "_originales"
CACHE = ROOT / "tools" / ".cache-sr"          # salida de super-resolución (gitignored)
QC = ROOT / "tools" / "antes-despues"
REPORT = ROOT / "tools" / "reporte-fotos.md"
MANIFEST = ROOT / "tools" / "fotos.json"
SR_DIR = Path(os.environ.get("CAINCO_SR_DIR", Path.home() / ".cache" / "cainco-sr"))

WIDTHS = [640, 1024, 1600, 2400]   # 2400 solo si la foto lo justifica (ver MAX_REAL)
MAX_KB_1600 = 250
# Factor máximo de agrandamiento "creíble" respecto del original: más allá de esto
# el detalle sería inventado por el modelo. Con originales de WhatsApp (≤1280 px)
# esto deja fuera la variante 2400.
MAX_REAL = 2.0

# ---------------------------------------------------------------------------
# Ajustes manuales por foto, decididos revisando cada imagen.
#   crop: (izq, arriba, der, abajo) en fracciones a recortar de cada borde
#   persp: True/False fuerza o desactiva el enderezado automático de verticales
#   wb: False desactiva el balance de blancos automático
#   nota: comentario que va al reporte
#   decision: override de la recomendación automática
# ---------------------------------------------------------------------------
MANUAL: dict[str, dict] = {}
MANUAL_PATH = ROOT / "tools" / "fotos-ajustes.json"
if MANUAL_PATH.exists():
    MANUAL = json.loads(MANUAL_PATH.read_text(encoding="utf-8"))

PERSP_CATS = {"cocina", "placard", "bano", "oficina", "locker"}


# ============================== utilidades ==================================
def log(*a):
    print(*a, flush=True)


def load_rgb(path: Path) -> np.ndarray:
    im = Image.open(path)
    im = ImageOps.exif_transpose(im).convert("RGB")
    return np.asarray(im)


def lap_var(rgb: np.ndarray) -> float:
    """Nitidez: varianza del Laplaciano sobre la imagen normalizada a 1024 px."""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    s = 1024 / max(g.shape)
    if s < 1:
        g = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    return float(cv2.Laplacian(g, cv2.CV_64F).var())


STD_LUMA = np.array([
    16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55,
    14, 13, 16, 24, 40, 57, 69, 56, 14, 17, 22, 29, 51, 87, 80, 62,
    18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
    49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99], float)


def jpeg_quality(path: Path) -> int | None:
    try:
        q = Image.open(path).quantization
    except Exception:
        return None
    if not q:
        return None
    t = np.array(q[0], float)
    s = float(np.mean(t / STD_LUMA) * 100)
    qual = (200 - s) / 2 if s <= 100 else 5000 / s
    return int(round(max(1, min(100, qual))))


def blockiness(rgb: np.ndarray) -> float:
    """Relación entre el salto de gradiente en bordes de bloque 8x8 y dentro del bloque."""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY).astype(np.float32)
    dx = np.abs(np.diff(g, axis=1))
    cols = np.arange(dx.shape[1])
    edge = dx[:, (cols % 8) == 7].mean()
    inner = dx[:, (cols % 8) != 7].mean()
    return float(edge / max(inner, 1e-6))


# ============================ super-resolución ==============================
_MODELS: dict[int, object] = {}


def get_model(scale: int):
    if scale in _MODELS:
        return _MODELS[scale]
    import torch
    import torch.nn as nn
    import torch.nn.functional as F

    class RDB(nn.Module):
        def __init__(self, nf=64, gc=32):
            super().__init__()
            self.conv1 = nn.Conv2d(nf, gc, 3, 1, 1)
            self.conv2 = nn.Conv2d(nf + gc, gc, 3, 1, 1)
            self.conv3 = nn.Conv2d(nf + 2 * gc, gc, 3, 1, 1)
            self.conv4 = nn.Conv2d(nf + 3 * gc, gc, 3, 1, 1)
            self.conv5 = nn.Conv2d(nf + 4 * gc, nf, 3, 1, 1)
            self.lrelu = nn.LeakyReLU(0.2, True)

        def forward(self, x):
            x1 = self.lrelu(self.conv1(x))
            x2 = self.lrelu(self.conv2(torch.cat((x, x1), 1)))
            x3 = self.lrelu(self.conv3(torch.cat((x, x1, x2), 1)))
            x4 = self.lrelu(self.conv4(torch.cat((x, x1, x2, x3), 1)))
            x5 = self.conv5(torch.cat((x, x1, x2, x3, x4), 1))
            return x5 * 0.2 + x

    class RRDB(nn.Module):
        def __init__(self, nf, gc):
            super().__init__()
            self.rdb1, self.rdb2, self.rdb3 = RDB(nf, gc), RDB(nf, gc), RDB(nf, gc)

        def forward(self, x):
            return self.rdb3(self.rdb2(self.rdb1(x))) * 0.2 + x

    class RRDBNet(nn.Module):
        """Arquitectura de Real-ESRGAN (basicsr), compatible con los pesos oficiales."""
        def __init__(self, scale, nf=64, nb=23, gc=32):
            super().__init__()
            self.scale = scale
            cin = 3 * (4 if scale == 2 else 1)
            self.conv_first = nn.Conv2d(cin, nf, 3, 1, 1)
            self.body = nn.Sequential(*[RRDB(nf, gc) for _ in range(nb)])
            self.conv_body = nn.Conv2d(nf, nf, 3, 1, 1)
            self.conv_up1 = nn.Conv2d(nf, nf, 3, 1, 1)
            self.conv_up2 = nn.Conv2d(nf, nf, 3, 1, 1)
            self.conv_hr = nn.Conv2d(nf, nf, 3, 1, 1)
            self.conv_last = nn.Conv2d(nf, 3, 3, 1, 1)
            self.lrelu = nn.LeakyReLU(0.2, True)

        def forward(self, x):
            feat = F.pixel_unshuffle(x, 2) if self.scale == 2 else x
            feat = self.conv_first(feat)
            feat = feat + self.conv_body(self.body(feat))
            feat = self.lrelu(self.conv_up1(F.interpolate(feat, scale_factor=2, mode="nearest")))
            feat = self.lrelu(self.conv_up2(F.interpolate(feat, scale_factor=2, mode="nearest")))
            return self.conv_last(self.lrelu(self.conv_hr(feat)))

    w = SR_DIR / f"RealESRGAN_x{scale}plus.pth"
    if not w.exists():
        sys.exit(f"Faltan pesos {w}. Corré tools/hd.sh para descargarlos.")
    net = RRDBNet(scale)
    sd = torch.load(w, map_location="cpu", weights_only=True)
    net.load_state_dict(sd.get("params_ema", sd.get("params", sd)), strict=True)
    net.eval()
    torch.set_num_threads(os.cpu_count() or 4)
    _MODELS[scale] = net
    return net


def super_res(rgb: np.ndarray, scale: int, tile=320, pad=16) -> np.ndarray:
    import torch
    net = get_model(scale)
    h, w = rgb.shape[:2]
    x = torch.from_numpy(rgb.astype(np.float32) / 255).permute(2, 0, 1)[None]
    out = torch.zeros(1, 3, h * scale, w * scale)
    with torch.inference_mode():
        for y0 in range(0, h, tile):
            for x0 in range(0, w, tile):
                y1, x1 = min(y0 + tile, h), min(x0 + tile, w)
                ya, xa = max(y0 - pad, 0), max(x0 - pad, 0)
                yb, xb = min(y1 + pad, h), min(x1 + pad, w)
                patch = x[:, :, ya:yb, xa:xb]
                ph, pw = patch.shape[2:]
                # x2plus necesita dimensiones pares
                eh, ew = ph % 2, pw % 2
                if eh or ew:
                    patch = torch.nn.functional.pad(patch, (0, ew, 0, eh), mode="reflect")
                o = net(patch)[:, :, : ph * scale, : pw * scale]
                oy, ox = (y0 - ya) * scale, (x0 - xa) * scale
                out[:, :, y0 * scale:y1 * scale, x0 * scale:x1 * scale] = \
                    o[:, :, oy:oy + (y1 - y0) * scale, ox:ox + (x1 - x0) * scale]
    o = out[0].clamp(0, 1).permute(1, 2, 0).numpy()
    return (o * 255 + 0.5).astype(np.uint8)


def upscale(rgb: np.ndarray, ident: str, force: bool) -> tuple[np.ndarray, int]:
    """Devuelve la imagen restaurada y agrandada (x2, o x4 si es muy chica)."""
    h, w = rgb.shape[:2]
    small = max(h, w) < 1000 or w < 640
    scale = 4 if small else 2
    CACHE.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha1(rgb.tobytes()).hexdigest()[:10]
    cp = CACHE / f"{ident}-x{scale}-{digest}.png"
    if cp.exists() and not force:
        sr = np.asarray(Image.open(cp).convert("RGB"))
    else:
        log(f"  · Real-ESRGAN x{scale} ({w}x{h}) …")
        sr = super_res(rgb, scale)
        Image.fromarray(sr).save(cp, compress_level=1)
    # Re-inyectar un poco de la textura original (evita el aspecto "plástico"
    # del modelo sobre la veta de la madera y las superficies lisas).
    bic = cv2.resize(rgb, (sr.shape[1], sr.shape[0]), interpolation=cv2.INTER_CUBIC)
    beta = MANUAL.get(ident, {}).get("textura", 0.3)
    mixed = cv2.addWeighted(sr, 1 - beta, bic, beta, 0)
    # x4 → nos quedamos con el doble del original como máximo "creíble" (x2.2 si es muy chica)
    target = min(scale, MAX_REAL if not small else 2.25)
    if target < scale:
        mixed = cv2.resize(mixed, (round(w * target), round(h * target)), interpolation=cv2.INTER_AREA)
    return mixed, scale


# ================================ geometría =================================
def vertical_fit(rgb: np.ndarray):
    """Ajusta tanθ = a + b·x (x normalizada) sobre líneas casi verticales."""
    g = cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY)
    s = 1200 / max(g.shape)
    g = cv2.resize(g, None, fx=s, fy=s, interpolation=cv2.INTER_AREA)
    H, W = g.shape
    e = cv2.Canny(cv2.GaussianBlur(g, (5, 5), 0), 50, 140)
    lines = cv2.HoughLinesP(e, 1, np.pi / 720, 80, minLineLength=H * 0.18, maxLineGap=8)
    if lines is None:
        return None
    xs, ts, ws = [], [], []
    for x1, y1, x2, y2 in lines.reshape(-1, 4).astype(float):  # OpenCV 4: (N,1,4); OpenCV 5: (N,4)
        if y1 < y2:
            x1, y1, x2, y2 = x2, y2, x1, y1
        dy = y1 - y2
        if dy <= 0:
            continue
        t = (x2 - x1) / dy
        if abs(t) > math.tan(math.radians(12)):
            continue
        xs.append(((x1 + x2) / 2 - W / 2) / (W / 2))
        ts.append(t)
        ws.append(math.hypot(x2 - x1, dy))
    if len(ts) < 6:
        return None
    xs, ts, ws = map(np.array, (xs, ts, ws))
    keep = np.ones(len(ts), bool)
    for _ in range(3):  # ajuste robusto: descarta líneas que no son verticales reales (diagonales, reflejos)
        A = np.stack([np.ones_like(xs[keep]), xs[keep]], 1) * ws[keep, None]
        (a, b), *_ = np.linalg.lstsq(A, ts[keep] * ws[keep], rcond=None)
        r = np.abs(ts - (a + b * xs))
        thr = max(2.5 * np.median(r[keep]), 0.01)
        new = r < thr
        if new.sum() < 6 or (new == keep).all():
            break
        keep = new
    resid = np.sqrt(np.average((ts[keep] - (a + b * xs[keep])) ** 2, weights=ws[keep]))
    return dict(a=float(a), b=float(b), n=int(keep.sum()), resid=float(resid), H=H, W=W)


def largest_valid_rect(mask: np.ndarray) -> tuple[int, int, int, int]:
    """Achica el rectángulo hasta que no queden bordes vacíos (recorte, no relleno)."""
    h, w = mask.shape
    x0, y0, x1, y1 = 0, 0, w, h
    for _ in range(4000):
        sub = mask[y0:y1, x0:x1]
        bad = [(sub[:, 0] == 0).sum() / sub.shape[0], (sub[0, :] == 0).sum() / sub.shape[1],
               (sub[:, -1] == 0).sum() / sub.shape[0], (sub[-1, :] == 0).sum() / sub.shape[1]]
        if max(bad) == 0:
            break
        i = int(np.argmax(bad))
        step = max(1, round(min(w, h) * 0.002))
        if i == 0: x0 += step
        elif i == 1: y0 += step
        elif i == 2: x1 -= step
        else: y1 -= step
    return x0, y0, x1, y1


def straighten(rgb: np.ndarray, ident: str, cat: str) -> tuple[np.ndarray, str]:
    cfg = MANUAL.get(ident, {})
    enabled = cfg.get("persp", cat in PERSP_CATS)
    if not enabled:
        return rgb, "sin enderezar"
    fit = vertical_fit(rgb)
    if not fit or fit["resid"] > 0.035 or fit["n"] < 6:
        return rgb, "sin líneas fiables"
    h, w = rgb.shape[:2]
    a = fit["a"]
    b = fit["b"] * cfg.get("persp_fuerza", 0.8)
    rot = math.degrees(math.atan(a))
    # Converge de arriba: el ancho efectivo arriba vs abajo
    r = 1 + 2 * b * fit["H"] / fit["W"]
    if abs(rot) < 0.25 and abs(1 - r) < 0.008:
        return rgb, "ya derecha"
    # Corrección parcial y acotada: enderezar del todo una foto muy picada deforma el mueble
    lim_r, lim_a = 0.08, math.tan(math.radians(4))
    nota_lim = ""
    if abs(1 - r) > lim_r or abs(a) > lim_a:
        nota_lim = " (acotada)"
    r = 1 + float(np.clip(r - 1, -lim_r, lim_r))
    a = float(np.clip(a, -lim_a, lim_a))
    rot = math.degrees(math.atan(a))
    # Homografía = rotación + keystone vertical
    cx = w / 2
    src = np.float32([[cx - w / 2 * r, 0], [cx + w / 2 * r, 0], [w, h], [0, h]])
    # aplicar la inclinación global (a) como corrimiento horizontal de la fila superior
    src[0][0] += a * h
    src[1][0] += a * h
    dst = np.float32([[0, 0], [w, 0], [w, h], [0, h]])
    M = cv2.getPerspectiveTransform(src, dst)
    out = cv2.warpPerspective(rgb, M, (w, h), flags=cv2.INTER_CUBIC, borderValue=0)
    mask = cv2.warpPerspective(np.full((h, w), 255, np.uint8), M, (w, h), flags=cv2.INTER_NEAREST)
    x0, y0, x1, y1 = largest_valid_rect(cv2.erode(mask, np.ones((5, 5), np.uint8)))
    return out[y0:y1, x0:x1], f"rot {rot:+.1f}°, verticales k={r:.3f}{nota_lim}"


def manual_crop(rgb: np.ndarray, ident: str) -> np.ndarray:
    c = MANUAL.get(ident, {}).get("crop")
    if not c:
        return rgb
    h, w = rgb.shape[:2]
    l, t, r_, b = c
    return rgb[round(t * h):h - round(b * h), round(l * w):w - round(r_ * w)]


# ================================== color ===================================
def color_correct(rgb: np.ndarray, ident: str) -> tuple[np.ndarray, str]:
    cfg = MANUAL.get(ident, {})
    f = rgb.astype(np.float32) / 255
    notes = []
    # 1) Balance de blancos: tomar sólo píxeles claros y poco saturados
    #    (paredes, cielorrasos, melamina blanca) y llevarlos a neutro.
    if cfg.get("wb", True):
        hsv = cv2.cvtColor(rgb, cv2.COLOR_RGB2HSV)
        lum = f.mean(2)
        sel = (hsv[..., 1] < 50) & (lum > np.percentile(lum, 55)) & (lum < 0.97)
        if sel.mean() > 0.03:
            m = f[sel].mean(0)
            gains = m.mean() / np.maximum(m, 1e-4)
            gains = np.clip(1 + (gains - 1) * cfg.get("wb_fuerza", 0.85), 0.88, 1.12)
            f = np.clip(f * gains, 0, 1)
            notes.append("WB " + "/".join(f"{g:.2f}" for g in gains))
    # 2) Exposición en L* (LAB): niveles suaves + levantar sombras + domar altas luces
    lab = cv2.cvtColor(f, cv2.COLOR_RGB2LAB)
    L = lab[..., 0] / 100
    lo, hi = np.percentile(L, 0.4), np.percentile(L, 99.6)
    lo = min(lo, 0.06)
    hi = max(hi, 0.90)
    L = np.clip((L - lo) / (hi - lo), 0, 1)
    mean = float(L.mean())
    target = cfg.get("brillo", 0.56)
    if mean < target - 0.02:
        g = math.log(target) / math.log(max(mean, 0.05))
        g = max(g, cfg.get("gamma_min", 0.80))   # tope a la aclarada (más bajo = aclara más)
        L = L ** g
        notes.append(f"gamma {g:.2f}")
    sh = cfg.get("sombras", 0.08)
    L = L + sh * (1 - L) * np.exp(-((L / 0.28) ** 2)) * L * 4   # levanta sombras sin lavar negros
    # Altas luces: sólo se comprime lo que está casi quemado (ventanas, luminarias);
    # las paredes blancas tienen que seguir viéndose blancas.
    knee = 0.95
    over = L > knee
    L[over] = knee + (1 - knee) * np.tanh((L[over] - knee) / (1 - knee))
    # Contraste local muy suave, sólo en medios tonos (no grisea blancos ni levanta negros)
    L8 = np.clip(L * 255, 0, 255).astype(np.uint8)
    clahe = cv2.createCLAHE(clipLimit=1.2, tileGridSize=(8, 8))
    Lc = clahe.apply(L8).astype(np.float32) / 255
    wmid = 0.2 * np.clip(1 - np.abs(L - 0.5) / 0.4, 0, 1)
    L = (1 - wmid) * L + wmid * Lc
    lab[..., 0] = np.clip(L, 0, 1) * 100
    # 3) Saturación moderada (vibrance: más en lo poco saturado)
    sat = cfg.get("saturacion", 1.06)
    c = np.sqrt(lab[..., 1] ** 2 + lab[..., 2] ** 2)
    k = 1 + (sat - 1) * np.clip(1 - c / 60, 0, 1)
    lab[..., 1] *= k
    lab[..., 2] *= k
    out = np.clip(cv2.cvtColor(lab, cv2.COLOR_LAB2RGB), 0, 1)
    return (out * 255 + 0.5).astype(np.uint8), ", ".join(notes)


def sharpen(rgb: np.ndarray, amount=0.45, radius=1.0, thresh=3) -> np.ndarray:
    """Unsharp mask moderado con umbral (no realza ruido) y sin halos fuertes."""
    f = rgb.astype(np.float32)
    blur = cv2.GaussianBlur(f, (0, 0), radius)
    d = f - blur
    d[np.abs(d) < thresh] = 0
    d = np.clip(d, -18, 18)   # limita halos
    return np.clip(f + amount * d, 0, 255).astype(np.uint8)


# ================================= export ===================================
def encode(im: Image.Image, fmt: str, q: int) -> bytes:
    b = io.BytesIO()
    if fmt == "avif":
        im.save(b, "AVIF", quality=q, speed=4)
    elif fmt == "webp":
        im.save(b, "WEBP", quality=q, method=6)
    else:
        im.save(b, "JPEG", quality=q, optimize=True, progressive=True)
    return b.getvalue()


Q = {"avif": (58, 40), "webp": (80, 60), "jpg": (84, 70)}


def export(rgb: np.ndarray, ident: str) -> dict:
    h, w = rgb.shape[:2]
    widths = [x for x in WIDTHS if x <= w]
    if not widths or widths[-1] < w and w - widths[-1] > 200 and w < 1600:
        widths.append(w)
    # nunca la variante 2400 salvo que el original lo justifique
    orig_w = MANUAL.get(ident, {}).get("_orig_w", 0)
    widths = [x for x in widths if x <= max(1600, orig_w * 1.25)]
    files = {}
    base = Image.fromarray(rgb)
    for tw in widths:
        th = round(h * tw / w)
        im = base.resize((tw, th), Image.LANCZOS) if tw != w else base
        im = Image.fromarray(sharpen(np.asarray(im), amount=0.35 if tw >= 1600 else 0.25))
        for fmt in ("avif", "webp", "jpg"):
            q, qmin = Q[fmt]
            data = encode(im, fmt, q)
            if tw >= 1600:
                limit = MAX_KB_1600 * 1024 * (1.6 if fmt == "jpg" else 1)
                while len(data) > limit and q > qmin:
                    q -= 4
                    data = encode(im, fmt, q)
            p = IMG / f"{ident}-{tw}.{fmt}"
            p.write_bytes(data)
            files[f"{tw}.{fmt}"] = len(data)
    # JPG "canónico" (OG, sitemap, fallback sin srcset): la variante más grande ≤1600
    big = max(x for x in widths if x <= 1600)
    shutil.copyfile(IMG / f"{ident}-{big}.jpg", IMG / f"{ident}.jpg")
    return dict(w=w, h=h, widths=widths, bytes=files)


# ============================== QC / reportes ===============================
def font(size):
    for p in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def before_after(orig: np.ndarray, final: np.ndarray, ident: str):
    QC.mkdir(parents=True, exist_ok=True)
    H = 900
    a = Image.fromarray(orig); b = Image.fromarray(final)
    a = a.resize((round(a.width * H / a.height), H), Image.LANCZOS)
    b = b.resize((round(b.width * H / b.height), H), Image.LANCZOS)
    # detalle: mismo recorte relativo (centro, 22% del lado), ampliado
    def detail(img: np.ndarray, size=H // 2):
        h, w = img.shape[:2]
        s = int(min(h, w) * 0.22)
        y, x = h // 2 - s // 2, w // 2 - s // 2
        return Image.fromarray(img[y:y + s, x:x + s]).resize((size, size), Image.LANCZOS)
    da, db = detail(orig), detail(final)
    W = a.width + b.width + 30
    sheet = Image.new("RGB", (W, H + H // 2 + 90), (24, 26, 27))
    sheet.paste(a, (0, 40)); sheet.paste(b, (a.width + 30, 40))
    sheet.paste(da, (0, H + 70)); sheet.paste(db, (a.width + 30, H + 70))
    d = ImageDraw.Draw(sheet); f = font(22)
    d.text((8, 8), f"{ident} · ORIGINAL {orig.shape[1]}x{orig.shape[0]}", fill="white", font=f)
    d.text((a.width + 38, 8), f"MEJORADA {final.shape[1]}x{final.shape[0]}", fill="white", font=f)
    d.text((8, H + 46), "detalle (centro, ampliado)", fill=(180, 180, 180), font=font(18))
    sheet.save(QC / f"{ident}.jpg", quality=82)


def contact_sheet(ids: list[str]):
    T, cols = 360, 6
    rows = math.ceil(len(ids) / cols)
    sheet = Image.new("RGB", (cols * T, rows * (T + 28)), (24, 26, 27))
    d = ImageDraw.Draw(sheet); f = font(16)
    for i, ident in enumerate(ids):
        im = Image.open(IMG / f"{ident}-640.jpg"); im.thumbnail((T - 8, T - 8))
        x, y = (i % cols) * T, (i // cols) * (T + 28)
        sheet.paste(im, (x + (T - im.width) // 2, y + 4))
        d.text((x + 6, y + T + 4), ident, fill="white", font=f)
    QC.mkdir(parents=True, exist_ok=True)
    sheet.save(QC / "_hoja-de-contactos.jpg", quality=82)


def recommend(d: dict) -> str:
    m = MANUAL.get(d["id"], {})
    if m.get("decision"):
        return m["decision"]
    if d["score"] >= 0.70:
        return "usar"
    if d["score"] >= 0.38:
        return "mejorar"
    return "pedir original"   # se publica la versión mejorada, pero conviene reemplazarla


def write_report(rows: list[dict], engine: str):
    rows = sorted(rows, key=lambda r: -r["score"])
    out = ["# Reporte de fotos — Cainco", "",
           "Generado por `tools/mejorar_fotos.py`. Ordenado de mejor a peor según el diagnóstico del original.", "",
           f"**Super-resolución usada:** {engine}", "",
           "- **Nitidez**: varianza del Laplaciano con la imagen normalizada a 1024 px (más alto = más nítida; <100 es blanda).",
           "- **Q JPEG**: calidad estimada a partir de la tabla de cuantización.",
           "- **Bloques**: salto de gradiente en bordes 8×8 vs. interior (1.0 = sin artefactos; >1.15 = bloques visibles).",
           "- **Recomprimida**: resolución típica de WhatsApp (lado mayor ≤1280/1600) y/o Q ≤ 85.", "",
           "| # | Foto | Original | KB | Q JPEG | Bloques | Nitidez orig → final | Recompr. | Puntaje | Recomendación | Final | Notas |",
           "|---|---|---|---|---|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        notes = "; ".join(x for x in [r.get("nota", ""), r.get("geo", ""), r.get("color", "")] if x)
        fin = f'{r["fw"]}×{r["fh"]}' if r.get("fw") else "—"
        lf = f'{r["lap"]:.0f} → {r["lap_final"]:.0f}' if r.get("lap_final") else f'{r["lap"]:.0f}'
        out.append(f'| {i} | `{r["id"]}` | {r["w"]}×{r["h"]} | {r["kb"]} | {r["q"] or "?"} | {r["block"]:.2f} | {lf} | '
                   f'{"sí" if r["recomp"] else "no"} | {r["score"]:.2f} | **{r["rec"]}** | {fin} | {notes} |')
    pedir = [r["id"] for r in rows if r["rec"] in ("pedir original", "descartar")]
    out += ["", "## Para pedir a Cainco", "",
            "Fotos que conviene reemplazar (original sin comprimir o foto nueva):", ""]
    out += [f"- `{p}` — {MANUAL.get(p, {}).get('nota', 'baja calidad de origen')}" for p in pedir] or ["- (ninguna)"]
    REPORT.write_text("\n".join(out) + "\n", encoding="utf-8")


# =================================== main ===================================
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ids", nargs="*")
    ap.add_argument("--solo-diagnostico", action="store_true")
    ap.add_argument("--forzar", action="store_true")
    args = ap.parse_args()

    ORIG.mkdir(parents=True, exist_ok=True)
    # 0) Resguardar originales (una sola vez; jamás se sobrescriben)
    for p in sorted(IMG.glob("*.jpg")):
        if "-" in p.stem and p.stem.rsplit("-", 1)[1].isdigit() and len(p.stem.rsplit("-", 1)[1]) == 2:
            dst = ORIG / p.name
            if not dst.exists():
                shutil.copy2(p, dst)
                log(f"original resguardado: {dst.relative_to(ROOT)}")

    ids = sorted(p.stem for p in ORIG.glob("*.jpg"))
    if args.ids:
        ids = [i for i in ids if i in args.ids]

    # 1) Diagnóstico
    rows = []
    for ident in ids:
        p = ORIG / f"{ident}.jpg"
        rgb = load_rgb(p)
        h, w = rgb.shape[:2]
        q = jpeg_quality(p)
        d = dict(id=ident, w=w, h=h, long=max(w, h), kb=round(p.stat().st_size / 1024), q=q,
                 lap=lap_var(rgb), block=blockiness(rgb))
        d["recomp"] = max(w, h) <= 1600 and (q is None or q <= 85 or max(w, h) in (1280, 1600))
        # Escalas calibradas con fotos reenviadas por WhatsApp (Q≈78, ≤1280 px):
        # nitidez 20 (muy blanda) … 500 (nítida); bloques 2.3 (muy visibles) … 1.2 (leves)
        n_lap = np.clip((math.log10(max(d["lap"], 1)) - 1.3) / (2.7 - 1.3), 0, 1)
        n_res = np.clip((w * h / 1e6 - 0.4) / (1.3 - 0.4), 0, 1)
        n_blk = np.clip((2.3 - d["block"]) / (2.3 - 1.2), 0, 1)
        d["score"] = float(0.55 * n_lap + 0.25 * n_res + 0.20 * n_blk)
        d["nota"] = MANUAL.get(ident, {}).get("nota", "")
        d["rec"] = recommend(d)
        MANUAL.setdefault(ident, {})["_orig_w"] = w
        rows.append(d)
        log(f"{ident:14s} {w}x{h} {d['kb']:4d}KB q≈{q} lap={d['lap']:.0f} blk={d['block']:.2f} → {d['rec']}")

    engine = "Real-ESRGAN x4plus / x2plus (PyTorch, CPU), mezclado 70/30 con bicúbica para conservar textura"
    if args.solo_diagnostico:
        write_report(rows, engine)
        return

    # 2–6) Mejora + export
    manifest = json.loads(MANIFEST.read_text()) if MANIFEST.exists() and args.ids else {}
    for d in rows:
        ident, cat = d["id"], d["id"].split("-")[0]
        if d["rec"] == "descartar":
            log(f"{ident}: descartada, no se exporta")
            manifest.pop(ident, None)
            continue
        log(f"{ident}:")
        orig = load_rgb(ORIG / f"{ident}.jpg")
        up, sc = upscale(orig, ident, args.forzar)
        geo_img, geo = straighten(up, ident, cat)
        geo_img = manual_crop(geo_img, ident)
        col, cnote = color_correct(geo_img, ident)
        info = export(col, ident)
        d.update(fw=info["w"], fh=info["h"], geo=geo, color=cnote, lap_final=lap_var(col))
        before_after(orig, col, ident)
        manifest[ident] = dict(w=info["w"], h=info["h"], widths=info["widths"], rec=d["rec"],
                               score=round(d["score"], 3))
        log(f"  → {info['w']}x{info['h']} {geo} | {cnote} | 1600: "
            + ", ".join(f"{k}={v // 1024}KB" for k, v in info["bytes"].items() if k.startswith("1600")))
    # limpiar variantes viejas del esquema anterior (<id>.webp, <id>-640.webp)
    for ident in manifest:
        (IMG / f"{ident}.webp").unlink(missing_ok=True)
    MANIFEST.write_text(json.dumps(manifest, indent=1, ensure_ascii=False) + "\n", encoding="utf-8")
    write_report(rows, engine)
    contact_sheet(sorted(manifest, key=lambda i: -manifest[i]["score"]))
    log("listo.")


if __name__ == "__main__":
    main()
