# Dograh — HUB Deployment

Dograh deployment for the HUB Dokploy server.

Git is the source of truth for the deployment. All application configuration, image customizations, and infrastructure-related changes must be maintained in this repository.

## Public endpoints

| Service | URL | Container port |
|---|---|---:|
| Dashboard | https://dograh.phoenix-rtp.com | 3010 |
| API | https://dograh.phoenix-rtp.com/api/v1 | 8000 |
| MinIO S3 API | https://storage-dograh.phoenix-rtp.com | 9000 |

All endpoints use the existing HUB Traefik instance and wildcard certificate.

Do not create another reverse proxy or Let's Encrypt resolver.

Do not expose MinIO console port 9001.

Do not activate public access until the trusted-IP restriction has been implemented in Traefik.

## Docker networks

### dokploy-network

Existing external Swarm overlay network.

| Service | Static IPv4 |
|---|---:|
| UI | 10.0.1.40 |
| MinIO | 10.0.1.41 |
| API | 10.0.1.45 |

Traefik reaches the three application services through this network.

The network is shared infrastructure. Never delete or recreate it as part of a Dograh deployment or reset.

### xui-ipv6-egress

Existing external bridge network.

| Service | IPv4 | IPv6 |
|---|---|---|
| UI | 172.23.0.40 | fd42:3a91:7c20:3::40 |
| MinIO | 172.23.0.41 | fd42:3a91:7c20:3::41 |
| API | 172.23.0.45 | fd42:3a91:7c20:3::45 |

The API uses the HUB xUI HTTP proxy at:

`http://172.23.0.10:8088`

The proxy provides outbound internet access through PUB. The expected public IPv4 egress address is:

`144.91.77.104`

The HUB's direct public IPv4 address is `193.151.155.226`. External HTTP/HTTPS requests from the API should use the proxy rather than direct HUB egress.

The UI and MinIO are attached to this network for their required network connectivity. They do not inherit the API's proxy environment configuration.

### dograh-internal

Private internal bridge network:

`172.30.0.0/16`

Attached services:

- PostgreSQL
- Redis
- MinIO
- MinIO initializer
- API

PostgreSQL and Redis are not attached to either shared network and have no published host ports.

The Compose `default` network declaration intentionally references the existing external `dokploy-network`. Do not remove it or allow Compose to create an unintended default network.

## Persistent volumes

| Volume | Purpose |
|---|---|
| dograh_postgres_data | PostgreSQL database |
| dograh_redis_data | Redis AOF data |
| dograh_minio_data | MinIO data |

Never use `docker compose down -v` casually. It removes persistent volumes.

A complete reset must explicitly verify the three Dograh volume names.

Never remove shared networks or resources belonging to other applications.

## PostgreSQL

Image: `pgvector/pgvector:pg17`

- Database user: `postgres`
- Database: `postgres`
- Internal hostname: `dograh-postgres`
- Port: `5432`

Only reachable through `dograh-internal`.

## Redis

Image: `redis:7`

- Internal hostname: `dograh-redis`
- Port: `6379`
- AOF persistence enabled
- Password authentication enabled

Only reachable through `dograh-internal`.

## MinIO

Image: `ghcr.io/dograh-hq/minio:2026.09.22`

- Bucket: `voice-audio`
- Internal endpoint: `http://minio:9000`
- Public S3 endpoint: `https://storage-dograh.phoenix-rtp.com`
- S3 API: `9000`
- Console: `9001`

Only port 9000 is routed through Traefik.

The MinIO root account is used only by the initializer.

Dograh uses a separate application account with the restricted policy in `config/minio-policy.json`.

The initializer preserves existing buckets, users and policies. It does not delete objects, reset existing passwords, or overwrite an existing bucket policy.

The MinIO service uses `MINIO_API_CORS_ALLOW_ORIGIN` for the Dograh UI origin. The initializer does not apply per-bucket CORS configuration.

## API image customization

The Dograh API is built from a locally maintained Dockerfile:

`HUB/dograh/api/Dockerfile`

The Dockerfile derives from a pinned upstream Dograh API image:

`ghcr.io/dograh-hq/dograh-api@sha256:715398c8376f8b6f04e46900d685693019fd3e016646c5df933358eb7d341fe0`

This digest was verified against the upstream image pulled on HUB on 2026-11-11.

The custom image applies one narrowly scoped source modification to enable proxy environment support for the Speechify TTS integration.

### Why the patch is needed

Python's `aiohttp.ClientSession()` defaults to:

```python
trust_env=False
```

With this default, aiohttp does not automatically use the `HTTP_PROXY`, `HTTPS_PROXY`, and `NO_PROXY` environment variables.

