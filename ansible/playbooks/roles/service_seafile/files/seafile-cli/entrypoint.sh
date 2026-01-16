#!/bin/bash
set -eu

CONFIG_DIR="${SEAFILE_CLI_CONFIG_DIR:-/config}"
DATA_DIR="${SEAFILE_CLI_DATA_DIR:-/data}"

LIBRARY_IDS="${SEAFILE_CLI_LIBRARY_IDS:-${SEAFILE_CLI_LIBRARY_ID:-}}"
SERVER_URL="${SEAFILE_CLI_SERVER_URL:-}"
USERNAME="${SEAFILE_CLI_USERNAME:-}"
TOKEN="${SEAFILE_CLI_TOKEN:-}"

# 1. Init config if missing
# seaf-cli init requires the config dir to not exist, so we use a subdirectory
SEAFILE_CONF_DIR="$CONFIG_DIR/seafile"

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

# 2. Start daemon (needed before download)
echo "[seaf-cli] Starting daemon..."
seaf-cli start -c "$SEAFILE_CONF_DIR"

# Wait for daemon to be ready
sleep 3

# 3. Download libraries (idempotent)
if [ -n "$LIBRARY_IDS" ]; then
  # Split comma-separated library IDs
  IFS=',' read -ra LIB_ARRAY <<< "$LIBRARY_IDS"
  
  for LIB_ID in "${LIB_ARRAY[@]}"; do
    # Trim whitespace
    LIB_ID=$(echo "$LIB_ID" | xargs)
    
    if ! seaf-cli list -c "$SEAFILE_CONF_DIR" | grep -q "$LIB_ID"; then
      echo "[seaf-cli] Downloading library $LIB_ID..."
      # Disable exit on error for this command since "Task is already in progress" is non-fatal
      set +e
      seaf-cli download \
        -c "$SEAFILE_CONF_DIR" \
        -l "$LIB_ID" \
        -s "$SERVER_URL" \
        -d "$DATA_DIR" \
        -u "$USERNAME" \
        -T "$TOKEN" 2>&1 | grep -v "Task is already in progress" || true
      set -e
    else
      echo "[seaf-cli] Library $LIB_ID already registered, skipping download"
    fi
  done
fi

# 4. Keep container alive (daemon runs in background)
echo "[seaf-cli] Sync running"
tail -f /dev/null
