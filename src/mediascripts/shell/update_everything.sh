#!/bin/bash
set -euo pipefail
./scan-to-files-yaml
./scan-to-artists-yaml
./scan-to-track-yaml
./scan-to-db
./upload-mediascan-db
./update-covers
./upload-covers
./restart-remote-services
sudo ./restart-local-services
