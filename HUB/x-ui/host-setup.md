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
EOF
```

## 2. Restart the resolver

```bash
systemctl restart systemd-resolved
```

## 3. Verify DNS configuration

```bash
resolvectl status
```

Confirm the global settings show:

- DNS Server: `172.23.0.10`
- DNS Domain: `~.`

## 4. Verify DNS resolution

Test UDP and TCP directly against 3x-ui:

```bash
dig @172.23.0.10 example.com A +time=3 +tries=1
dig @172.23.0.10 example.com A +tcp +time=3 +tries=1
```

Both must return `status: NOERROR`.

Test normal host DNS resolution:

```bash
getent ahostsv4 example.com
resolvectl query example.com
```

Both commands must return valid DNS results without specifying a DNS server.

## 5. Verify persistence

```bash
systemctl restart systemd-resolved
resolvectl status
getent ahostsv4 example.com
```

Confirm that `172.23.0.10` remains the global DNS server and hostname resolution succeeds.

**Expected result:** HUB uses the 3x-ui container (`172.23.0.10`) as its upstream DNS resolver through systemd-resolved.