#!/bin/bash
set -euo pipefail

pushd moongas-mediascan-go > /dev/null
go run cmd/scan-to-track-yaml "$MOONGAS_COLLECTION_ROOTDIR/mediascan-config.yml"
popd > /dev/null
