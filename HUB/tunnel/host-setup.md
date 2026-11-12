# HUB Tunnel Host — Installation, Recovery and Verification

This runbook installs and verifies persistent HUB host routes and the Docker networking required for SIP/RTP forwarding through the HUB-LAB tunnel.

## 1. Architecture

| Component | Responsibility |
|---|---|
| HUB host | Routes LAB/PUB networks through the tunnel container |
| HUB tunnel container | Routes LAB networks through `ct-hub-lab` |
| HUB tunnel container | DNATs provider SIP/RTP traffic to FreePBX |
| HUB tunnel container | MASQUERADEs FreePBX-originated provider traffic |
| HUB Docker bridge | Provides container-to-public-network NAT |
| LAB LXC | Routes provider destinations through `ct-lab-hub` |
| LAB OpenWrt | Routes provider destinations to LAB LXC |
| FreePBX | `192.168.11.30` |

HUB tunnel container:

| Item | Value |
|---|---|
| Container | `hub-tunnel-kflvaq-tunnel-1` |
| Docker network | `xui-ipv6-egress` |
| Docker bridge | `br-xui6` |
| Container IPv4 | `172.23.0.100` |
| Docker gateway | `172.23.0.1` |
| HUB-LAB interface | `ct-hub-lab` |
| HUB-LAB address | `10.100.30.100` |
| LAB peer | `10.100.30.10` |

## 2. Install or recover persistent HUB host routes

Run on the HUB host as root.

The repository is the source of truth for both installation files.

```bash
set -eu

cd /etc/dokploy/compose/hub-tunnel-kflvaq/code

test -f HUB/tunnel/hub-host-routes.sh
test -f HUB/tunnel/hub-host-routes.service

install -o root -g root -m 0755 \
  HUB/tunnel/hub-host-routes.sh \
  /usr/local/sbin/hub-host-routes

install -o root -g root -m 0644 \
  HUB/tunnel/hub-host-routes.service \
  /etc/systemd/system/hub-host-routes.service

systemctl daemon-reload
systemctl enable hub-host-routes.service
systemctl restart hub-host-routes.service

systemctl is-enabled hub-host-routes.service
systemctl is-active hub-host-routes.service
```

## 3. Verify HUB host routes

```bash
echo "========== HUB HOST ROUTES =========="
ip route show 172.19.0.0/16
ip route show 192.168.10.0/24
ip route show 192.168.11.0/24
ip route show 10.100.20.100/32
ip route show 10.100.30.10/32

echo
echo "========== FREEPBX ROUTE =========="
ip route get 192.168.11.30
```

Expected FreePBX route:

```text
192.168.11.30 via 172.23.0.100 dev br-xui6
```

## 4. Verify HUB tunnel container forwarding

The container image installs:

- `/usr/local/sbin/hub-lab-routes`
- `/usr/local/sbin/hub-sip-forwarding`

Both are attached to `ctunnel@hub-lab.service`, in this order:

1. `hub-lab-routes`
2. `hub-sip-forwarding`

No separate host-level SIP DNAT or SNAT service is required.

Expected forwarding configuration:

| Traffic | Action |
|---|---|
| UDP 5060 from `185.98.113.196/32` | DNAT to `192.168.11.30:5060` |
| UDP 10000–10019 from `185.98.113.208/29` | DNAT to FreePBX |
| UDP 10000–10019 from `185.98.113.216/29` | DNAT to FreePBX |
| UDP 10000–10019 from `185.98.113.120/29` | DNAT to FreePBX |
| FreePBX traffic to provider networks | MASQUERADE through `eth0` |

RTP destination ports are preserved. TCP 5061 is not part of this configuration.

## 5. Verify the running container

Run on the HUB host:

```bash
set -eu

C="hub-tunnel-kflvaq-tunnel-1"

docker inspect "$C" >/dev/null

echo "========== CONTAINER =========="
docker inspect -f \
  'Status={{.State.Status}} Image={{.Config.Image}}' "$C"

echo
echo "========== CONTAINER INTERFACES =========="
docker exec "$C" ip -br addr

echo
echo "========== CONTAINER ROUTES =========="
docker exec "$C" ip route

echo
echo "========== FREEPBX ROUTE =========="
docker exec "$C" ip route get 192.168.11.30

echo
echo "========== IPV4 FORWARDING =========="
docker exec "$C" sysctl net.ipv4.ip_forward

echo
echo "========== TUNNEL SERVICE =========="
docker exec "$C" systemctl is-active ctunnel@hub-lab.service
docker exec "$C" systemctl show ctunnel@hub-lab.service \
  -p ExecStartPost --value

echo
echo "========== NAT PREROUTING =========="
docker exec "$C" iptables -t nat -vnL PREROUTING

echo
echo "========== NAT POSTROUTING =========="
docker exec "$C" iptables -t nat -vnL POSTROUTING

echo
echo "========== FORWARD =========="
docker exec "$C" iptables -vnL FORWARD
```

Expected FreePBX route:

```text
192.168.11.30 dev ct-hub-lab src 10.100.30.100
```

Expected forwarding:

```text
net.ipv4.ip_forward = 1
```

The NAT and FORWARD listings must contain the provider-specific rules described in section 4.

## 6. Verify Docker port publication

```bash
C="hub-tunnel-kflvaq-tunnel-1"

echo "========== SIP UDP =========="
docker port "$C" 5060/udp

echo
echo "========== RTP UDP =========="
for PORT in $(seq 10000 10019); do
    docker port "$C" "${PORT}/udp"
done

echo
echo "========== TCP 5061 =========="
if docker port "$C" 5061/tcp | grep -q .; then
    echo "ERROR: TCP 5061 is published"
    exit 1
else
    echo "OK: TCP 5061 is not published"
fi
```

Expected: UDP 5060 and every UDP port from 10000 through 10019 are published on the HUB host.

## 7. Verify Docker bridge masquerading

Inspect the Docker network:

```bash
docker network inspect xui-ipv6-egress \
  --format 'Driver={{.Driver}} Options={{json .Options}}'
```

The bridge must be named `br-xui6`. Docker bridge IPv4 masquerading must not be explicitly disabled.

Inspect the actual HUB host NAT rules:

```bash
echo "========== DOCKER BRIDGE NAT =========="
iptables -t nat -S POSTROUTING | grep -E \
  '172\.23\.0\.0/16|br-xui6' || true

echo
echo "========== DOCKER FORWARD RULES =========="
iptables -S FORWARD | grep -E \
  'br-xui6|172\.23\.0\.0/16' || true
```

Confirm that Docker has a MASQUERADE rule for traffic from `172.23.0.0/16` leaving the bridge toward external networks.

If the network option explicitly disables masquerading, or the expected host NAT rule is absent, investigate Docker networking before testing provider traffic. Do not add duplicate NAT rules manually.

## 8. Operational rules

- Do not add provider routes to the HUB host.
- Do not install SIP DNAT/SNAT rules on the HUB host.
- Do not install another tunnel on the HUB host.
- Do not change HUB-PUB routing.
- Do not change HUB-LAB transport.
- The HUB host owns persistent routes to remote site networks.
- The HUB container owns SIP/RTP forwarding and provider-facing NAT.
- Docker owns container-to-public-network masquerading.
- The LAB LXC owns provider destination routes.
- OpenWrt owns routes from the LAB LAN to the LAB LXC.

Do not consider SIP/RTP end-to-end connectivity verified until an actual provider call and RTP media flow have been tested.