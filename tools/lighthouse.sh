#!/usr/bin/env bash
# Lighthouse móvil (3 corridas, mediana). Usar con la máquina libre: sin el pipeline de fotos corriendo.
# Uso: bash tools/lighthouse.sh [carpeta-salida] [corridas]
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$REPO/tools/.verificacion}"
DIR="${CAINCO_VERIF_DIR:-$HOME/.cache/cainco-verif}"
export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" >/dev/null
[ -d "$DIR/node_modules/lighthouse" ] || { echo "Primero corré tools/verificar.sh (instala Playwright y Lighthouse)"; exit 1; }
if pgrep -f mejorar_fotos.py >/dev/null; then echo "El pipeline de fotos está corriendo: esperá a que termine para medir"; exit 1; fi
LIBS="$DIR/libs/root/usr/lib/x86_64-linux-gnu"
[ -d "$LIBS" ] && export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
cp "$REPO/tools/lighthouse.mjs" "$DIR/lighthouse.mjs"
cd "$DIR"
echo "carga de la máquina: $(cut -d' ' -f1-3 /proc/loadavg)"
CAINCO_ROOT="$REPO" node lighthouse.mjs "$OUT" "${2:-3}"
