# Paperclip — Post-Deploy Commands

## 1. Get Paperclip container

```bash
PC=$(docker ps --filter "name=paperclip" --format '{{.Names}}' | grep -v postgres | head -1)
echo "$PC"
```

## 2. Verify Paperclip + Hermes

```bash
docker exec "$PC" hermes --version
```

Expected:

```text
Hermes Agent v0.19.0
```

## 3. Onboard Paperclip

```bash
docker exec -it --user node "$PC" sh -lc '
/app/cli/node_modules/.bin/tsx /app/cli/src/index.ts onboard
'
```

When prompted:

```text
◆ PostgreSQL connection string
│ postgres://user:pass@localhost:5432/paperclip
```

Enter the actual Compose database connection:

```text
postgres://paperclip:YOUR_POSTGRES_PASSWORD@paperclip-postgres:5432/paperclip
```

Use the **same `POSTGRES_PASSWORD` configured in Dokploy**.

## 4. Connect CLI as board

```bash
docker exec -it "$PC" sh -lc '
/app/cli/node_modules/.bin/tsx /app/cli/src/index.ts \
  connect \
  --persona board \
  --api-base https://paperclip.phoenix-rtp.com
'
```

Expected:

```text
Connected profile 'default' as board.
```

## 5. Create CEO

```bash
docker exec "$PC" sh -lc '
CLI=/app/cli/node_modules/.bin/tsx
APP=/app/cli/src/index.ts

$CLI "$APP" agent create \
  --company-id f9a66595-b99a-4296-b087-d78e176b8f35 \
  --profile default \
  --payload-json '"'"'{
    "name": "CEO",
    "role": "ceo",
    "title": "Chief Executive Officer",
    "icon": "crown",
    "adapterType": "hermes_local",
    "adapterConfig": {
      "persistSession": true,
      "quiet": true,
      "timeoutSec": 1800,
      "graceSec": 10
    },
    "onboardingFirstAgent": true
  }'"'"' \
  --json
'
```

## 6. Verify CEO

```bash
docker exec "$PC" sh -lc '
CLI=/app/cli/node_modules/.bin/tsx
APP=/app/cli/src/index.ts

$CLI "$APP" agent list \
  --company-id f9a66595-b99a-4296-b087-d78e176b8f35 \
  --json
'
```

Expected:

```text
role: ceo
status: idle
adapterType: hermes_local
heartbeat.enabled: false
```

## Canonical model references

Paperclip/Hermes:

```text
openrouter/bifrost/main-free
```

OpenCode:

```text
bifrost/openrouter/bifrost/main-free
```