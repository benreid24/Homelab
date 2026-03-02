#!/usr/bin/env python3
"""Sync Seafile libraries using seaf-cli sync with library names from the API.

Authentication is always handled by this script using system Python to obtain
an API token, because seaf-cli's bundled/system Python has compatibility issues
with some servers. Remote library listing is done via direct API calls.
For seaf-cli sync, -T (token) is used on AppImage builds, -p (password) on pi.
"""

import json
import os
import sqlite3
import subprocess
import sys
import urllib.request
import urllib.parse
import urllib.error


def get_api_token(server_url, username, password):
    """Obtain an API token from the Seafile server using system Python."""
    data = urllib.parse.urlencode({
        "username": username,
        "password": password,
    }).encode("utf-8")
    url = f"{server_url}/api2/auth-token/"
    try:
        resp = urllib.request.urlopen(urllib.request.Request(url, data=data))
        return json.loads(resp.read().decode())["token"]
    except urllib.error.HTTPError as e:
        print(f"[sync] Auth failed ({e.code}): {e.read().decode()}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"[sync] Auth error: {e}", file=sys.stderr)
        return None


def get_remote_libraries(server_url, token):
    """Fetch remote libraries via the Seafile API and return a dict of {id: name}."""
    url = f"{server_url}/api2/repos/"
    headers = {"Authorization": f"Token {token}"}
    try:
        req = urllib.request.Request(url, headers=headers)
        resp = urllib.request.urlopen(req)
        repos = json.loads(resp.read().decode())
        return {repo["id"]: repo["name"] for repo in repos}
    except Exception as e:
        print(f"[sync] Failed to fetch remote libraries: {e}", file=sys.stderr)
        return {}


PATCHED_SEAF_CLI = "/tmp/seaf-cli-patched"


def patch_seaf_cli():
    """Create a patched copy of seaf-cli that reads auth token from env var.

    The pi's seaf-cli uses Python 3.9 urllib which gets 400 errors from the
    server's auth endpoint. This patches get_token to return a pre-fetched
    token from the SEAF_PREFETCHED_TOKEN env var instead.
    """
    seaf_cli_path = "/usr/bin/seaf-cli"
    with open(seaf_cli_path, "r") as f:
        source = f.read()

    # Inject a token override at the very start of get_token
    old = "def get_token(url, username, password, tfa, conf_dir):"
    new = (
        "def get_token(url, username, password, tfa, conf_dir):\n"
        "    _env_token = __import__('os').environ.get('SEAF_PREFETCHED_TOKEN')\n"
        "    if _env_token:\n"
        "        return _env_token"
    )
    if old not in source:
        print("[sync] Warning: could not patch seaf-cli, get_token signature not found",
              file=sys.stderr)
        return False

    patched = source.replace(old, new, 1)
    with open(PATCHED_SEAF_CLI, "w") as f:
        f.write(patched)
    os.chmod(PATCHED_SEAF_CLI, 0o755)
    print("[sync] Patched seaf-cli to use pre-fetched token")
    return True


def run(cmd, check=True):
    """Run a shell command and return stdout."""
    result = subprocess.run(cmd, capture_output=True, text=True)
    if check and result.returncode != 0:
        print(f"[sync] Command failed: {' '.join(cmd)}", file=sys.stderr)
        print(f"[sync] stderr: {result.stderr.strip()}", file=sys.stderr)
        return None
    return result.stdout.strip()


def get_synced_libraries(conf_dir):
    """Return set of library IDs currently synced."""
    # Try --json first
    output = run(["seaf-cli", "list", "-c", conf_dir, "--json"], check=False)
    if output:
        try:
            libraries = json.loads(output)
            return {lib["id"] for lib in libraries}
        except (json.JSONDecodeError, KeyError):
            pass

    # Fall back to plain text
    output = run(["seaf-cli", "list", "-c", conf_dir], check=False)
    if not output:
        return set()
    ids = set()
    for line in output.splitlines():
        # Look for UUID-shaped strings (36 chars with hyphens)
        for part in line.split():
            if len(part) == 36 and part.count("-") == 4:
                ids.add(part)
    return ids


def desync_bad_libraries(conf_dir, data_dir, log_path):
    """Desync libraries if the daemon log shows server resolution errors."""
    if not os.path.exists(log_path):
        return

    with open(log_path, "r") as f:
        log_content = f.read()

    error_markers = ["Couldn't resolve host name", "Cannot resolve server address"]
    if not any(marker in log_content for marker in error_markers):
        return

    print("[sync] Detected server resolution errors in logs, desyncing libraries...")
    for entry in os.listdir(data_dir):
        folder = os.path.join(data_dir, entry)
        if os.path.isdir(folder):
            print(f"[sync] Desyncing {folder}...")
            run(["seaf-cli", "desync", "-c", conf_dir, "-d", folder], check=False)

    # Clear the log to prevent re-triggering
    open(log_path, "w").close()


def set_libraries_readonly(conf_dir, data_dir, library_ids):
    """Mark libraries as read-only in the daemon's SQLite DB.

    This prevents the daemon from scanning for local changes and trying
    to commit/upload them, which fails with read-only server permissions.
    """
    # repo.db lives in the seafile-data directory under the data dir
    db_path = os.path.join(data_dir, "seafile-data", "repo.db")
    if not os.path.exists(db_path):
        print(f"[sync] Warning: {db_path} not found, can't set read-only", file=sys.stderr)
        return

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        for lib_id in library_ids:
            # Check if the repo exists in the RepoProperty table
            cursor.execute(
                "SELECT value FROM RepoProperty WHERE repo_id=? AND key='is-readonly'",
                (lib_id,)
            )
            row = cursor.fetchone()
            if row and row[0] == "true":
                continue

            if row:
                cursor.execute(
                    "UPDATE RepoProperty SET value='true' WHERE repo_id=? AND key='is-readonly'",
                    (lib_id,)
                )
            else:
                cursor.execute(
                    "INSERT INTO RepoProperty (repo_id, key, value) VALUES (?, 'is-readonly', 'true')",
                    (lib_id,)
                )
            print(f"[sync] Set library {lib_id} to read-only")

        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[sync] Warning: Failed to set read-only: {e}", file=sys.stderr)


def main():
    conf_dir = os.environ.get("SEAFILE_CONF_DIR")
    data_dir = os.environ.get("SEAFILE_CLI_DATA_DIR", "/data")
    server_url = os.environ.get("SEAFILE_CLI_SERVER_URL", "")
    username = os.environ.get("SEAFILE_CLI_USERNAME", "")
    password = os.environ.get("SEAFILE_CLI_PASSWORD", "")
    library_ids_str = os.environ.get("SEAFILE_CLI_LIBRARY_IDS", "")
    use_token = os.environ.get("SEAFILE_CLI_USE_TOKEN", "false").lower() == "true"

    if not all([server_url, username, password, library_ids_str]):
        print("[sync] Missing required environment variables", file=sys.stderr)
        sys.exit(1)

    # Always authenticate via system Python (seaf-cli's Python has issues)
    print("[sync] Authenticating via system Python...")
    token = get_api_token(server_url, username, password)
    if not token:
        print("[sync] Failed to obtain API token", file=sys.stderr)
        sys.exit(1)

    # For pi builds, patch seaf-cli to use our pre-fetched token
    seaf_cli_cmd = "seaf-cli"
    if not use_token:
        os.environ["SEAF_PREFETCHED_TOKEN"] = token
        if patch_seaf_cli():
            seaf_cli_cmd = PATCHED_SEAF_CLI

    wanted_ids = {lib_id.strip() for lib_id in library_ids_str.split(",") if lib_id.strip()}

    # Check for and fix server resolution errors
    log_path = os.path.join(conf_dir, "logs", "seafile.log")
    desync_bad_libraries(conf_dir, data_dir, log_path)

    # Get already synced libraries
    synced_ids = get_synced_libraries(conf_dir)
    needed_ids = wanted_ids - synced_ids

    if not needed_ids:
        print("[sync] All libraries already synced")
        return

    # Fetch remote library list to get names
    print("[sync] Fetching remote library list...")
    remote_libs = get_remote_libraries(server_url, token)
    if not remote_libs:
        print("[sync] Failed to fetch remote libraries", file=sys.stderr)
        sys.exit(1)

    for lib_id in needed_ids:
        lib_name = remote_libs.get(lib_id)
        if not lib_name:
            print(f"[sync] Library {lib_id} not found on remote server, skipping")
            continue

        sync_path = os.path.join(data_dir, lib_name)
        os.makedirs(sync_path, exist_ok=True)

        print(f"[sync] Syncing library '{lib_name}' ({lib_id}) to {sync_path}...")
        sync_cmd = [
            seaf_cli_cmd, "sync",
            "-c", conf_dir,
            "-l", lib_id,
            "-s", server_url,
            "-d", sync_path,
            "-u", username,
        ]
        if use_token:
            sync_cmd += ["-T", token]
        else:
            sync_cmd += ["-p", password]
        result = subprocess.run(
            sync_cmd,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0 and "Task is already in progress" not in result.stderr:
            print(f"[sync] Error syncing {lib_name}: {result.stderr.strip()}", file=sys.stderr)
        else:
            output = (result.stdout + result.stderr).strip()
            if output:
                print(f"[sync] {output}")

    # Mark all libraries as read-only to prevent upload attempts
    # Note: this is now done via --set-readonly before daemon starts


def set_readonly_mode():
    """Set all wanted libraries to read-only in the DB (daemon must be stopped)."""
    data_dir = os.environ.get("SEAFILE_CLI_DATA_DIR", "/data")
    conf_dir = os.environ.get("SEAFILE_CONF_DIR")
    library_ids_str = os.environ.get("SEAFILE_CLI_LIBRARY_IDS", "")
    wanted_ids = {lib_id.strip() for lib_id in library_ids_str.split(",") if lib_id.strip()}
    if wanted_ids:
        set_libraries_readonly(conf_dir, data_dir, wanted_ids)


if __name__ == "__main__":
    import sys as _sys
    if "--set-readonly" in _sys.argv:
        set_readonly_mode()
    else:
        main()
