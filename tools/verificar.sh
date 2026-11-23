#!/usr/bin/env bash
# Verificación completa: Playwright (capturas + formulario + teclado), html-validate y Lighthouse móvil.
# Uso: tools/verificar.sh [carpeta-salida]   (por defecto tools/.verificacion, ignorada por git)
set -euo pipefail
REPO="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:-$REPO/tools/.verificacion}"
DIR="${CAINCO_VERIF_DIR:-$HOME/.cache/cainco-verif}"
export NVM_DIR="$HOME/.nvm"; [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" >/dev/null
mkdir -p "$DIR" "$OUT"
cd "$DIR"
[ -f package.json ] || npm init -y >/dev/null
[ -d node_modules/playwright ] || npm i -s playwright@1.56 lighthouse@12 html-validate@9
./node_modules/.bin/playwright install chromium >/dev/null 2>&1 || true
cp "$REPO/tools/verificar.mjs" ./verificar.mjs

# Chromium necesita libnss3/libnspr4/libasound2. Si no están en el sistema y no hay sudo,
# se bajan los .deb y se usan desde una carpeta local.
if ! ldconfig -p | grep -q libnss3.so; then
  LIBS="$DIR/libs/root/usr/lib/x86_64-linux-gnu"
  if [ ! -f "$LIBS/libnss3.so" ]; then
    mkdir -p "$DIR/libs/debs" && (cd "$DIR/libs/debs" && apt-get download libnspr4 libnss3 libasound2t64 >/dev/null && for f in *.deb; do dpkg -x "$f" "$DIR/libs/root"; done)
  fi
  export LD_LIBRARY_PATH="$LIBS${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
  export PLAYWRIGHT_SKIP_VALIDATE_HOST_REQUIREMENTS=1
fi

echo "== html-validate"
cat > htmlvalidate.json <<'EOF'
{"extends":["html-validate:recommended"],
 "rules":{"no-inline-style":"off","long-title":"off","no-trailing-whitespace":"off","attribute-boolean-style":"off","void-style":"off","prefer-native-element":"off"}}
EOF
./node_modules/.bin/html-validate --config htmlvalidate.json "$REPO/index.html" || true

echo "== Playwright"
CAINCO_ROOT="$REPO" node verificar.mjs "$OUT"
