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

Expected version will depend on the Hermes version installed by the installer.

## 3. Install Hermes

Hermes is installed automatically by the Paperclip Dockerfile. If Hermes ever needs to be installed manually inside the container:

```bash
docker exec -it --user node "$PC" sh -lc '
curl -fsSL https://hermes-agent.nousresearch.com/install.sh \
  | bash -s -- --non-interactive
'
```

After installation:

```bash
docker exec "$PC" hermes --version
```

## 4. Update Hermes

Use Hermes' normal update mechanism:

```bash
docker exec "$PC" hermes update
```

Then verify:

```bash
docker exec "$PC" hermes --version
```

## 5. Run Hermes doctor

```bash
docker exec "$PC" hermes doctor
```

This verifies the Hermes Python environment, required packages, configuration, tools, and other runtime components.

## 6. Configure Mem0

Launch the Hermes Mem0 setup wizard:

```bash
docker exec -it "$PC" hermes mem0
```

For the self-hosted Mem0 server, use:

```text
Mem0 server URL:
https://mem0.phoenix-rtp.com
```

When prompted for the **Server API key**, enter the actual Mem0 API key.

For the Paperclip CEO:

```text
User identifier: paperclip-ceo
Agent identifier: paperclip-ceo
```

The wizard saves the Mem0 configuration to Hermes' persistent configuration and saves the API key to Hermes' `.env`.

Expected:

```text
✓ Mem0 server reachable at https://mem0.phoenix-rtp.com

Memory provider: mem0 (self-hosted)
Server: https://mem0.phoenix-rtp.com
Activation saved to config.yaml
Provider config saved
API key saved to .env

Start a new session to activate.
```

## 7. Start a new Hermes session

After Mem0 setup, start a new session so the configuration is activated:

```bash
docker exec -it "$PC" hermes
```

Test memory by asking Hermes to remember a unique test value, for example:

```text
Remember that the Paperclip CEO's Mem0 test identifier is paperclip-ceo-test-001.
```

Then ask:

```text
What is the Paperclip CEO's Mem0 test identifier?
```

The expected answer is:

```text
paperclip-ceo-test-001
```

## 8. Onboard Paperclip

```bash
docker exec -it --user node "$PC" sh -lc '
/app/cli/node_modules/.bin/tsx /app/cli/src/index.ts onboard
'
```

Enter the actual Compose database connection:

```text
postgres://paperclip:YOUR_POSTGRES_PASSWORD@paperclip-postgres:5432/paperclip
```

Use the **same `POSTGRES_PASSWORD` configured in Dokploy**.

## 9. Connect CLI as board

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

## 10. Create CEO

```bash
docker exec "$PC" sh -lc '
CLI=/app/cli/node_modules/.bin/tsx
APP=/app/cli/src/index.ts

$CLI "$APP" agent create \
  --company-id b3f346ee-b573-4f7e-bad9-12643b51a240 \
  --profile default \
  --payload-json '"'"'{
    "name": "Headman",
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

## 11. Verify CEO

```bash
docker exec "$PC" sh -lc '
CLI=/app/cli/node_modules/.bin/tsx
APP=/app/cli/src/index.ts

$CLI "$APP" agent list \
  --company-id b3f346ee-b573-4f7e-bad9-12643b51a240 \
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

## 12. Get the Board Key

Create a temporary/named board API key. Copy the returned token from the command output.

```bash
docker exec "$PC" sh -lc '
set -e

CLI=/app/cli/node_modules/.bin/tsx
ENTRY=/app/cli/src/index.ts
API=https://paperclip.phoenix-rtp.com

$CLI $ENTRY token board create \
  --name "lab-doctor-bridge-bootstrap" \
  --api-base "$API"
'
```

## 13. Create the Lab Doctor Task-Bridge Key

Paste the board token returned by Section 12 into `BOARD_KEY`.

```bash
BOARD_KEY='PASTE_THE_BOARD_TOKEN_HERE'
```

Then create the scoped task-bridge key for Lab Doctor:

```bash
curl -sS -f \
  -X POST \
  -H "Authorization: Bearer $BOARD_KEY" \
  -H "Content-Type: application/json" \
  "https://paperclip.phoenix-rtp.com/api/agents/7c013219-e5c7-4fcd-90b1-be942e872da8/keys" \
  -d '{
    "name": "Lab Doctor task bridge",
    "scope": {
      "kind": "task_bridge",
      "projectIds": [
        "d93dc06f-88d9-4a30-8121-a15537c35d7e",
        "36b9fa42-d801-42e4-b557-36040abf81f5"
      ]
    }
  }' | python3 -m json.tool
```

The resulting key is the **Lab Doctor `PAPERCLIP_BRIDGE_API_KEY`**.

Scope:

```text
Onboarding
Infrastructure
```

The key is **task-bridge scoped** and is not a normal full agent API key.

## 14. List Board Keys

After creating the bootstrap key, verify the board keys that currently exist:

```bash
docker exec "$PC" sh -lc '
CLI=/app/cli/node_modules/.bin/tsx
ENTRY=/app/cli/src/index.ts

$CLI $ENTRY token board list
'
```

Record the `keyId` for the temporary:

```text
lab-doctor-bridge-bootstrap
```

**Do not confuse the board key ID with the Lab Doctor task-bridge key.** They are different credentials.

## 15. Revoke the Bootstrap Board Key

After the Lab Doctor task-bridge key has been successfully created and stored, revoke the temporary bootstrap board key.

Set the key ID returned by Section 14:

```bash
BOARD_KEY_ID='PASTE_BOOTSTRAP_BOARD_KEY_ID_HERE'
```

Then:

```bash
docker exec "$PC" sh -lc '
CLI=/app/cli/node_modules/.bin/tsx
ENTRY=/app/cli/src/index.ts

$CLI $ENTRY token board revoke "$BOARD_KEY_ID"
'
```

Expected:

```json
{"ok":true,"keyId":"..."}
```

After revocation, the bootstrap board credential must no longer be usable.

## 16. Verify Board Keys After Cleanup

List the remaining board keys:

```bash
docker exec "$PC" sh -lc '
CLI=/app/cli/node_modules/.bin/tsx
ENTRY=/app/cli/src/index.ts

$CLI $ENTRY token board list
'
```

Confirm that:

```text
lab-doctor-bridge-bootstrap
```

is no longer present.

**Important:** this only lists/revokes **board API keys**. The Lab Doctor `task_bridge` key created in Section 13 is a separate agent key and is intentionally not revoked here.

## Canonical model references

Paperclip/Hermes:

```text
openrouter/bifrost/main-free
```

OpenCode:

```text
bifrost/openrouter/bifrost/main-free
```