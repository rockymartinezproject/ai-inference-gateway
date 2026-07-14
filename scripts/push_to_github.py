#!/usr/bin/env python3
"""Push all repository files to GitHub in a single commit via the Git Data API.

Usage:
    export GITHUB_TOKEN=ghp_...
    export COMMIT_MESSAGE="feat: my daily change"
    python scripts/push_to_github.py

This avoids the per-file-commit spam that the old Contents API approach produced.
Local git is still not used; everything goes through the GitHub REST API.
"""

import base64
import hashlib
import json
import os
import time
import urllib.error
import urllib.request

TOKEN = os.environ["GITHUB_TOKEN"]
OWNER = "rockymartinezproject"
REPO = "ai-inference-gateway"
BRANCH = "main"
API_BASE = f"https://api.github.com/repos/{OWNER}/{REPO}"

SKIP_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
    ".venv",
    "venv",
}


def api_call(method: str, endpoint: str, data: dict | None = None) -> dict:
    url = f"{API_BASE}/{endpoint}"
    headers = {
        "Authorization": f"token {TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "Content-Type": "application/json",
        "User-Agent": "ai-gateway-push",
    }
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())


def api_call_with_retry(method: str, endpoint: str, data: dict | None = None, max_attempts: int = 5) -> dict:
    for attempt in range(max_attempts):
        try:
            return api_call(method, endpoint, data)
        except urllib.error.HTTPError as e:
            if e.code in {502, 503, 504, 429} and attempt < max_attempts - 1:
                wait = 2 ** attempt
                print(f"  HTTP {e.code} for {endpoint}, retrying in {wait}s...")
                time.sleep(wait)
                continue
            raise
    raise RuntimeError(f"Failed {method} {endpoint} after {max_attempts} attempts")


def git_blob_sha(content: bytes) -> str:
    """Compute the Git blob SHA for a byte string."""
    header = f"blob {len(content)}\0".encode()
    return hashlib.sha1(header + content).hexdigest()


def get_local_files() -> dict[str, bytes]:
    """Return a mapping of repo-relative paths to file contents."""
    files: dict[str, bytes] = {}
    skip_prefixes = tuple(p + "/" for p in SKIP_DIRS)
    for root, dirs, filenames in os.walk("."):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for filename in filenames:
            if filename.endswith(".pyc"):
                continue
            filepath = os.path.join(root, filename)
            relpath = os.path.relpath(filepath).replace("\\", "/")
            if relpath.startswith(skip_prefixes):
                continue
            with open(filepath, "rb") as f:
                files[relpath] = f.read()
    return files


def get_current_tree() -> tuple[str, dict[str, dict]]:
    """Return (tree_sha, {path: entry}) for the current branch."""
    ref = api_call_with_retry("GET", f"git/ref/heads/{BRANCH}")
    commit_sha = ref["object"]["sha"]
    commit = api_call_with_retry("GET", f"git/commits/{commit_sha}")
    tree_sha = commit["tree"]["sha"]
    tree = api_call_with_retry("GET", f"git/trees/{tree_sha}?recursive=1")
    entries = {entry["path"]: entry for entry in tree.get("tree", []) if entry["type"] == "blob"}
    return tree_sha, entries


def create_blob(content: bytes) -> str:
    """Create a Git blob and return its SHA."""
    resp = api_call_with_retry(
        "POST",
        "git/blobs",
        {"content": base64.b64encode(content).decode(), "encoding": "base64"},
    )
    return resp["sha"]


def push_all(message: str) -> None:
    local_files = get_local_files()
    print(f"Found {len(local_files)} local files.")

    base_tree_sha, current_entries = get_current_tree()
    print(f"Current tree has {len(current_entries)} entries.")

    tree_entries: list[dict] = []
    changed = 0
    unchanged = 0
    for path, content in sorted(local_files.items()):
        new_sha = git_blob_sha(content)
        existing = current_entries.get(path)
        if existing and existing["sha"] == new_sha:
            unchanged += 1
            continue
        blob_sha = create_blob(content)
        tree_entries.append(
            {
                "path": path,
                "mode": "100644",
                "type": "blob",
                "sha": blob_sha,
            }
        )
        changed += 1

    # Delete files present in the remote tree but missing locally.
    deleted = 0
    for path in current_entries:
        if path not in local_files:
            tree_entries.append({"path": path, "mode": "100644", "type": "blob", "sha": None})
            deleted += 1

    print(f"{changed} changed/new, {deleted} deleted, {unchanged} unchanged.")

    if not tree_entries:
        print("Nothing to push.")
        return

    new_tree = api_call_with_retry(
        "POST",
        "git/trees",
        {"base_tree": base_tree_sha, "tree": tree_entries},
    )
    new_tree_sha = new_tree["sha"]

    ref = api_call_with_retry("GET", f"git/ref/heads/{BRANCH}")
    parent_sha = ref["object"]["sha"]

    new_commit = api_call_with_retry(
        "POST",
        "git/commits",
        {
            "message": message,
            "tree": new_tree_sha,
            "parents": [parent_sha],
        },
    )
    new_commit_sha = new_commit["sha"]

    api_call_with_retry(
        "PATCH",
        f"git/refs/heads/{BRANCH}",
        {"sha": new_commit_sha},
    )

    print(f"Pushed commit {new_commit_sha}: {message}")


def main() -> None:
    message = os.environ.get("COMMIT_MESSAGE", "chore: sync repository files")
    push_all(message)


if __name__ == "__main__":
    main()
