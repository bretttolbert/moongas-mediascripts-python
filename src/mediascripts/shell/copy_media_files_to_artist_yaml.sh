#!/bin/bash
set -euo pipefail

"""
Copy media files from the local collection to the (metadata-only) 
demo collection and optionally generate track YAML files.

--make-track-yml (DEPRECATED - use moongas-mediascan-go/cmd/scan-to-track-yaml instead)
  Makes empty track yaml (.yml) file to represent the media file
"""
copy-medialib \
  --src-paths "$MOONGAS_COLLECTION_LOCAL/data/Music" \
  --dst-path "$MOONGAS_COLLECTION_DEMO/data/" \
  --include-filenames "*.mp3" "*.m4a" \
  --dir-copy-mode PreserveStructure \
  --make-track-yml \
  --diff \
  "$@"
