#!/bin/bash
set -euo pipefail

copy-medialib \
  --src-paths "$MOONGAS_COLLECTION_LOCAL/data/Music" \
  --dst-path "$MOONGAS_COLLECTION_DEMO/data/" \
  --include-filenames artist.yml \
  --dir-copy-mode PreserveStructure \
  --overwrite-existing
