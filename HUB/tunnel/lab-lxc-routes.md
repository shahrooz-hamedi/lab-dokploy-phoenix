# LAB LXC Route Recovery — HUB

This runbook documents route recovery inside the LAB Proxmox LXC (VMID 150).

LAB is an LXC deployment, not a Docker or Dokploy deployment.

## 1. Network details

| Item | Value |
|---|---|
| LAB tunnel interface | `ct-lab-hub` |
| Transport | WireGuard |
| LAB tunnel address | `10.100.30.10` |
| HUB tunnel address | `10.100.30.100` |
| HUB Docker subnet | `172.23.0.0/16` |
| LAB systemd unit | `ctunnel@lab-hub.service` |

The route to the HUB Docker network must use the LAB-HUB WireGuard interface. It must not use either LAB LAN default gateway.

## 2. Inspect current state

Run inside LAB LXC as root:

```bash
echo "========== LAB-HUB INTERFACE =========="
ip -br addr show ct-lab-hub

echo
echo "========== LAB-HUB SERVICE =========="
systemctl --no-pager --full status ctunnel@lab-hub.service

echo
echo "========== CURRENT HUB ROUTE =========="
ip route show 172.23.0.0/16

echo
echo "========== ROUTE LOOKUPS =========="
ip route get 172.23.0.1
ip route get 172.23.0.100
```

Expected route:

```text
172.23.0.0/16 dev ct-lab-hub
```

Expected route lookup uses `ct-lab-hub`, with source address `10.100.30.10`.

## 3. Install persistent route recovery

This installs a route script and attaches it to the correct WireGuard systemd unit.

It does not restart the tunnel.

```bash
set -eu

cat > /usr/local/sbin/lab-hub-routes <<'EOF'
#!/bin/sh
set -eu

IFACE="ct-lab-hub"
REMOTE_NET="172.23.0.0/16"

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

ip route replace "$REMOTE_NET" dev "$IFACE"

echo "[LAB-HUB-ROUTES] Installed route:"
ip route show "$REMOTE_NET"
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

# Restore the live route without restarting WireGuard.
ip route replace 172.23.0.0/16 dev ct-lab-hub
```

## 4. Verify route and connectivity

```bash
echo "========== HUB ROUTE =========="
ip route show 172.23.0.0/16

echo
echo "========== HUB ROUTE LOOKUPS =========="
ip route get 172.23.0.1
ip route get 172.23.0.100

echo
echo "========== HUB CONNECTIVITY =========="
ping -c 4 -W 2 172.23.0.1
ping -c 4 -W 2 172.23.0.100

echo
echo "========== CORRECT SYSTEMD UNIT =========="
systemctl cat ctunnel@lab-hub.service

echo
echo "========== ROUTE SCRIPT =========="
cat /usr/local/sbin/lab-hub-routes
```

Expected route:

```text
172.23.0.0/16 dev ct-lab-hub
```

Expected source address for HUB route lookups:

```text
10.100.30.10
```

## 5. Operational notes

- The correct LAB-HUB unit is `ctunnel@lab-hub.service`.
- `ctunnel-engine@lab-hub.service` must remain disabled/inactive.
- The route hook runs whenever the correct WireGuard unit starts.
- The immediate route installation does not restart the tunnel.
- Do not change the LAB-HUB transport selection as part of route recovery.
- Do not modify LAB LAN interfaces, default gateways, Proxmox networking, or HUB Docker networking through this procedure.

This runbook manages only the LAB LXC route and its systemd integration.