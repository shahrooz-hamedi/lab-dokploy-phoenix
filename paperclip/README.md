# Paperclip Deployment

## 1. CEO dashboard password hash

Generate the `HERMES_DASHBOARD_BASIC_AUTH_PASSWORD_HASH` value:

```bash
python3 -c 'import base64,hashlib,secrets; p="strongpassword"; salt=secrets.token_bytes(16); dk=hashlib.scrypt(p.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32,maxmem=0); print(f"scrypt$16384$8$1${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}")'
```

Set the result in Dokploy environment variables.

## 2. Deploy

Deploy the Compose application through Dokploy.

For a clean installation, use fresh volumes:

- `paperclip-data`
- `paperclip-postgres`
- `paperclip-hermes`

## 3. Verify containers

```bash
PC=$(docker ps --filter "name=paperclip" --format '{{.Names}}' | grep -v postgres | head -1)

docker exec "$PC" hermes --version

docker exec "$PC" sh -lc '
cat /home/node/.hermes/config.yaml
'
```

Expected Hermes version:

```text
0.21.5
```

Expected model:

```text
openrouter/bifrost/main-free
```

## 4. Onboard

```bash
docker exec -it --user node "$PC" sh -lc '
/app/cli/node_modules/.bin/tsx \
  /app/cli/src/index.ts \
  onboard
'
```

## 5. Board operator CLI token

```bash
docker exec -it "$PC" sh -lc '
/app/cli/node_modules/.bin/tsx \
  /app/cli/src/index.ts \
  connect \
  --persona board \
  --api-base https://paperclip.phoenix-rtp.com
'
```

## PostgreSQL

```text
postgresql://paperclip:${POSTGRES_PASSWORD}@paperclip-postgres:5432/paperclip
```

## Bifrost

Canonical model:

```text
openrouter/bifrost/main-free
```

OpenCode reference:

```text
bifrost/openrouter/bifrost/main-free
```