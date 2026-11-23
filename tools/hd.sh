#!/usr/bin/env bash
# Pipeline completo de fotos en un solo comando:
#   diagnóstico → super-resolución → limpieza/color/geometría → variantes AVIF/WebP/JPG → QC
#
# Uso:  tools/hd.sh                 (todas las fotos)
#       tools/hd.sh --ids cocina-01 (solo algunas)
#       tools/hd.sh --solo-diagnostico
#
# Para agregar fotos nuevas: copiá el original a img/_originales/<categoria>-NN.jpg
# (idealmente el archivo original, no el que reenvía WhatsApp) y corré este script.
# Los ajustes manuales por foto (recorte, enderezado, notas) están en tools/fotos-ajustes.json.
set -euo pipefail
cd "$(dirname "$0")/.."

VENV="${CAINCO_VENV:-$HOME/.venvs/cainco-sr}"
SR_DIR="${CAINCO_SR_DIR:-$HOME/.cache/cainco-sr}"

if [ ! -x "$VENV/bin/python" ]; then
  echo "Creando entorno en $VENV (PyTorch CPU + OpenCV)…"
  python3 -m venv "$VENV"
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q torch --index-url https://download.pytorch.org/whl/cpu
  "$VENV/bin/pip" install -q opencv-python-headless "pillow>=11" numpy
fi

mkdir -p "$SR_DIR"
[ -f "$SR_DIR/RealESRGAN_x4plus.pth" ] || curl -fsSLo "$SR_DIR/RealESRGAN_x4plus.pth" \
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.1.0/RealESRGAN_x4plus.pth
[ -f "$SR_DIR/RealESRGAN_x2plus.pth" ] || curl -fsSLo "$SR_DIR/RealESRGAN_x2plus.pth" \
  https://github.com/xinntao/Real-ESRGAN/releases/download/v0.2.1/RealESRGAN_x2plus.pth

CAINCO_SR_DIR="$SR_DIR" "$VENV/bin/python" tools/mejorar_fotos.py "$@"
case " $* " in *" --solo-diagnostico "*) exit 0;; esac
"$VENV/bin/python" tools/actualizar_html.py
