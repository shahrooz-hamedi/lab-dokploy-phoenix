# HUB Tunnel Host — Installation, Recovery and Verification

This runbook installs and verifies persistent HUB host routes and the Docker networking required for SIP/RTP forwarding through the HUB-LAB tunnel.

## 1. Architecture

| Component | Responsibility |
|---|---|
| HUB host | Routes LAB/PUB networks through the tunnel container |
| HUB tunnel container | Routes LAB networks through `ct-hub-lab` |
| HUB tunnel container | DNATs provider SIP/RTP traffic to FreePBX |
| HUB tunnel container | MASQUERADEs FreePBX-originated provider traffic |
| HUB Docker bridge | Provides container-to-public-network NAT and forwarding |
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

The repository is the source of truth.

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
echo "========== ROUTE SERVICE =========="
systemctl is-enabled hub-host-routes.service
systemctl is-active hub-host-routes.service

echo
echo "========== HUB HOST ROUTES =========="
ip route show 172.19.0.0/16
ip route show 192.168.10.0/24
ip route show 192.168.11.0/24
ip route show 10.100.20.100/32
ip route show 10.100.30.10/32

echo
echo "========== FREEPBX ROUTE =========="
ip route get 192.168.11.30

echo
echo "========== ROUTE SERVICE DEFINITION =========="
systemctl cat hub-host-routes.service
```

Expected FreePBX route:

```text
192.168.11.30 via 172.23.0.100 dev br-xui6
```

All five routes must use `172.23.0.100` through `br-xui6`.

## 4. Verify HUB tunnel container

```bash
set -eu

C="hub-tunnel-kflvaq-tunnel-1"

docker inspect "$C" >/dev/null

echo "========== CONTAINER =========="
docker inspect -f \
  'Status={{.State.Status}} Image={{.Config.Image}}' "$C"

echo
echo "========== INTERFACES =========="
docker exec "$C" ip -br addr

echo
echo "========== ROUTES =========="
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
```

Expected FreePBX route:

```text
192.168.11.30 dev ct-hub-lab src 10.100.30.100
```

Expected forwarding:

```text
net.ipv4.ip_forward = 1
```

The tunnel service must have both hooks:

1. `/usr/local/sbin/hub-lab-routes`
2. `/usr/local/sbin/hub-sip-forwarding`

Both must report successful execution.

## 5. Verify container SIP/RTP forwarding

```bash
C="hub-tunnel-kflvaq-tunnel-1"

echo "========== DNAT =========="
docker exec "$C" iptables -t nat -vnL PREROUTING

echo
echo "========== SNAT =========="
docker exec "$C" iptables -t nat -vnL POSTROUTING

echo
echo "========== FORWARD =========="
docker exec "$C" iptables -vnL FORWARD
```

Expected provider rules:

| Traffic | Action |
|---|---|
| UDP 5060 from `185.98.113.196/32` | DNAT to `192.168.11.30:5060` |
| UDP 10000–10019 from `185.98.113.208/29` | DNAT to `192.168.11.30` |
| UDP 10000–10019 from `185.98.113.216/29` | DNAT to `192.168.11.30` |
| UDP 10000–10019 from `185.98.113.120/29` | DNAT to `192.168.11.30` |
| FreePBX to provider networks | MASQUERADE through `eth0` |

RTP destination ports must be preserved.

TCP 5061 is not part of this configuration.

Rule counters indicate matching traffic, not merely rule existence. Zero counters do not invalidate an otherwise correctly installed rule.

## 6. Verify published ports

```bash
set -eu

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
if docker port "$C" 5061/tcp 2>/dev/null | grep -q .; then
    echo "ERROR: TCP 5061 is published"
    exit 1
else
    echo "OK: TCP 5061 is not published"
fi
```

Expected: UDP 5060 and every UDP port from 10000 through 10019 are published on the HUB host.

## 7. Verify Docker host forwarding and NAT

Inspect the Docker network:

```bash
docker network inspect xui-ipv6-egress \
  --format 'Id={{.Id}} Driver={{.Driver}} Internal={{.Internal}} Options={{json .Options}}'
```

Expected:
- Driver: `bridge`
- Internal: `false`
- Bridge name: `br-xui6`
- IPv4 masquerading must not be explicitly disabled.

Verify the actual host NAT rule:

```bash
echo "========== DOCKER BRIDGE MASQUERADE =========="
iptables -t nat -C POSTROUTING \
  -s 172.23.0.0/16 ! -o br-xui6 -j MASQUERADE \
  && echo "OK: Docker bridge MASQUERADE exists"
```

Verify Docker forwarding chains:

```bash
echo "========== HOST FORWARD =========="
iptables -vnL FORWARD

echo
echo "========== DOCKER-FORWARD =========="
iptables -vnL DOCKER-FORWARD

echo
echo "========== DOCKER PUBLISHED PORT RULES =========="
iptables -S DOCKER | grep '172.23.0.100'

echo
echo "========== BRIDGE NETFILTER =========="
sysctl net.bridge.bridge-nf-call-iptables
```

Required forwarding behavior:

- Host `FORWARD` chain jumps to `DOCKER-USER` and `DOCKER-FORWARD`.
- `DOCKER-FORWARD` accepts traffic entering from `br-xui6`.
- Docker `DOCKER` chain accepts the published UDP ports for `172.23.0.100`.
- Docker bridge MASQUERADE rule exists.
- `net.bridge.bridge-nf-call-iptables = 1`.

A host `FORWARD` policy of `DROP` is acceptable when Docker's forwarding chains contain the required ACCEPT rules.

Do not add manual firewall rules if any check fails. Investigate Docker's actual rules first.

## 8. End-to-end operational test

Configuration verification does not prove provider connectivity.

After the HUB and LAB checks pass:

1. Verify the provider SIP endpoint can reach FreePBX UDP 5060.
2. Place an outbound call through the provider.
3. Confirm two-way RTP media.
4. Inspect the container NAT/FORWARD counters during the call.
5. Confirm the public source address seen by the provider is the HUB public IPv4 address.

Do not treat successful route lookups, published ports, or installed firewall rules as proof of a successful call.

## 9. Operational rules

- Do not add provider routes to the HUB host.
- Do not install SIP DNAT/SNAT rules on the HUB host.
- Do not install another tunnel on the HUB host.
- Do not change HUB-PUB routing.
- Do not change HUB-LAB transport.
- HUB host owns persistent routes to remote site networks.
- HUB container owns SIP/RTP forwarding and provider-facing NAT.
- Docker owns container-to-public-network forwarding and masquerading.
- LAB LXC owns provider destination routes.
- LAB OpenWrt owns routes from the LAB LAN to the LAB LXC.