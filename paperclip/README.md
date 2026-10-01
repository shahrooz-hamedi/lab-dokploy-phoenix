##
BEST COMMIT BEFORE ADDING CEO DASHBOARD

Paperclip self-hosted deployment

Pinned Paperclip image: ghcr.io/paperclipai/paperclip:2026.916.1

Services:

* paperclip
* PostgreSQL 17

Paperclip uses the existing external dokploy-network.
No host ports are published and no Traefik labels are included; Dokploy/Traefik
handles the paperclip.phoenix-rtp.com route and TLS.

Included AI runtime

The Paperclip image includes:

* Hermes Agent
* Claude Code
* OpenAI Codex
* Gemini CLI
* OpenCode
* Pi
* Kimi Code
* Grok
* Cursor Agent

All CLI runtime directories are owned by the node user.

Hermes is installed at:

/home/node/.hermes

and persisted separately with the paperclip-hermes Docker volume.

Paperclip’s native hermes_local adapter can therefore run Hermes locally
inside the Paperclip container. No Hermes adapter/plugin installation is
required.

Bifrost

Bifrost provides the OpenAI-compatible and Anthropic-compatible AI endpoints:

* OpenAI-compatible:
    https://bifrost.phoenix-rtp.com/v1
* Anthropic-compatible:
    https://bifrost.phoenix-rtp.com/anthropic

The selected Bifrost model is configured with:

BIFROST_SELECTED_MODEL=hermes-main-free

Paperclip currently exposes Bifrost to its OpenCode, Pi, and Codex provider
definitions through the corresponding PAPERCLIP_*_PROVIDERS variables.

Persistent storage

Three Docker volumes are used:

* paperclip-data — Paperclip application data, backups, and persistent files
* paperclip-postgres — PostgreSQL data
* paperclip-hermes — Hermes installation, configuration, sessions, skills,
    and state

Hermes is intentionally kept separate from /paperclip.

First deployment

1. Create:
    * compose.yaml
    * .env
    * Dockerfile
2. Populate .env and generate the required secrets.
3. Deploy the stack from Dokploy.
4. Verify PostgreSQL becomes healthy and Paperclip starts successfully.
5. Open:
    https://paperclip.phoenix-rtp.com
6. Install LLM Wiki from:
    Settings -> Plugins -> Install Plugin
    Package:
    @paperclipai/plugin-llm-wiki
7. Enable the plugin and approve its requested capabilities.
8. Bootstrap the Wiki root under persistent /paperclip storage.

Important

BIFROST_API_KEY is the Bifrost virtual key used by the custom Paperclip
OpenCode/Pi/Codex provider definitions. It is not an upstream provider key.

ANTHROPIC_BASE_URL points Claude Code and compatible integrations to
Bifrost’s Anthropic-compatible endpoint. ANTHROPIC_API_KEY therefore contains
the credential expected by Bifrost for that endpoint.

Provider credentials may later be stored in Paperclip’s company secret store
and referenced by individual agents.

The process-level provider variables remain intentionally available because
Paperclip and its adapters may use them for provider/model discovery.

Do not delete or regenerate these secrets after deployment unless performing
the corresponding rotation or migration:

* BETTER_AUTH_SECRET
* PAPERCLIP_TOOL_ACTION_SIGNING_SECRET
* PAPERCLIP_SECRETS_MASTER_KEY
* POSTGRES_PASSWORD

Current infrastructure state

The deployment has been validated with:

* Paperclip API health: ok
* PostgreSQL: healthy
* Bifrost model discovery: working
* Bifrost models discovered: 94
* Hermes runtime: working
* Hermes persistence: working
* Codex: working without PATH-alias warning
* Gemini: working without filesystem permission errors
* Claude Code: working
* OpenCode: working
* Pi: working
* Kimi Code: working
* Grok: working
* Cursor Agent: working
* Paperclip container restart count: 0