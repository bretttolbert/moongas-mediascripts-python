#!/bin/bash
set -euo pipefail

SVC=mediatunes-svc
systemctl stop $SVC && sleep 1 && systemctl start $SVC; echo "Restarted $SVC"
echo "Restarted $SVC"

SVC=mediatunes-web
systemctl stop $SVC && sleep 1 && systemctl start $SVC; echo "Restarted $SVC"
echo "Restarted $SVC"

echo 'Done'
