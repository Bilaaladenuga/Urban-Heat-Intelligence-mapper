#!/usr/bin/env bash
#
# Reliable `npm install` for this Windows machine.
#
# Encodes the workarounds discovered while installing apps/web deps:
#   1. The npm registry is extremely slow from this network (~30s per request),
#      so we install OFFLINE from the warm local cache whenever possible.
#   2. Postinstall scripts CRASH on this machine (unrs-resolver exits with
#      0xC0000142, a Windows DLL-init failure, likely antivirus). We skip them
#      with --ignore-scripts; nothing in our dependency tree needs them.
#   3. Antivirus file-locks intermittently break extraction of large packages
#      (next) with "ENOTEMPTY: directory not empty". We kill any lingering
#      node/npm processes first, and retry the install — npm resumes where it
#      left off, so repeated runs converge.
#   4. Completion is detected via node_modules/.package-lock.json (npm's hidden
#      lock that marks a finished install) plus the presence of expected bins.
#
# Usage:
#   bash scripts/npm-install-win.sh [target-dir] [extra npm args...]
#
# Examples:
#   bash scripts/npm-install-win.sh apps/web
#   bash scripts/npm-install-win.sh apps/web --prefer-offline   # allow network fallback
#
# Exit codes: 0 = install complete, 1 = gave up after MAX_ATTEMPTS.

set -u

TARGET_DIR="${1:-apps/web}"
shift || true

# Extra npm flags. Default is fully offline (cache-only). If you pass
# --prefer-offline (or any flag), it overrides the default entirely.
NPM_FLAGS="${*:---offline}"

MAX_ATTEMPTS=8
SUCCESS=0

cd "$TARGET_DIR" || { echo "ERROR: cannot cd into $TARGET_DIR"; exit 1; }
echo "==> Installing deps in $(pwd)"
echo "    npm flags: $NPM_FLAGS"

for attempt in $(seq 1 "$MAX_ATTEMPTS"); do
  echo
  echo "==> Attempt $attempt/$MAX_ATTEMPTS"

  # 1. Kill lingering node/npm processes that may hold file locks.
  #    (xargs -r = no-op when empty; kill errors are ignored.)
  ps aux 2>/dev/null | grep -iE "node|npm" | grep -v grep \
    | awk '{print $1}' | xargs -r kill 2>/dev/null
  sleep 1

  # 2. Run the install. --ignore-scripts avoids the crashing postinstalls.
  if npm install --ignore-scripts --no-audit --no-fund $NPM_FLAGS; then
    echo "==> npm install reported success."
    break
  fi
  echo "==> Attempt $attempt failed; will retry (npm resumes progress)."
  sleep 2
done

# 3. Verify completion with npm's hidden lock file (only written when an
#    install finishes cleanly).
if [ -f node_modules/.package-lock.json ]; then
  echo
  echo "==> Install complete: node_modules/.package-lock.json present."
  SUCCESS=1
else
  echo
  echo "ERROR: install did not complete after $MAX_ATTEMPTS attempts"
  echo "       (no node_modules/.package-lock.json)."
  echo "       If you keep hitting ENOTEMPTY, close file explorer / editors"
  echo "       that might hold node_modules open, then rerun this script."
  SUCCESS=0
fi

# 4. Sanity-check the CLI binaries we actually use.
for bin in next; do
  if [ -x "node_modules/.bin/$bin" ] || [ -f "node_modules/.bin/$bin" ]; then
    echo "    - .bin/$bin OK"
  else
    echo "    WARNING: node_modules/.bin/$bin missing"
    SUCCESS=0
  fi
done

[ "$SUCCESS" = "1" ] && exit 0 || exit 1
