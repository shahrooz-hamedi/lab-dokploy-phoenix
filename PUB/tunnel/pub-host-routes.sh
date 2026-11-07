#!/bin/sh
set -eu

BRIDGE="br-xui6"
GATEWAY="172.19.0.100"

echo "[PUB-HOST-ROUTES] Waiting for Docker bridge ${BRIDGE}..."

i=0
until ip link show dev "$BRIDGE" >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge 120 ]; then
        echo "[PUB-HOST-ROUTES] ERROR: Docker bridge unavailable." >&2
        exit 1
    fi
    sleep 1
done

echo "[PUB-HOST-ROUTES] Installing LAB and HUB routes..."

# Remote site networks
ip route replace 192.168.10.0/24 via "$GATEWAY" dev "$BRIDGE"
ip route replace 192.168.11.0/24 via "$GATEWAY" dev "$BRIDGE"
ip route replace 172.23.0.0/16 via "$GATEWAY" dev "$BRIDGE"

# Return routes to remote C-Tunnel peer addresses
ip route replace 10.100.20.10/32 via "$GATEWAY" dev "$BRIDGE"
ip route replace 10.100.10.10/32 via "$GATEWAY" dev "$BRIDGE"

echo "[PUB-HOST-ROUTES] Installed routes:"
ip route show 192.168.10.0/24
ip route show 192.168.11.0/24
ip route show 172.23.0.0/16
ip route show 10.100.20.10/32
ip route show 10.100.10.10/32

echo "[PUB-HOST-ROUTES] Configuration complete."
