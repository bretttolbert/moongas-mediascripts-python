#!/bin/bash
set -euo pipefail
rsync -ahvP /data/Covers/ root@$MEDIASERVER_DROPLET_IP:/var/www/html/Covers/ --delete --timeout=10
