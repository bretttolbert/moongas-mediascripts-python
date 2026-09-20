#!/bin/bash
set -euo pipefail

pushd moongas-mediascan-go > /dev/null
go run cmd/scan-to-db/main.go "$MOONGAS_COLLECTION_ROOTDIR/mediascan-config.yml" "$MOONGAS_COLLECTION_ROOTDIR/mediascan.db"
popd > /dev/null
