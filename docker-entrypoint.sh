#!/bin/sh
# Started as root (e.g. from an Unraid template): make /data writable for PUID:PGID,
# then drop privileges. Started with --user: nothing to do.
set -e
if [ "$(id -u)" = "0" ]; then
  PUID="${PUID:-99}"; PGID="${PGID:-100}"
  umask "${UMASK:-0002}"
  mkdir -p "${ORDNUNG_DATA:-/data}"
  chown -R "$PUID:$PGID" "${ORDNUNG_DATA:-/data}"
  # Folders Docker just created for the archive or an inbox are empty and belong
  # to root: hand them over. Folders with content are never touched.
  for d in "${ORDNUNG_ARCHIVE:-/archiv}" /eingang /eingang/*; do
    if [ -d "$d" ] && [ -z "$(ls -A "$d")" ]; then chown "$PUID:$PGID" "$d"; fi
  done
  exec setpriv --reuid="$PUID" --regid="$PGID" --clear-groups -- "$@"
fi
[ -n "$UMASK" ] && umask "$UMASK"
exec "$@"
