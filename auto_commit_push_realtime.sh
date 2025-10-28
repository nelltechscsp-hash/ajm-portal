#!/bin/bash
# Script para commit y push automático en tiempo real usando inotifywait
# Ubicación sugerida: /opt/odoo/custom_addons/auto_commit_push_realtime.sh

WATCH_DIR="/opt/odoo/custom_addons"
BRANCH="master"
REMOTE="origin"

# Verifica que inotifywait esté instalado
if ! command -v inotifywait &> /dev/null; then
    echo "Falta inotifywait. Instálalo con: sudo apt-get install inotify-tools"
    exit 1
fi

cd "$WATCH_DIR"

echo "[auto_commit_push_realtime] Monitoreando cambios en $WATCH_DIR..."

inotifywait -m -r -e modify,create,delete,move --format '%w%f' . | while read FILE
  do
    # Ignora archivos temporales y de git
    if [[ "$FILE" =~ \.swp$|~$|\.git/|auto_commit_push_realtime\.sh$ ]]; then
      continue
    fi
    git add "$FILE"
    MSG="Auto-commit: cambio en $FILE ($(date '+%Y-%m-%d %H:%M:%S'))"
    git commit -m "$MSG" --allow-empty
    git push $REMOTE $BRANCH
    echo "[auto_commit_push_realtime] Commit y push realizados por cambio en $FILE"
  done
