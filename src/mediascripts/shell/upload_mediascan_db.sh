#!/bin/bash
set -euo pipefail
rsync -ahvP "$MOONGAS_COLLECTION_ROOTDIR/mediascan.db" root@$MEDIASERVER_DROPLET_IP:/var/www/moongas/mediascan.db --timeout=10
