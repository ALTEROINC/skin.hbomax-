#!/bin/bash
VERSION=${1:-1.0.0}
TMPDIR=$(mktemp -d)
mkdir -p "$TMPDIR/skin.hbomax"
rsync -av --exclude='.git' --exclude='.github' --exclude='tools' --exclude='*.md' --exclude='*.py' --exclude='*.txt' ./ "$TMPDIR/skin.hbomax/"
cd "$TMPDIR"
zip -r "$OLDPWD/skin.hbomax-$VERSION.zip" skin.hbomax/
cd "$OLDPWD"
rm -rf "$TMPDIR"
echo "Built skin.hbomax-$VERSION.zip"
echo "Top level folder inside zip:"
unzip -l "skin.hbomax-$VERSION.zip" | head -5