Dograh's Speechify integration creates its own aiohttp session in:

`/app/api/services/pipecat/service_factory.py`

The upstream implementation was:

```python
session = aiohttp.ClientSession()
```

The custom image changes it to:

```python
session = aiohttp.ClientSession(trust_env=True)
```

This allows the Speechify session to respect the proxy environment configured on the API container.

### Guarded patch

The patch script is maintained in:

`HUB/dograh/api/patch-speechify-proxy.py`

It checks the upstream source before modifying it.

Expected behavior:

- Exactly one original unpatched statement: apply the modification.
- Exactly one already-patched statement: accept the source as already patched.
- Missing or multiple matching statements: fail the image build.

This prevents silently modifying an unexpected upstream implementation.

The script does not install additional Python packages or modify Dograh's application configuration.

The Dockerfile restores the original `dograh` ownership and file permissions after patching.

### Build configuration

The API service in `docker-compose.yml` uses:

```yaml
api:
  image: hub-dograh-api:proxyfix-1
  build:
    context: ./api
    dockerfile: Dockerfile
```

The build context is relative to the directory containing the Compose file.

The `minio-init` service intentionally continues to use the upstream Dograh API image. It only uses the image's Python runtime to execute the MinIO initialization script and does not require the Speechify patch.

The UI continues to use the upstream Dograh UI image.

### Build and deployment

From the Dograh deployment directory:

```bash
docker compose config --quiet
docker compose build api
```

After a successful build, deploy the API through the existing Dokploy Compose application.

If deploying manually through Docker Compose:

```bash
docker compose up -d api
```

Do not use `docker compose down -v`.

Do not remove or recreate any persistent volume or external network.

### API patch verification

After deployment:

```bash
API="hub-dograh-5veknr-api-1"

docker exec "$API" python - <<'PY'
from pathlib import Path
import inspect
import aiohttp

path = Path("/app/api/services/pipecat/service_factory.py")
source = path.read_text()

patched = "session = aiohttp.ClientSession(trust_env=True)"
original = "session = aiohttp.ClientSession()"

assert source.count(patched) == 1, "Speechify proxy patch missing or duplicated"
assert source.count(original) == 0, "Unpatched Speechify session still exists"

default = inspect.signature(
    aiohttp.ClientSession
).parameters["trust_env"].default

assert default is False, "Unexpected aiohttp default"

print("PASS: Speechify session explicitly enables trust_env")
print("PASS: Original unpatched Speechify session is absent")
print(f"aiohttp default trust_env: {default}")
PY
```

The aiohttp default remains unchanged globally. Only the Speechify session explicitly enables environment proxy support.

## API outbound proxy configuration

The API Compose service defines both uppercase and lowercase proxy environment variables:

```yaml
HTTP_PROXY: http://172.23.0.10:8088
HTTPS_PROXY: http://172.23.0.10:8088
NO_PROXY: localhost,127.0.0.1,::1,postgres,redis,minio,api,dograh-api,dograh-postgres,dograh-redis,phoenix-rtp.com,192.168.10.0/24,192.168.11.0/24,10.100.0.0/16,172.19.0.0/16,172.23.0.0/16,172.30.0.0/16,10.0.1.0/24,fd42:3a91:7c20:2::/64,fd42:3a91:7c20:3::/64

http_proxy: http://172.23.0.10:8088
https_proxy: http://172.23.0.10:8088
no_proxy: localhost,127.0.0.1,::1,postgres,redis,minio,api,dograh-api,dograh-postgres,dograh-redis,phoenix-rtp.com,192.168.10.0/24,192.168.11.0/24,10.100.0.0/16,172.19.0.0/16,172.23.0.0/16,172.30.0.0/16,10.0.1.0/24,fd42:3a91:7c20:2::/64,fd42:3a91:7c20:3::/64
```

Keep the uppercase and lowercase values synchronized.

`NO_PROXY` is important. It prevents internal service communication and local network traffic from being sent through the external HTTP proxy.

### Proxy coverage and limitations

The API's outbound proxy configuration covers HTTP clients that honor proxy environment variables.

Verified behavior in the deployed environment:

- Python `urllib` uses the configured proxy.
- Python `requests` uses the configured proxy.
- HTTPX uses environment proxy configuration by default.
- `websockets` 17.4 supports automatic proxy discovery, and the shared Pipecat WebSocket connector does not override that default.
- The Speechify aiohttp session is explicitly configured with `trust_env=True` by the custom image.

Important limitations:

- aiohttp sessions created with the default `trust_env=False` do not automatically use the proxy.
- The Speechify patch does not modify every third-party provider integration.
- Raw TCP, UDP, SIP, RTP, and WebRTC media traffic are not tunneled by HTTP proxy environment variables.

