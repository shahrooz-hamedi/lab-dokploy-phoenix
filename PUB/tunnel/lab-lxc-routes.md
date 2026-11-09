# LAB LXC Route Recovery — PUB

This runbook documents route recovery inside the LAB Proxmox LXC (VMID 150).

LAB is an LXC deployment, not a Docker or Dokploy deployment.

## 1. Network details

| Item | Value |
|---|---|
| LAB tunnel interface | `ct-lab-pub` |
| Transport | GRETAP |
| LAB tunnel address | `10.100.10.10` |
| PUB tunnel address | `10.100.10.100` |
| PUB Docker subnet | `172.19.0.0/16` |
| LAB systemd unit | `ctunnel-engine@lab-pub.service` |

The route to the PUB Docker network must use the LAB-PUB GRETAP interface. It must not use either LAB LAN default gateway.

## 2. Inspect current state

Run inside LAB LXC as root:

```bash
echo "========== LAB-PUB INTERFACE =========="
ip -br addr show ct-lab-pub

echo
echo "========== LAB-PUB SERVICE =========="
systemctl --no-pager --full status ctunnel-engine@lab-pub.service

echo
echo "========== CURRENT PUB ROUTE =========="
ip route show 172.19.0.0/16

echo
echo "========== ROUTE LOOKUPS =========="
ip route get 172.19.0.1
ip route get 172.19.0.100
```

Expected route:

```text
172.19.0.0/16 dev ct-lab-pub
```

Expected route lookup uses `ct-lab-pub`, with source address `10.100.10.10`.

## 3. Install persistent route recovery

This installs a route script and attaches it to the LAB-PUB userspace engine unit.

It does not restart the tunnel.

```bash
set -eu

cat > /usr/local/sbin/lab-pub-routes <<'EOF'
#!/bin/sh
set -eu

IFACE="ct-lab-pub"
REMOTE_NET="172.19.0.0/16"

echo "[LAB-PUB-ROUTES] Waiting for ${IFACE}..."

i=0
until ip link show dev "$IFACE" >/dev/null 2>&1; do
    i=$((i + 1))
    if [ "$i" -ge 30 ]; then
        echo "[LAB-PUB-ROUTES] ERROR: ${IFACE} is unavailable." >&2
        exit 1
    fi
    sleep 1
done

echo "[LAB-PUB-ROUTES] Installing PUB route..."

ip route replace "$REMOTE_NET" dev "$IFACE"

echo "[LAB-PUB-ROUTES] Installed route:"
ip route show "$REMOTE_NET"
EOF

chmod 0755 /usr/local/sbin/lab-pub-routes

mkdir -p /etc/systemd/system/ctunnel-engine@lab-pub.service.d

cat > /etc/systemd/system/ctunnel-engine@lab-pub.service.d/site-routes.conf <<'EOF'
[Service]
ExecStartPost=/usr/local/sbin/lab-pub-routes
EOF

systemctl daemon-reload

# Restore the live route without restarting the LAB-PUB tunnel.
ip route replace 172.19.0.0/16 dev ct-lab-pub
```

## 4. Verify route and connectivity

```bash
echo "========== PUB ROUTE =========="
ip route show 172.19.0.0/16

echo
echo "========== PUB ROUTE LOOKUPS =========="
ip route get 172.19.0.1
ip route get 172.19.0.100

echo
echo "========== PUB CONNECTIVITY =========="
ping -c 4 -W 2 172.19.0.1
ping -c 4 -W 2 172.19.0.100

echo
echo "========== CORRECT SYSTEMD UNIT =========="
systemctl cat ctunnel-engine@lab-pub.service

echo
echo "========== ROUTE SCRIPT =========="
cat /usr/local/sbin/lab-pub-routes
```

Expected route:

```text
172.19.0.0/16 dev ct-lab-pub
```

Expected source address for PUB route lookups:

```text
10.100.10.10
```

## 5. Operational notes

- The correct LAB-PUB unit is `ctunnel-engine@lab-pub.service`.
- Keep the LAB-PUB GRETAP transport selection unchanged.
- The route hook runs whenever the LAB-PUB userspace engine starts.
- The immediate route installation does not restart the tunnel.
- Do not modify LAB LAN interfaces, default gateways, Proxmox networking, or PUB Docker networking through this procedure.

This runbook manages only the LAB LXC route and its systemd integration.