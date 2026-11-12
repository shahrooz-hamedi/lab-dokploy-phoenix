# LAB LXC — HUB and SIP Provider Routing

Run this procedure as `root` inside the LAB tunnel LXC (VMID 150).

It configures persistent routing between LAB, HUB, and the Asiatech SIP/RTP provider networks. It does not restart C-Tunnel or change tunnel transport.

## 1. Network requirements

| Item | Value |
|---|---|
| LAB tunnel interface | `ct-lab-hub` |
| LAB tunnel address | `10.100.30.10` |
| HUB tunnel peer | `10.100.30.100` |
| LAB LXC LAN address | `192.168.11.50` |
| OpenWrt gateway | `192.168.11.1` |
| FreePBX | `192.168.11.30` |
| HUB Docker subnet | `172.23.0.0/16` |
| C-Tunnel unit | `ctunnel@lab-hub.service` |

Required OpenWrt static routes:

| Destination | Gateway |
|---|---|
| `185.98.113.196/32` | `192.168.11.50` |
| `185.98.113.208/29` | `192.168.11.50` |
| `185.98.113.216/29` | `192.168.11.50` |
| `185.98.113.120/29` | `192.168.11.50` |

Configure these routes persistently on OpenWrt. Do not change existing LAN default gateways or other site routes.

## 2. Check prerequisites

```bash
set -eu

systemctl is-enabled ctunnel@lab-hub.service
ip link show ct-lab-hub
ip addr show ct-lab-hub
```

The `ct-lab-hub` interface must be created by the active `ctunnel@lab-hub.service` unit.

## 3. Enable IPv4 forwarding persistently

```bash
cat > /etc/sysctl.d/90-lab-hub-forwarding.conf <<'EOF'
net.ipv4.ip_forward = 1
EOF

sysctl --system

test "$(sysctl -n net.ipv4.ip_forward)" = "1"
```

## 4. Install persistent route recovery

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

echo "[LAB-HUB-ROUTES] Installing routes..."

ip route replace 172.23.0.0/16 dev "$IFACE"

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

rm -f /etc/systemd/system/ctunnel-engine@lab-hub.service.d/site-routes.conf

systemctl daemon-reload
```

## 5. Apply routes without restarting C-Tunnel

```bash
/usr/local/sbin/lab-hub-routes
```

This immediately installs the routes. The `ExecStartPost` hook reinstalls them whenever `ctunnel@lab-hub.service` starts.

## 6. Verify configuration

```bash
echo "========== TUNNEL SERVICE =========="
systemctl is-active ctunnel@lab-hub.service

echo
echo "========== IPV4 FORWARDING =========="
sysctl net.ipv4.ip_forward

echo
echo "========== HUB ROUTE =========="
ip route show 172.23.0.0/16
ip route get 172.23.0.100

echo
echo "========== PROVIDER ROUTES =========="
ip route show 185.98.113.196/32
ip route show 185.98.113.208/29
ip route show 185.98.113.216/29
ip route show 185.98.113.120/29

echo
echo "========== PROVIDER ROUTE LOOKUPS =========="
ip route get 185.98.113.196
ip route get 185.98.113.209
ip route get 185.98.113.217
ip route get 185.98.113.121

echo
echo "========== HUB CONNECTIVITY =========="
ping -c 4 -W 2 10.100.30.100
ping -c 4 -W 2 172.23.0.100

echo
echo "========== SYSTEMD ROUTE HOOK =========="
systemctl cat ctunnel@lab-hub.service
```

Expected provider route lookups:

```text
via 10.100.30.100 dev ct-lab-hub src 10.100.30.10
```

Expected HUB Docker route:

```text
172.23.0.0/16 dev ct-lab-hub
```

## 7. Operational rules

- Use `ctunnel@lab-hub.service`, not `ctunnel-engine@lab-hub.service`.
- Do not change the WireGuard transport or tunnel addresses.
- Do not change LAB LAN interfaces or default gateways.
- Do not add NAT rules to the LAB LXC.
- HUB tunnel container handles provider-facing source NAT and inbound SIP/RTP forwarding.
- Keep the four OpenWrt static routes configured persistently.
- Do not restart the tunnel merely to apply route changes.