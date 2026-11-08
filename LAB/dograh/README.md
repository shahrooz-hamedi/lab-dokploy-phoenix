# Dograh — LAB Deployment

This repository directory contains the Docker Compose deployment for Dograh
on the LAB Dokploy server.

The deployment includes:

- Dograh API
- Dograh UI
- PostgreSQL with pgvector
- Redis with AOF persistence
- MinIO S3-compatible object storage
- A one-shot MinIO initialization service

## 1. Public endpoints

| Service | URL |
|---|---|
| Dograh application | https://dograh.phoenix-rtp.com |
| Dograh API | https://dograh.phoenix-rtp.com/api/v1 |
| MinIO S3 API | https://storage-dograh.phoenix-rtp.com |

The application and storage endpoints use the existing LAB Dokploy Traefik
deployment and the existing wildcard TLS certificate.

Do not configure a separate Let's Encrypt resolver for this stack.

## 2. Dokploy routing

Configure the following domains in the Dokploy application.

| Domain | Path | Target service | Target port |
|---|---|---|---:|
| dograh.phoenix-rtp.com | `/api/v1` | API | 8000 |
| dograh.phoenix-rtp.com | `/` | UI | 3010 |
| storage-dograh.phoenix-rtp.com | `/` | MinIO | 9000 |

All routes must use HTTPS.

The API route must preserve the `/api/v1` prefix. Do not attach a
StripPrefix middleware to this route.

MinIO's S3 API is exposed through Traefik on port 9000.

MinIO's administrative console on port 9001 must not be published or routed.

Use the existing wildcard certificate. Do not create another certificate
resolver or modify the shared Traefik deployment for this application.

## 3. Docker network architecture

The stack uses two Docker networks.

### dokploy-network

This is the existing external Dokploy network.

The following services join it:

- UI
- API
- MinIO

Traefik reaches the UI, API, and MinIO through this network.

The network is shared infrastructure. It is not owned by Dograh and must
never be deleted as part of a Dograh reset.

### dograh-internal

This is a private, internal Docker bridge network.

The following services join it:

- PostgreSQL
- Redis
- MinIO
- MinIO initializer
- API

Its subnet is:

`172.30.0.0/16`

PostgreSQL and Redis are not attached to `dokploy-network` and have no
published host ports.

The UI reaches the API through the `dokploy-network` service DNS name.

## 4. Persistent resources

The Compose deployment creates these named volumes:

| Volume | Purpose |
|---|---|
| `dograh_postgres_data` | PostgreSQL database |
| `dograh_redis_data` | Redis AOF data |
| `dograh_minio_data` | MinIO objects and internal metadata |

The Dograh private network is:

`dograh-internal`

The external shared network is:

`dokploy-network`

A complete Dograh reset may remove the three Dograh volumes and the private
Dograh network. It must not remove the shared `dokploy-network`.

Never use `docker compose down -v` casually. It deletes the persistent
volumes associated with the Compose project.

For an intentional complete Dograh reset, verify the exact volume names
before removing them.

## 5. PostgreSQL

Image:

`pgvector/pgvector:pg17`

Database:

- User: `postgres`
- Database: `postgres`
- Internal hostname: `dograh-postgres`
- Port: `5432`

The database password is supplied through the Dokploy environment.

PostgreSQL is reachable only through `dograh-internal`.

The health check uses `pg_isready`.

## 6. Redis

Image:

`redis:7`

Redis runs with:

- AOF persistence enabled
- Password authentication enabled
- Internal hostname: `dograh-redis`
- Port: `6379`

The Redis password is supplied through the Dokploy environment.

Redis is reachable only through `dograh-internal`.

## 7. MinIO object storage

Image:

`ghcr.io/dograh-hq/minio:2026.09.22`

Bucket:

`voice-audio`

Internal endpoint:

`http://minio:9000`

Public S3 endpoint:

`https://storage-dograh.phoenix-rtp.com`

MinIO listens internally on:

- S3 API: TCP 9000
- Console: TCP 9001

Only the S3 API is routed through Traefik.

The console is not publicly exposed.

### Storage backend selection

Dograh uses its S3-compatible filesystem implementation.

The API environment uses:

- `ENABLE_AWS_S3=true`
- `S3_BUCKET=voice-audio`
- `S3_REGION=us-east-1`
- `S3_ENDPOINT_URL=https://storage-dograh.phoenix-rtp.com`
- `S3_SIGNATURE_VERSION=s3v4`
- `S3_ADDRESSING_STYLE=path`

The public HTTPS endpoint is intentional.

The API uses the same endpoint for S3 operations and generated presigned
URLs. Do not replace it with the internal MinIO endpoint.

Do not disable TLS certificate verification.

The API must be able to reach the public storage hostname through the
configured network and Traefik routing. This must be verified after deployment.

Browsers access objects through presigned URLs. MinIO credentials are not
provided to browsers.

## 8. MinIO credentials and access policy

Two identities are used.

### MinIO root account

