
# LAB LXC Route Recovery — PUB

This runbook documents route recovery inside the LAB Proxmox LXC (VMID 150).

LAB is an LXC deployment, not a Docker or Dokploy deployment. The LAB route script is installed manually inside the LXC. This file documents the configuration; it does not imply that LAB has a GitHub or Dokploy deployment integration.

## 1. Network details

| Item | Value |
|---|---|
| LAB tunnel interface | `ct-lab-pub` |
| Transport | GRETAP |
| LAB tunnel address | `10.100.10.10` |
| PUB tunnel address / next hop | `10.100.10.100` |
| PUB Docker subnet | `172.19.0.0/16` |
| LAB systemd unit | `ctunnel-engine@lab-pub.service` |
| Route script | `/usr/local/sbin/lab-pub-routes` |
| Systemd drop-in | `/etc/systemd/system/ctunnel-engine@lab-pub.service.d/site-routes.conf` |

The route to the PUB Docker network must use the LAB-PUB GRETAP interface and the remote tunnel peer as its next hop:

```text
172.19.0.0/16 via 10.100.10.100 dev ct-lab-pub
```

Do not install this route as a directly connected route using only `dev ct-lab-pub`. The remote PUB Docker subnet is reached through the PUB tunnel endpoint, `10.100.10.100`.

Do not use either LAB LAN default gateway for this route.

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
172.19.0.0/16 via 10.100.10.100 dev ct-lab-pub
```

Expected route lookups must use:

- Interface: `ct-lab-pub`
- Next hop: `10.100.10.100`
- Source address: `10.100.10.10`

## 3. Install persistent route recovery

This installs the route script and attaches it to the LAB-PUB userspace engine unit.

The route is installed after the tunnel engine starts, when the GRETAP interface is available.

This procedure does not restart the tunnel.

Run inside LAB LXC as root:

```bash
set -eu

cat > /usr/local/sbin/lab-pub-routes <<'EOF'
#!/bin/sh
set -eu

IFACE="ct-lab-pub"
REMOTE_PEER="10.100.10.100"
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

echo "[LAB-PUB-ROUTES] Installing PUB route via ${REMOTE_PEER}..."

ip route replace "$REMOTE_NET" via "$REMOTE_PEER" dev "$IFACE"

echo "[LAB-PUB-ROUTES] Installed route:"
ip route show "$REMOTE_NET"

echo "[LAB-PUB-ROUTES] Configuration complete."
EOF

chmod 0755 /usr/local/sbin/lab-pub-routes

mkdir -p /etc/systemd/system/ctunnel-engine@lab-pub.service.d

cat > /etc/systemd/system/ctunnel-engine@lab-pub.service.d/site-routes.conf <<'EOF'
[Service]
ExecStartPost=/usr/local/sbin/lab-pub-routes
EOF

systemctl daemon-reload

# Restore the live route without restarting the LAB-PUB tunnel.
ip route replace 172.19.0.0/16 via 10.100.10.100 dev ct-lab-pub
```

## 4. Verify route and connectivity

Run inside LAB LXC:

```bash
echo "========== PUB ROUTE =========="
ip route show 172.19.0.0/16

echo
echo "========== PUB ROUTE LOOKUPS =========="
ip route get 172.19.0.1
ip route get 172.19.0.100

echo
echo "========== PUB PEER CONNECTIVITY =========="
ping -c 4 -W 2 10.100.10.100

echo
echo "========== PUB DOCKER GATEWAY =========="
ping -c 4 -W 2 172.19.0.1

echo
echo "========== PUB TUNNEL CONTAINER =========="
ping -c 4 -W 2 172.19.0.100

echo
echo "========== SYSTEMD DROP-IN =========="
systemctl cat ctunnel-engine@lab-pub.service

echo
echo "========== ROUTE SCRIPT =========="
cat /usr/local/sbin/lab-pub-routes
```

Expected route:

```text
172.19.0.0/16 via 10.100.10.100 dev ct-lab-pub
```

Expected route lookup characteristics:

```text
via 10.100.10.100 dev ct-lab-pub src 10.100.10.10
```

The exact output may include additional kernel route attributes.

## 5. Operational notes

- The correct LAB-PUB unit is `ctunnel-engine@lab-pub.service`.
- Keep the LAB-PUB GRETAP transport selection unchanged.
- The route hook runs whenever the LAB-PUB userspace engine starts.
- The route script waits for `ct-lab-pub` before installing the route.
- The route uses `10.100.10.100` as its next hop.
- The immediate route installation does not restart the tunnel.
- Do not modify LAB LAN interfaces, default gateways, Proxmox networking, or PUB Docker networking through this procedure.
- Do not change the LAB-HUB WireGuard configuration or its route as part of this procedure.

This runbook manages only the LAB-PUB route and its systemd integration inside the LAB LXC.
