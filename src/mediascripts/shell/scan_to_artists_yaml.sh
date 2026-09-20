#!/bin/bash
set -euo pipefail

pushd moongas-mediascan-go > /dev/null
go run cmd/scan-to-artists-yaml/main.go "$MOONGAS_COLLECTION_ROOTDIR/mediascan-config.yml" "$MOONGAS_COLLECTION_ROOTDIR/scan-to-artists-yaml.yml"
popd > /dev/null