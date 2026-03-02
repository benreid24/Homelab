#!/bin/bash
set -eu

CONFIG_DIR="${SEAFILE_CLI_CONFIG_DIR:-/config}"
DATA_DIR="${SEAFILE_CLI_DATA_DIR:-/data}"

SEAFILE_CONF_DIR="$CONFIG_DIR/seafile"

# Ensure dirs exist (seafile-data needed by seaf-cli for device ID)
mkdir -p "$CONFIG_DIR" "$DATA_DIR" "$DATA_DIR/seafile-data"

# 1. Init config if missing
# seaf-cli init requires the config dir to not exist, so we use a subdirectory
if [ ! -f "$SEAFILE_CONF_DIR/seafile.ini" ]; then
  echo "[seaf-cli] Initializing config..."
  seaf-cli init -c "$SEAFILE_CONF_DIR" -d "$DATA_DIR"
else
  echo "[seaf-cli] Config already initialized"
fi

# Configure file limit (increase from default ~100k to 2m)
SEAFILE_CONF_FILE="$SEAFILE_CONF_DIR/seafile.conf"
if ! grep -q "max_sync_file_count" "$SEAFILE_CONF_FILE" 2>/dev/null; then
  echo "[seaf-cli] Configuring max_sync_file_count..."
  cat >> "$SEAFILE_CONF_FILE" << EOF

[library]
max_sync_file_count = 2000000
EOF
fi

# 2. Start daemon
echo "[seaf-cli] Starting daemon..."
seaf-cli start -c "$SEAFILE_CONF_DIR"

# Wait for daemon to be ready (socket file + status check)
echo "[seaf-cli] Waiting for daemon..."
for i in {1..60}; do
  if [ -S "$SEAFILE_CONF_DIR/seafile.sock" ] || ls "$SEAFILE_CONF_DIR"/*.sock >/dev/null 2>&1; then
    if seaf-cli status -c "$SEAFILE_CONF_DIR" >/dev/null 2>&1; then
      echo "[seaf-cli] Daemon ready"
      break
    fi
  fi
  if [ "$i" -eq 60 ]; then
    echo "[seaf-cli] WARNING: Daemon may not be ready after 60s"
  fi
  sleep 1
done

# 3. Sync libraries
export SEAFILE_CONF_DIR
python3 /sync_libraries.py

# 4. Keep container alive (daemon runs in background)
echo "[seaf-cli] Sync running"
tail -f "$SEAFILE_CONF_DIR/logs/seafile.log"
