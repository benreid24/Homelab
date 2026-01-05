#!/bin/sh
set -eu

CONFIG_DIR="${SEAFILE_CONFIG_DIR:-/config}"
DATA_DIR="${SEAFILE_DATA_DIR:-/data}"

LIB_ID="${SEAFILE_LIBRARY_ID:-}"
SERVER_URL="${SEAFILE_SERVER_URL:-}"
USERNAME="${SEAFILE_USERNAME:-}"
TOKEN="${SEAFILE_TOKEN:-}"

# 1. Init config if missing
# seaf-cli init requires the config dir to not exist, so we use a subdirectory
SEAFILE_CONF_DIR="$CONFIG_DIR/seafile"

if [ ! -f "$SEAFILE_CONF_DIR/seafile.ini" ]; then
  echo "[seaf-cli] Initializing config..."
  seaf-cli init -c "$SEAFILE_CONF_DIR" -d "$DATA_DIR"
else
  echo "[seaf-cli] Config already initialized"
fi

# 2. Start daemon (needed before download)
echo "[seaf-cli] Starting daemon..."
seaf-cli start -c "$SEAFILE_CONF_DIR"

# Wait for daemon to be ready
sleep 3

# 3. Download library ONCE (idempotent)
if [ -n "$LIB_ID" ]; then
  if ! seaf-cli list -c "$SEAFILE_CONF_DIR" | grep -q "$LIB_ID"; then
    echo "[seaf-cli] Downloading library $LIB_ID..."
    seaf-cli download \
      -c "$SEAFILE_CONF_DIR" \
      -l "$LIB_ID" \
      -s "$SERVER_URL" \
      -d "$DATA_DIR" \
      -u "$USERNAME" \
      -T "$TOKEN"
  else
    echo "[seaf-cli] Library already registered, skipping download"
  fi
fi

# 4. Keep container alive (daemon runs in background)
echo "[seaf-cli] Sync running"
tail -f /dev/null
