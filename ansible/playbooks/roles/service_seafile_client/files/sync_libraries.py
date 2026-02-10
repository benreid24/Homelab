#!/usr/bin/env python3
"""Sync Seafile libraries using seaf-cli sync with library names from list-remote.

On AppImage builds (USE_TOKEN=true), authentication is handled by this script
using system Python to obtain an API token, because the AppImage's bundled
Python has compatibility issues with some servers. The token is then passed
to seaf-cli with -T. On non-AppImage builds, password auth (-p) is used directly.
"""

import json
import os
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


def get_remote_libraries(server_url, username, credential, conf_dir, use_token):
    """Fetch remote libraries and return a dict of {id: name}."""
    auth_flag = "-T" if use_token else "-p"
    output = run([
        "seaf-cli", "list-remote",
        "-c", conf_dir,
        "-s", server_url,
        "-u", username,
        auth_flag, credential,
        "--json",
    ])
    if output is None:
        return {}

    try:
        libraries = json.loads(output)
        return {lib["id"]: lib["name"] for lib in libraries}
    except:
        print(f"[sync] Failed to parse list-remote output: {output}", file=sys.stderr)
        raise Exception("Failed to parse list-remote output")


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
    output = run(["seaf-cli", "list", "-c", conf_dir, "--json"], check=False)
    if not output:
        return set()

    try:
        libraries = json.loads(output)
        return {lib["id"] for lib in libraries}
    except (json.JSONDecodeError, KeyError):
        print(f"[sync] Failed to parse list output: {output}", file=sys.stderr)
        return set()


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

    # For AppImage builds, obtain a token via system Python to work around
    # the bundled Python's auth issues
    if use_token:
        print("[sync] Authenticating via system Python...")
        token = get_api_token(server_url, username, password)
        if not token:
            print("[sync] Failed to obtain API token", file=sys.stderr)
            sys.exit(1)
        credential = token
    else:
        credential = password

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
    remote_libs = get_remote_libraries(server_url, username, credential, conf_dir, use_token)
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
        auth_flag = "-T" if use_token else "-p"
        result = subprocess.run(
            [
                "seaf-cli", "sync",
                "-c", conf_dir,
                "-l", lib_id,
                "-s", server_url,
                "-d", sync_path,
                "-u", username,
                auth_flag, credential,
            ],
            capture_output=True,
            text=True,
        )

        if result.returncode != 0 and "Task is already in progress" not in result.stderr:
            print(f"[sync] Error syncing {lib_name}: {result.stderr.strip()}", file=sys.stderr)
        else:
            output = (result.stdout + result.stderr).strip()
            if output:
                print(f"[sync] {output}")


if __name__ == "__main__":
    main()
