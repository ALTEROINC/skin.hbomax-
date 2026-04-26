#!/bin/bash
set -e

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
VERSION=${1:-1.0.0}
ZIPNAME="skin.hbomax-${VERSION}.zip"
TMPDIR="$(mktemp -d)"

mkdir -p "${TMPDIR}/skin.hbomax"

rsync -a \
  --exclude='.git' \
  --exclude='.github' \
  --exclude='.DS_Store' \
  --exclude='tools/' \
  --exclude='*.md' \
  --exclude='*.py' \
  --exclude='*.txt' \
  --exclude='*.zip' \
  "${REPO_ROOT}/" "${TMPDIR}/skin.hbomax/"

rm -f "${REPO_ROOT}/${ZIPNAME}"
(cd "${TMPDIR}" && zip -r "${REPO_ROOT}/${ZIPNAME}" skin.hbomax/)

rm -rf "${TMPDIR}"

echo "Built ${ZIPNAME}"
echo ""
echo "Top 5 lines of zip listing:"
unzip -l "${REPO_ROOT}/${ZIPNAME}" | head -5

chmod +x "$0"
