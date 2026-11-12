# LAB LXC Route Recovery — HUB and SIP Provider

This runbook documents routing from the LAB LAN to the HUB and
to the Asiatech SIP/RTP provider networks.

LAB is a Proxmox LXC deployment, not a Docker or Dokploy deployment.

## 1. Network details

| Item | Value |
|---|---|
| LAB LXC VMID | `150` |
| LAB tunnel interface | `ct-lab-hub` |
| Transport | WireGuard |
| LAB tunnel address | `10.100.30.10` |
| HUB tunnel address | `10.100.30.100` |
| LAB LXC LAN address | `192.168.11.50` |
| LAB OpenWrt gateway | `192.168.11.1` |
| FreePBX address | `192.168.11.30` |
| HUB Docker subnet | `172.23.0.0/16` |
| LAB systemd unit | `ctunnel@lab-hub.service` |

## 2. Required OpenWrt static routes

The LAB OpenWrt router must send provider traffic to the LAB LXC
at `192.168.11.50`.

These routes must be configured persistently in OpenWrt:

| Destination | Gateway |
|---|---|
| `185.98.113.196/32` | `192.168.11.50` |
| `185.98.113.208/29` | `192.168.11.50` |
| `185.98.113.216/29` | `192.168.11.50` |
| `185.98.113.120/29` | `192.168.11.50` |

Do not replace or remove existing routes to HUB or PUB networks.

## 3. Required LAB LXC routes

The LAB LXC must route the following networks through
`ct-lab-hub`:

| Destination | Next hop / interface |
|---|---|
| `172.23.0.0/16` | `ct-lab-hub` |
| `185.98.113.196/32` | `10.100.30.100` |
| `185.98.113.208/29` | `10.100.30.100` |
| `185.98.113.216/29` | `10.100.30.100` |
| `185.98.113.120/29` | `10.100.30.100` |

The provider routes must not use either LAB LAN default gateway.

## 4. Inspect current state

Run inside LAB LXC as root:

```bash
echo "========== LAB-HUB INTERFACE =========="
ip -br addr show ct-lab-hub

echo
echo "========== LAB-HUB SERVICE =========="
systemctl --no-pager --full status ctunnel@lab-hub.service

echo
echo "========== HUB ROUTE =========="
ip route show 172.23.0.0/16

echo
echo "========== PROVIDER ROUTES =========="
ip route show 185.98.113.196/32
ip route show 185.98.113.208/29
ip route show 185.98.113.216/29
ip route show 185.98.113.120/29

echo
echo "========== ROUTE LOOKUPS =========="
ip route get 172.23.0.100
ip route get 185.98.113.196
ip route get 185.98.113.209
ip route get 185.98.113.217
ip route get 185.98.113.121

echo
echo "========== FORWARDING =========="
sysctl net.ipv4.ip_forward
```

Expected provider route lookups use:

```text
via 10.100.30.100 dev ct-lab-hub
```

Expected source address for locally generated route lookups:

```text
10.100.30.10
```

Forwarded packets originating from FreePBX retain their original
source address until they reach the HUB tunnel container.

## 5. Install persistent route recovery

This installs the route script and attaches it to the correct
WireGuard systemd unit.

It does not restart the tunnel.

Run inside LAB LXC as root:

```bash
set -eu

cat > /usr/local/sbin/lab-hub-routes <<'EOF'
#!/bin/sh
set -eu

IFACE="ct-lab-hub"
HUB_PEER="10.100.30.100"

echo "[LAB-HUB-ROUTES] Waiting for ${IFACE}..."

i=0
until ip link show dev "$IFACE" >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge 30 ]; then
        echo "[LAB-HUB-ROUTES] ERROR: ${IFACE} is unavailable." >&2
        exit 1
    fi
    sleep 1
done

echo "[LAB-HUB-ROUTES] Installing HUB route..."

ip route replace 172.23.0.0/16 dev "$IFACE"

echo "[LAB-HUB-ROUTES] Installing SIP provider routes..."

ip route replace 185.98.113.196/32 via "$HUB_PEER" dev "$IFACE"
ip route replace 185.98.113.208/29 via "$HUB_PEER" dev "$IFACE"
ip route replace 185.98.113.216/29 via "$HUB_PEER" dev "$IFACE"
ip route replace 185.98.113.120/29 via "$HUB_PEER" dev "$IFACE"

echo "[LAB-HUB-ROUTES] Installed routes:"
ip route show 172.23.0.0/16
ip route show 185.98.113.196/32
ip route show 185.98.113.208/29
ip route show 185.98.113.216/29
ip route show 185.98.113.120/29
EOF

chmod 0755 /usr/local/sbin/lab-hub-routes

mkdir -p /etc/systemd/system/ctunnel@lab-hub.service.d

cat > /etc/systemd/system/ctunnel@lab-hub.service.d/site-routes.conf <<'EOF'
[Service]
ExecStartPost=/usr/local/sbin/lab-hub-routes
EOF

# Remove the obsolete route hook from the inactive engine unit.
rm -f /etc/systemd/system/ctunnel-engine@lab-hub.service.d/site-routes.conf

systemctl daemon-reload

# Restore routes immediately without restarting WireGuard.
/usr/local/sbin/lab-hub-routes
```

## 6. Verify routes and connectivity

```bash
echo "========== HUB ROUTE =========="
ip route show 172.23.0.0/16

echo
echo "========== PROVIDER ROUTES =========="
ip route show 185.98.113.196/32
ip route show 185.98.113.208/29
ip route show 185.98.113.216/29
ip route show 185.98.113.120/29

echo
echo "========== ROUTE LOOKUPS =========="
ip route get 172.23.0.100
ip route get 185.98.113.196
ip route get 185.98.113.209
ip route get 185.98.113.217
ip route get 185.98.113.121

echo
echo "========== HUB CONNECTIVITY =========="
ping -c 4 -W 2 10.100.30.100
ping -c 4 -W 2 172.23.0.100

echo
echo "========== ROUTE SCRIPT =========="
cat /usr/local/sbin/lab-hub-routes

echo
echo "========== SYSTEMD DROP-IN =========="
systemctl cat ctunnel@lab-hub.service
```

## 7. Operational notes

- The correct LAB-HUB unit is `ctunnel@lab-hub.service`.
- `ctunnel-engine@lab-hub.service` must remain inactive.
- The route hook runs whenever the WireGuard unit starts.
- The immediate route installation does not restart the tunnel.
- Do not change the LAB-HUB transport selection.
- Do not change LAB LAN interfaces or default gateways.
- Do not add NAT rules to the LAB LXC for this design.
- The HUB tunnel container handles the provider-facing source NAT.
- The LAB OpenWrt static routes must remain configured persistently.
