#!/usr/bin/env bash
# Cartas One Piece — publica los cambios (cartas.json + img/) en GitHub Pages.
# Uso: /workspace/cartas-one-piece/publicar.sh ["mensaje de commit"]
set -euo pipefail
BASE="$(cd "$(dirname "$0")" && pwd)"
MSG="${1:-Actualizar colección $(date '+%Y-%m-%d %H:%M')}"
cd "$BASE"
python3 -c "import json;d=json.load(open('cartas.json'));print('▶ cartas.json OK:', len(d['cartas']), 'cartas distintas')"
git pull -q --ff-only origin main || true
touch .nojekyll
git add -A
if git diff --cached --quiet; then
  echo "✓ Sin cambios: nada que publicar."
  exit 0
fi
git commit -q -m "$MSG"
git push -q origin main
echo "✓ Publicado. Estará en línea en ~1 minuto: https://dacam32-del.github.io/cartas-one-piece/"
