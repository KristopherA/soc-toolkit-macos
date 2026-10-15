#!/bin/sh
# The rules folder shipped in the release zip is a git checkout that Hayabusa's built-in git cannot
# update in place. The first `update-rules` clones fresh into a temp folder and swaps it in only on
# success, so a failed download never leaves the volume without rules. Later updates are normal pulls.
set -eu
rules=/opt/hayabusa/rules
if [ "${1:-}" = "update-rules" ] && [ -f "$rules/.shipped-release" ]; then
  shift
  tmp=$(mktemp -d)
  if /opt/hayabusa/hayabusa update-rules -r "$tmp/rules" "$@" && [ -d "$tmp/rules/config" ]; then
    find "$rules" -mindepth 1 -delete
    cp -a "$tmp/rules/." "$rules/"
    rm -rf "$tmp"
    echo "Rules folder converted to a live clone; future update-rules runs pull changes."
    exit 0
  fi
  rm -rf "$tmp"
  echo "Rules update failed; the bundled rules were kept." >&2
  exit 1
fi
exec /opt/hayabusa/hayabusa "$@"
