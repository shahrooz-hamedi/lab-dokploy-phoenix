# HUB Tunnel Host Setup and Verification

This runbook documents the HUB host routes and the verification
of SIP/RTP forwarding through the HUB-LAB tunnel.

## 1. Architecture

| Component | Responsibility |
|---|---|
| HUB host | Routes LAB/PUB networks through the tunnel container |
| HUB tunnel container | Routes LAB networks through `ct-hub-lab` |
| HUB tunnel container | DNATs provider SIP/RTP traffic to FreePBX |
| HUB tunnel container | MASQUERADEs FreePBX-originated provider traffic |
| LAB LXC | Routes provider destinations through `ct-lab-hub` |
| LAB OpenWrt | Routes provider destinations to LAB LXC |
| FreePBX | `192.168.11.30` |

The HUB tunnel container has:

| Item | Value |
|---|---|
| Container | `hub-tunnel-kflvaq-tunnel-1` |
| Docker bridge | `br-xui6` |
| Container IPv4 | `172.23.0.100` |
| Docker gateway | `172.23.0.1` |
| HUB-LAB interface | `ct-hub-lab` |
| HUB-LAB address | `10.100.30.100` |
| LAB-LXC peer | `10.100.30.10` |

## 2. Install persistent HUB host routes

Run on the HUB host as root.

```bash
set -eu

cd /etc/dokploy/compose/hub-tunnel-kflvaq/code

install -o root -g root -m 0755 \
  HUB/tunnel/hub-host-routes.sh \
  /usr/local/sbin/hub-host-routes

install -o root -g root -m 0644 \
  HUB/tunnel/hub-host-routes.service \
  /etc/systemd/system/hub-host-routes.service

systemctl daemon-reload
systemctl enable hub-host-routes.service
systemctl restart hub-host-routes.service

systemctl --no-pager --full status hub-host-routes.service
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

## 4. HUB tunnel container forwarding

The container image installs:

- `/usr/local/sbin/hub-lab-routes`
- `/usr/local/sbin/hub-sip-forwarding`

Both scripts are attached to `ctunnel@hub-lab.service`.

The route script runs first. The SIP forwarding script runs second.

No separate host-level SIP DNAT or SNAT service is required.

The container forwarding configuration is:

| Traffic | Action |
|---|---|
| UDP 5060 from `185.98.113.196/32` | DNAT to `192.168.11.30:5060` |
| UDP 10000–10019 from `185.98.113.208/29` | DNAT to FreePBX |
| UDP 10000–10019 from `185.98.113.216/29` | DNAT to FreePBX |
| UDP 10000–10019 from `185.98.113.120/29` | DNAT to FreePBX |
| FreePBX traffic to provider networks | MASQUERADE through `eth0` |

RTP destination ports are preserved.

TCP 5061 is not part of this configuration.

## 5. Verify the running container

Run on the HUB host:

```bash
set -eu

C="hub-tunnel-kflvaq-tunnel-1"

docker inspect "$C" >/dev/null

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

Expected IPv4 forwarding:

```text
net.ipv4.ip_forward = 1
```

## 6. Verify Docker port publication

```bash
C="hub-tunnel-kflvaq-tunnel-1"

echo "========== SIP UDP =========="
docker port "$C" 5060/udp

echo
echo "========== RTP UDP =========="
docker port "$C" 10000/udp
docker port "$C" 10019/udp
```

Expected published ports:

- UDP 5060
- UDP 10000 through UDP 10019

TCP 5061 must not be published.

## 7. Verify Docker bridge egress NAT

The container uses `xui-ipv6-egress` for its Docker-facing interface.

Inspect the network:

```bash
docker network inspect xui-ipv6-egress \
  --format 'Driver: {{.Driver}}
Options: {{json .Options}}'
```

Docker bridge IPv4 masquerading must be enabled. If the option
`com.docker.network.bridge.enable_ip_masquerade` is explicitly
`false`, investigate before testing outbound provider traffic.

## 8. Operational notes

- Do not add provider routes to the HUB host.
- Do not install SIP DNAT rules on the HUB host.
- Do not install another tunnel on the HUB host.
- Do not change HUB-PUB routing.
- Do not change HUB-LAB transport.
- The HUB container owns the SIP/RTP forwarding rules.
- The LAB LXC owns the provider destination routes.
- OpenWrt owns the routes from the LAB LAN to the LAB LXC.
