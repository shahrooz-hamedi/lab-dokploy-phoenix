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

- `dokploy-network`: Traefik and application ingress
- `dograh-internal`: PostgreSQL, Redis, and private application traffic

## Repository structure

All Dograh deployment files are maintained in the infrastructure repository.

```text
LAB/
  dograh/
    README.md
    docker-compose.yml
    minio-init.py
    config/
      minio-policy.json
      minio-cors.json
```

## Environment and secrets

All environment variables and secrets are managed through Dokploy.

Use the environment template as the reference for required variables.

Never commit actual secrets or `.env` files.

### Generating secrets

Generate strong random secrets using OpenSSL.

PostgreSQL password:

```bash
openssl rand -hex 32
```

Redis password:

```bash
openssl rand -hex 32
```

MinIO root password:

```bash
openssl rand -hex 32
```

MinIO application access key:

```bash
openssl rand -hex 10
```

MinIO application secret:

```bash
openssl rand -hex 32
```

Dograh JWT secret:

```bash
openssl rand -hex 48
```

Telephony WebSocket token secret:

```bash
openssl rand -hex 32
```

MinIO root username:

```text
dograh-admin
```

Generate values on a trusted local machine and enter them directly into the Dokploy Environment section.

Do not commit generated secrets.

## Deployment

1. Create a Docker Compose application in Dokploy.
2. Connect the infrastructure Git repository.
3. Select the production branch.
4. Set the Compose file path to:

   ```text
   LAB/dograh/docker-compose.yml
   ```

5. Configure the environment variables in Dokploy.
6. Configure the three domains in the Domains section.
7. Deploy the application.

## Domains

Configure the following domains through Dokploy.

| Host | Path | Service | Container Port |
|---|---|---|---|
| dograh.phoenix-rtp.com | `/` | ui | 3010 |
| dograh.phoenix-rtp.com | `/api/v1` | api | 8000 |
| storage-dograh.phoenix-rtp.com | `/` | minio | 9000 |

Enable HTTPS for all three domains.

Use the existing wildcard certificate loaded by Traefik.

Do not configure a new Let's Encrypt resolver.

For the API domain, do not enable Strip Path.

Dograh expects the original `/api` path.

## Storage

MinIO bucket:

```text
voice-audio
```

The bucket must remain private.

Dograh uses S3-compatible credentials and presigned URLs.

The application account has restricted permissions to the `voice-audio` bucket.

Configuration files:

- `config/minio-policy.json`
- `config/minio-cors.json`

Never enable anonymous bucket access.

MinIO root credentials are only for administration and automatic provisioning.

## Automatic MinIO provisioning

MinIO provisioning is automated through the `minio-init` one-shot Compose service.

During initial deployment, and whenever the initialization service is recreated, it:

1. Waits for MinIO to become healthy.
2. Creates the private `voice-audio` bucket if necessary.
3. Creates the dedicated application account if necessary.
4. Creates the least-privilege application policy if necessary.
5. Attaches the policy to the application account.
6. Applies the bucket CORS configuration.
7. Removes any existing anonymous bucket policy.
8. Verifies application bucket access.

The Dograh API starts only after successful initialization.

The initialization service uses the existing Dograh API image and its installed Python SDK dependencies.

It does not require MinIO Client or an additional image.

Existing application users are not recreated or silently assigned new passwords.

Existing policies are not automatically overwritten.

Changes to an existing policy require an explicit policy update procedure.

A completed one-shot initialization container is not guaranteed to execute again on every unchanged Compose redeployment.

## Initial account setup

Keep:

```dotenv
ENABLE_SIGNUP=true
```

for initial administrator registration.

After creating the first administrator:

1. Change `ENABLE_SIGNUP` to `false` in Dokploy.
2. Redeploy the application.

## Backup

Back up:

- PostgreSQL volume
- MinIO volume
- Protected Dokploy environment variables

Redis uses AOF persistence but should be treated primarily as application state/cache rather than the authoritative data store.

Never delete persistent volumes during application upgrades.