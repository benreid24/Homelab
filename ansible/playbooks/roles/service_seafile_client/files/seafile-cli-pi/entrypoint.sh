#!/bin/bash
set -eu

CONFIG_DIR="${SEAFILE_CLI_CONFIG_DIR:-/config}"
DATA_DIR="${SEAFILE_CLI_DATA_DIR:-/data}"

LIBRARY_IDS="${SEAFILE_CLI_LIBRARY_IDS:-${SEAFILE_CLI_LIBRARY_ID:-}}"
SERVER_URL="${SEAFILE_CLI_SERVER_URL:-}"
USERNAME="${SEAFILE_CLI_USERNAME:-}"
TOKEN="${SEAFILE_CLI_TOKEN:-}"

SEAFILE_CONF_DIR="$CONFIG_DIR/seafile"

# Ensure dirs exist
mkdir -p "$CONFIG_DIR" "$DATA_DIR" "$DATA_DIR/seafile-data"

# 1. Init config if missing
if [ ! -f "$SEAFILE_CONF_DIR/seafile.ini" ]; then
  echo "[seaf-cli] Initializing config..."
  seaf-cli init -c "$SEAFILE_CONF_DIR" -d "$DATA_DIR"
else
  echo "[seaf-cli] Config already initialized"
fi

# 2. Start daemon FIRST (required for config in v7)
echo "[seaf-cli] Starting daemon..."
seaf-cli start -c "$SEAFILE_CONF_DIR"

# Wait for daemon socket
echo "[seaf-cli] Waiting for daemon socket..."
for i in {1..10}; do
  if [ -S "$SEAFILE_CONF_DIR/seafile.sock" ] || ls "$SEAFILE_CONF_DIR"/*.sock >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

# Configure file limit
SEAFILE_CONF_FILE="$SEAFILE_CONF_DIR/seafile.conf"
if ! grep -q "max_sync_file_count" "$SEAFILE_CONF_FILE" 2>/dev/null; then
  echo "[seaf-cli] Configuring max_sync_file_count..."
  cat >> "$SEAFILE_CONF_FILE" << EOF

[library]
max_sync_file_count = 2000000
EOF
fi

# 4. Download libraries
if [ -n "$LIBRARY_IDS" ]; then
  # Check if daemon logs show server resolution errors (indicates wrong URL)
  if [ -f "$SEAFILE_CONF_DIR/logs/seafile.log" ]; then
    if grep -q "Couldn't resolve host name" "$SEAFILE_CONF_DIR/logs/seafile.log" || \
       grep -q "Cannot resolve server address" "$SEAFILE_CONF_DIR/logs/seafile.log"; then
      echo "[seaf-cli] Detected server resolution errors in logs, desyncing all libraries..."
      # Desync each library folder in the data directory
      for lib_folder in "$DATA_DIR"/*/ ; do
        if [ -d "$lib_folder" ]; then
          echo "[seaf-cli] Desyncing ${lib_folder}..."
          seaf-cli desync -c "$SEAFILE_CONF_DIR" -d "${lib_folder%/}" || true
        fi
      done
      # Clear the log to prevent re-triggering on next restart
      > "$SEAFILE_CONF_DIR/logs/seafile.log"
    fi
  fi
  
  IFS=',' read -ra LIB_ARRAY <<< "$LIBRARY_IDS"

  for LIB_ID in "${LIB_ARRAY[@]}"; do
    LIB_ID=$(echo "$LIB_ID" | xargs)

    if ! seaf-cli list -c "$SEAFILE_CONF_DIR" | grep -q "$LIB_ID"; then
      echo "[seaf-cli] Downloading library $LIB_ID..."
      set +e
      seaf-cli download \
        -c "$SEAFILE_CONF_DIR" \
        -l "$LIB_ID" \
        -s "$SERVER_URL" \
        -d "$DATA_DIR" \
        -u "$USERNAME" \
        -p "$TOKEN" 2>&1 | grep -v "Task is already in progress" || true
      set -e
    else
      echo "[seaf-cli] Library $LIB_ID already registered, skipping download"
    fi
  done
fi

# 5. Keep container alive
echo "[seaf-cli] Sync running"
tail -f /dev/null