The root account is used only by the initialization service for MinIO
administration and bucket configuration.

Its credentials are provided through Dokploy environment variables:

- `MINIO_ROOT_USER`
- `MINIO_ROOT_PASSWORD`

Do not use root credentials in the Dograh API.

### Dograh application account

The API uses a separate S3-compatible application account:

- Access key: `AWS_ACCESS_KEY_ID`
- Secret key: `AWS_SECRET_ACCESS_KEY`

The application policy is defined in:

`config/minio-policy.json`

The policy grants access only to the `voice-audio` bucket and its objects.

The application account is not an administrator.

The application policy must not grant access to other buckets or MinIO
administrative operations.

## 9. Bucket CORS

Bucket CORS rules are defined in:

`config/minio-cors.json`

The allowed origin is:

`https://dograh.phoenix-rtp.com`

Allowed methods:

- GET
- PUT
- HEAD

The initializer applies the bucket CORS configuration using boto3 and reads
it back to verify that the configuration was accepted.

CORS is not a substitute for authentication. The bucket remains private.

## 10. MinIO initialization

The one-shot `minio-init` service uses the Dograh API image.

It runs:

`python /opt/minio-init.py`

The initializer:

1. Waits for MinIO to become available.
2. Creates the `voice-audio` bucket if it does not exist.
3. Checks for an existing bucket policy and stops if one is found.
4. Creates the Dograh application account if it does not exist.
5. Creates the restricted application policy if it does not exist.
6. Attaches the policy to the application account.
7. Applies the bucket CORS configuration.
8. Reads back and verifies the CORS configuration.
9. Verifies application-account access to the bucket.

The initializer must never:

- Delete the bucket or its objects.
- Make the bucket public.
- Reset an existing application user's password.
- Silently overwrite an existing application policy.
- Delete an existing bucket policy without review.

The API depends on successful completion of `minio-init`.

If initialization fails, the API must not start.

For a fresh installation, the Dograh volumes are empty and the initializer
creates the required bucket, account, policy, and CORS configuration.

If initialization is rerun after a partial deployment, inspect the logs
before changing existing credentials or policies.

## 11. API configuration

The API uses:

- PostgreSQL through `dograh-internal`
- Redis through `dograh-internal`
- MinIO through the S3-compatible public HTTPS endpoint
- MinIO's internal endpoint for its native MinIO-related configuration

The API health check calls:

`http://127.0.0.1:8000/api/v1/health`

The API uses one FastAPI worker initially.

Telephony and campaign components are enabled. Prometheus metrics and
Coturn are disabled in this initial deployment.

The telephony WebSocket token enforcement is enabled.

## 12. UI configuration

The UI uses the Dograh UI image:

`ghcr.io/dograh-hq/dograh-ui:latest`

It listens on port 3010.

Its backend URL is:

`http://api:8000`

The UI starts only after the API health check succeeds.

## 13. Environment variables and secrets

Production environment variables are configured in Dokploy.

The template file `sample.env.txt` contains placeholders only.

Required secrets include:

- `POSTGRES_PASSWORD`
- `REDIS_PASSWORD`
- `MINIO_ROOT_PASSWORD`
- `AWS_ACCESS_KEY_ID`
- `AWS_SECRET_ACCESS_KEY`
- `OSS_JWT_SECRET`
- `TELEPHONY_WS_TOKEN_SECRET`

Optional settings include:

- `DOGRAH_DEVOPS_SECRET`
- `ENABLE_SIGNUP`
- `ENABLE_TELEMETRY`

Use newly generated credentials for a fresh installation.

Do not commit production `.env` files or real credentials to Git.

Use URL-safe random passwords for database and Redis credentials because
they are embedded in connection URLs.

## 14. Deployment procedure

1. Confirm the old Dograh containers, volumes, and private network have been
   removed if performing a complete reset.
2. Confirm `dokploy-network` still exists.
3. Commit the repository files.
4. Create the new Dokploy Compose application from this directory.
5. Configure all required production environment variables in Dokploy.
6. Configure the three HTTPS domains and their target ports.
7. Deploy the application.
8. Verify PostgreSQL and Redis health.
9. Verify MinIO health.
10. Verify successful completion of `minio-init`.
11. Verify API health.
12. Verify UI health.
13. Test the public application and storage endpoints.
14. Test S3 upload, download, and presigned URL access.
15. Only after standalone Dograh works, integrate HUB Speaches.
16. Integrate LAB FreePBX after the HUB integration is verified.

## 15. Troubleshooting and safety

Do not modify shared Dokploy infrastructure to troubleshoot a Dograh-only
problem without first identifying the actual fault.

Do not remove:

- `dokploy-network`
- Dokploy
- Traefik
- The existing wildcard certificate
- Other application volumes or networks

Do not publish PostgreSQL, Redis, or the MinIO console.

Do not disable TLS verification for the public S3 endpoint.

Do not make the `voice-audio` bucket public.

Keep deployment changes in this repository and use Git as the source of
truth.