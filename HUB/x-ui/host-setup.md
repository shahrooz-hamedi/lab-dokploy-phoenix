# HUB — 3x-ui Host DNS Setup

## 1. Configure systemd-resolved

Create the HUB DNS configuration:

```bash
mkdir -p /etc/systemd/resolved.conf.d

cat > /etc/systemd/resolved.conf.d/99-hub-dns.conf <<'EOF'
[Resolve]
DNS=172.23.0.10
Domains=~.
FallbackDNS=
DNSStubListenerExtra=172.23.0.1
EOF
```

**Configuration purpose:**
- `DNS=172.23.0.10`: Use the HUB 3x-ui container as the upstream DNS resolver.
- `Domains=~.`: Route all DNS queries through this DNS server.
- `FallbackDNS=`: Disable fallback DNS servers.
- `DNSStubListenerExtra=172.23.0.1`: Listen for DNS requests on the HUB Docker bridge gateway so Docker containers can resolve external domains through systemd-resolved.

## 2. Restart the resolver

```bash
systemctl restart systemd-resolved
```

## 3. Verify DNS configuration and listeners

```bash
resolvectl status

echo
echo "========== DNS LISTENERS =========="
ss -lnutp | grep -E '(:53[[:space:]]|:53$)'
```

Confirm:

- Global DNS Server: `172.23.0.10`
- Global DNS Domain: `~.`
- DNS listener: `172.23.0.1:53` (UDP and TCP)

## 4. Verify DNS resolution

Test UDP and TCP directly against 3x-ui:

```bash
dig @172.23.0.10 example.com A +time=3 +tries=1
dig @172.23.0.10 example.com A +tcp +time=3 +tries=1
```

Both must return `status: NOERROR`.

Test the Docker bridge gateway DNS listener:

```bash
dig @172.23.0.1 example.com A +time=3 +tries=1
dig @172.23.0.1 example.com A +tcp +time=3 +tries=1
```

Both must return `status: NOERROR`.

Test normal host DNS resolution:

```bash
getent ahostsv4 example.com
resolvectl query example.com
```

Both commands must return valid DNS results without specifying a DNS server.

## 5. Verify Docker container DNS resolution

Test the Docker embedded DNS resolver from a running Dokploy container:

```bash
DOK=$(docker ps -q \
  --filter label=com.docker.swarm.service.name=dokploy | head -n1)

test -n "$DOK"

docker exec "$DOK" node -e '
require("node:dns").promises.lookup("api.github.com", {family:4})
  .then(x => console.log("PASS:", x))
  .catch(e => { console.error("FAIL:", e); process.exit(1); });
'
```

Expected: `PASS` followed by a valid IPv4 address.

## 6. Verify persistence

Restart systemd-resolved:

```bash
systemctl restart systemd-resolved
```

Verify the configuration and DNS listener again:

```bash
resolvectl status

ss -lnutp | grep -E '172\.23\.0\.1:53'
```

Repeat the DNS tests:

```bash
dig @172.23.0.1 example.com A +time=3 +tries=1
getent ahostsv4 example.com
```

Confirm that:
- `172.23.0.10` remains the global upstream DNS server.
- `172.23.0.1:53` listens on UDP and TCP.
- Host DNS resolution succeeds.
- Docker container DNS resolution succeeds.

**Expected result:** HUB uses the 3x-ui container (`172.23.0.10`) as its upstream DNS resolver through systemd-resolved. The resolver additionally listens on the Docker bridge gateway (`172.23.0.1:53`), allowing Docker containers, including Dokploy, to resolve external domains through Docker's embedded DNS resolver without publishing DNS ports publicly.