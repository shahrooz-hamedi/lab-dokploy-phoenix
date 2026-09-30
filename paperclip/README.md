# Paperclip self-hosted deployment

Pinned Paperclip image: `ghcr.io/paperclipai/paperclip:2026.916.1`

Services:
- `paperclip`
- PostgreSQL 17

Paperclip is exposed only through the existing external `dokploy-network`.
No host port is published and no Traefik labels are included; Dokploy/Traefik
remains responsible for the `paperclip.phoenix-rtp.com` route and TLS.

## First deployment

1. Create the three files:
   - `compose.yaml`
   - `.env`
   - `Dockerfile`

2. Populate `.env`.

3. Start the stack from Dokploy.

4. Wait for PostgreSQL health and Paperclip startup.

5. Open:
   `https://paperclip.phoenix-rtp.com`

6. Install LLM Wiki from:
   Settings -> Plugins -> Install Plugin
   Package:
   `@paperclipai/plugin-llm-wiki`

7. Enable the plugin and approve its requested capabilities.

8. Bootstrap the Wiki root from the plugin settings/API. The Wiki root
   should be placed under the persistent `/paperclip` storage, not a second
   Docker volume.

## Important

The Bifrost virtual key in `BIFROST_API_KEY` is used by the custom
OpenCode/Pi/Codex provider definitions. It is not an upstream provider key.

The `ANTHROPIC_BASE_URL` points Claude Code at Bifrost's Anthropic-compatible
endpoint. `ANTHROPIC_API_KEY` should therefore contain the credential Bifrost
expects for that path.

Provider credentials can later be copied into Paperclip's company secret
store and referenced from individual agent configurations. The process-level
provider variables remain intentionally present because Paperclip uses them
for provider/model discovery.

Do not delete or regenerate:
- `BETTER_AUTH_SECRET`
- `PAPERCLIP_TOOL_ACTION_SIGNING_SECRET`
- `PAPERCLIP_SECRETS_MASTER_KEY`
- `POSTGRES_PASSWORD`

unless you have deliberately planned the corresponding rotation/migration.
