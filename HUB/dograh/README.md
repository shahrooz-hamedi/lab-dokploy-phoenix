# Dograh — HUB Deployment

Dograh deployment for the HUB Dokploy server.

## Public endpoints

| Service | URL | Container port |
|---|---|---:|
| Dashboard | https://dograh.phoenix-rtp.com | 3010 |
| API | https://dograh.phoenix-rtp.com/api/v1 | 8000 |
| MinIO S3 API | https://storage-dograh.phoenix-rtp.com | 9000 |

All endpoints use the existing HUB Traefik instance and wildcard certificate.
Do not create another reverse proxy or Let's Encrypt resolver.

Do not expose MinIO console port 9001.

## Docker networks

### dokploy-network

Existing external Swarm overlay network.

| Service | Static IPv4 |
|---|---:|
| UI | 10.0.1.40 |
| MinIO | 10.0.1.41 |
| API | 10.0.1.45 |

Traefik reaches the three application services through this network.

The network is shared infrastructure. Never delete or recreate it as part
of a Dograh deployment or reset.

### xui-ipv6-egress

Existing external bridge network.

| Service | IPv4 | IPv6 |
|---|---|---|
| UI | 172.23.0.40 | fd42:3a91:7c20:3::40 |
| MinIO | 172.23.0.41 | fd42:3a91:7c20:3::41 |
| API | 172.23.0.45 | fd42:3a91:7c20:3::45 |

This network provides connectivity to the HUB xUI egress environment.
No custom proxy, TUN routing, or application-specific outbound routing is
configured in this initial deployment.

### dograh-internal

Private internal bridge network:

172.30.0.0/16

Attached services:

- PostgreSQL
- Redis
- MinIO
- MinIO initializer
- API

PostgreSQL and Redis are not attached to either shared network and have
no published host ports.

The Compose `default` network declaration intentionally references the
existing external `dokploy-network`. Do not remove it or allow Compose to
create an unintended default network.

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

Image: pgvector/pgvector:pg17

- Database user: postgres
- Database: postgres
- Internal hostname: dograh-postgres
- Port: 5432

Only reachable through dograh-internal.

## Redis

Image: redis:7

- Internal hostname: dograh-redis
- Port: 6379
- AOF persistence enabled
- Password authentication enabled

Only reachable through dograh-internal.

## MinIO

Image: ghcr.io/dograh-hq/minio:2026.09.22

- Bucket: voice-audio
- Internal endpoint: http://minio:9000
- Public S3 endpoint: https://storage-dograh.phoenix-rtp.com
- S3 API: 9000
- Console: 9001

Only port 9000 is routed through Traefik.

The MinIO root account is used only by the initializer.
Dograh uses a separate application account with the restricted policy
in config/minio-policy.json.

The initializer preserves existing buckets, users and policies. It does
not delete objects, reset existing passwords, or overwrite an existing
bucket policy.

The MinIO service uses MINIO_API_CORS_ALLOW_ORIGIN for the Dograh UI origin.
The initializer does not apply per-bucket CORS configuration.

## API and S3

The API uses:

- PostgreSQL and Redis through dograh-internal
- MinIO internally for native MinIO configuration
- The public HTTPS S3 endpoint for S3 operations and presigned URLs

Do not replace S3_ENDPOINT_URL with the internal MinIO endpoint.
Do not disable TLS verification.

The API health check is:

http://127.0.0.1:8000/api/v1/health

## UI

Image: ghcr.io/dograh-hq/dograh-ui:latest

- Container port: 3010
- Backend URL: http://dograh-api:8000

The UI and API communicate over dokploy-network.

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

Do not activate public access until the trusted-IP restriction has been
implemented in Traefik.

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
2. Validate the Compose file.
3. Commit deployment changes to Git.
4. Create/configure the Dokploy Compose application.
5. Configure environment variables.
6. Deploy without enabling public access.
7. Verify PostgreSQL and Redis health.
8. Verify MinIO health and initializer completion.
9. Verify API health.
10. Verify UI health and API connectivity.
11. Verify S3 upload, download and presigned URLs.
12. Implement Traefik trusted-IP restrictions.
13. Only then enable public DNS/routing.
14. Integrate HUB Speaches after standalone Dograh works.
15. Integrate LAB FreePBX after HUB integration is verified.

## Safety

Never remove or recreate:

- dokploy-network
- xui-ipv6-egress
- Dokploy
- Traefik
- Existing wildcard certificates
- Other application volumes or networks

Do not publish PostgreSQL, Redis or MinIO console ports.

Keep all deployment changes in this repository and use Git as
the source of truth.


### Generate secrets

Use openssl rand -hex 32 and openssl rand -hex 10
