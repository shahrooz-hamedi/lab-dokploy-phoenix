# Dograh - LAB Deployment

Self-hosted Dograh deployment on LAB Dokploy.

## Endpoints

- UI/API: https://dograh.phoenix-rtp.com
- S3 API: https://storage-dograh.phoenix-rtp.com

LAN/VPN-only access.

## Infrastructure

- Deployment: Dokploy Docker Compose
- Reverse proxy: Existing Dokploy Traefik
- PostgreSQL: pgvector/pgvector
- Redis: Redis 7
- Object storage: Self-hosted MinIO
- Application: Dograh API + UI

## Networks

- dokploy-network: Traefik and application ingress
- dograh-internal: PostgreSQL, Redis and private application traffic

## Environment and secrets

All environment variables and secrets are managed through Dokploy.

Use `.env.example` as the reference for the required variables.

Never commit actual secrets or `.env` files.

### Generating secrets

Generate strong random secrets using OpenSSL.

Examples:

PostgreSQL password:

    openssl rand -hex 32

Redis password:

    openssl rand -hex 32

MinIO root password:

    openssl rand -hex 32

MinIO application access key:

    openssl rand -hex 10

MinIO application secret:

    openssl rand -hex 32

Dograh JWT secret:

    openssl rand -hex 48

Telephony WebSocket token secret:

    openssl rand -hex 32

MinIO root username:

    dograh-admin

Generate the values on a trusted local machine and enter them
directly into the Dokploy Environment section.

Do not commit generated secrets.

## Deployment

1. Create a Docker Compose application in Dokploy.
2. Connect the infrastructure Git repository.
3. Select the production branch.
4. Set the Compose file path to:

       applications/dograh/compose.yaml

5. Configure environment variables in Dokploy.
6. Configure the three domains in the Domains section.
7. Deploy the application.

## Domains

Configure the following domains through Dokploy.

| Host | Path | Service | Container Port |
|---|---|---|---|
| dograh.phoenix-rtp.com | / | ui | 3010 |
| dograh.phoenix-rtp.com | /api | api | 8000 |
| storage-dograh.phoenix-rtp.com | / | minio | 9000 |

Enable HTTPS for all three domains.

Use the existing wildcard certificate loaded by Traefik.
Do not configure a new Let's Encrypt resolver.

For the API domain, do not enable Strip Path.
Dograh expects the original `/api` path.

## Storage

MinIO bucket:

    voice-audio

The bucket must remain private.

Dograh uses S3-compatible credentials and presigned URLs.

The application account must have restricted permissions
to the `voice-audio` bucket.

Configuration files:

- config/minio-policy.json
- config/minio-cors.json

## Initial MinIO provisioning

After MinIO is running, create:

1. Private bucket `voice-audio`.
2. Dedicated application user using the AWS credentials.
3. Policy defined in `config/minio-policy.json`.
4. Bucket CORS configuration from `config/minio-cors.json`.

Never enable anonymous bucket access.

MinIO root credentials are only for administration.

## Initial account setup

Keep ENABLE_SIGNUP=true for initial administrator registration.

After creating the first administrator:

1. Change ENABLE_SIGNUP to false in Dokploy.
2. Redeploy the application.

## Backup

Back up:

- PostgreSQL volume
- MinIO volume
- Protected Dokploy environment variables

Redis uses AOF persistence but should be treated primarily
as application state/cache rather than the authoritative data store.

Never delete persistent volumes during application upgrades.