Therefore, do not describe the HTTP proxy as a universal tunnel for all Dograh network traffic. Audit additional provider-specific clients if new integrations are enabled.

### External egress verification

Verify the proxy endpoint and public egress from the running API container:

```bash
API="hub-dograh-5veknr-api-1"

docker exec "$API" python - <<'PY'
import os
import urllib.request

expected_proxy = "http://172.23.0.10:8088"

for key in ("HTTP_PROXY", "HTTPS_PROXY", "http_proxy", "https_proxy"):
    value = os.environ.get(key)
    assert value == expected_proxy, f"{key} unexpected: {value!r}"
    print(f"PASS: {key}={value}")

print("Checking external egress...")
with urllib.request.urlopen("https://api.ipify.org", timeout=15) as response:
    public_ip = response.read().decode().strip()

print("Observed public egress IP:", public_ip)

assert public_ip == "144.91.77.104", (
    f"Expected PUB egress 144.91.77.104, got {public_ip}"
)

print("PASS: API external HTTP request exits through PUB")
PY
```

A successful result confirms that the tested HTTP request exits through PUB. It does not independently prove that every provider-specific client uses the proxy.

## API and S3

The API uses:

- PostgreSQL and Redis through `dograh-internal`.
- MinIO internally for native MinIO configuration.
- The public HTTPS S3 endpoint for S3 operations and presigned URLs.

Do not replace `S3_ENDPOINT_URL` with the internal MinIO endpoint.

Do not disable TLS verification.

The API health check is:

`http://127.0.0.1:8000/api/v1/health`

## UI

Image: `ghcr.io/dograh-hq/dograh-ui:latest`

- Container port: `3010`
- Backend URL: `http://dograh-api:8000`

The UI and API communicate over `dokploy-network`.

## Dokploy domains

Configure these three domains:

| Domain | Service | Port | Path |
|---|---|---:|---|
| dograh.phoenix-rtp.com | ui | 3010 | / |
| dograh.phoenix-rtp.com | api | 8000 | /api/v1 |
| storage-dograh.phoenix-rtp.com | minio | 9000 | / |

Use HTTPS and the existing wildcard certificate.

The API path must be preserved. Do not configure StripPrefix.

Do not route MinIO port 9001.

Do not activate public access until the trusted-IP restriction has been implemented in Traefik.

## Environment variables

Configure secrets in Dokploy, not in Git.

Required:

- POSTGRES_PASSWORD
- REDIS_PASSWORD
- MINIO_ROOT_USER
- MINIO_ROOT_PASSWORD
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
- OSS_JWT_SECRET
- TELEPHONY_WS_TOKEN_SECRET

Optional:

- ENABLE_SIGNUP
- ENABLE_TELEMETRY
- DOGRAH_DEVOPS_SECRET

Use unique, newly generated secrets for a fresh deployment.

Use URL-safe passwords for values embedded in connection URLs.

Never commit real credentials.

## Deployment and verification order

1. Verify the external Docker networks and static addresses.
2. Verify the three persistent volume names.
3. Validate the Compose file using `docker compose config --quiet`.
4. Review and commit deployment changes to Git.
5. Verify the custom API Dockerfile and guarded patch script are present in the repository.
6. Configure the Dokploy Compose application to use the repository and the correct Compose file.
7. Confirm Dokploy builds the API image from `HUB/dograh/api/Dockerfile`.
8. Configure environment variables in Dokploy.
9. Build the custom API image.
10. Deploy without enabling public access.
11. Verify PostgreSQL and Redis health.
12. Verify MinIO health and initializer completion.
13. Verify the API health check.
14. Verify the Speechify proxy patch in the running API container.
15. Verify external API HTTP egress through PUB (`144.91.77.104`).
16. Verify UI health and API connectivity.
17. Verify S3 upload, download and presigned URLs.
18. Implement Traefik trusted-IP restrictions.
19. Only then enable public DNS/routing.
20. Integrate HUB Speaches after standalone Dograh works.
21. Integrate LAB FreePBX after HUB integration is verified.

## Safety

Never remove or recreate:

- `dokploy-network`
- `xui-ipv6-egress`
- Dokploy
- Traefik
- Existing wildcard certificates
- Other application volumes or networks

Do not publish PostgreSQL, Redis or MinIO console ports.

Do not use `docker compose down -v` as a routine deployment command.

Do not make undocumented changes inside running containers. All persistent application changes must be maintained in this repository and deployed through Dokploy.

Keep Git as the source of truth.

## Generate secrets

Generate secrets locally. Examples:

```bash
openssl rand -hex 32
openssl rand -hex 10
```

Store the generated values in Dokploy environment variables. Never commit real credentials.