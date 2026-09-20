#!/usr/bin/env bash

set -euo pipefail

cat << EOF
------------------------------------------------------------------------------
                             Moongas Environment                              
------------------------------------------------------------------------------
  MOONGAS_COLLECTION_ROOTDIR:
    "${MOONGAS_COLLECTION_ROOTDIR:-}"
  MOONGAS_REMOTE_SERVER_IP:
    "${MOONGAS_REMOTE_SERVER_IP:-}"
------------------------------------------------------------------------------
EOF