#!/bin/bash
# Syncs project xml and media changes to the Kodi addon directory that Kodi actually reads.
KODI_ADDON="/Users/michaelhernandez/Library/Application Support/Kodi/addons/skin.hbomax.dev"
PROJECT_ROOT="/Users/michaelhernandez/Coding Projects/HBOMAXSKIN"

rsync -av \
  --include="*/" \
  --include="*.xml" \
  --include="*.png" \
  --include="*.svg" \
  --include="*.py" \
  --exclude="*" \
  "$PROJECT_ROOT/" "$KODI_ADDON/"
echo "Sync complete. Reload the skin in Kodi."
