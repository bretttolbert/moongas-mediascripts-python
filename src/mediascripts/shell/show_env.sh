#!/bin/bash

set -euo pipefail

echo "|------------------------------------------------------------------------|"
echo "|                     Moongas Environment                                |"
echo "|------------------------------------------------------------------------|"
echo "| MOONGAS_COLLECTION_ROOTDIR:                                            "
echo "|   \"${MOONGAS_COLLECTION_ROOTDIR:-}\"                                  "
echo "| MOONGAS_SERVER_IP:                                                     "
echo "|   \"${MOONGAS_SERVER_IP:-}\"                                           "
echo "|------------------------------------------------------------------------|"
