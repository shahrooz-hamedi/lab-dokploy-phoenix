# Paperclip self-hosted deployment

Pinned Paperclip image: ghcr.io/paperclipai/paperclip:2026.916.1

## Services

* paperclip
* PostgreSQL 17
* hermes-dashboard

Paperclip uses the existing external `dokploy-network`.

No host ports are published and no Traefik labels are included; Dokploy/Traefik
handles the `paperclip.phoenix-rtp.com` route and TLS.

## Included AI runtime

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

All CLI runtime directories are owned by the `node` user.

Hermes is installed at:

`/home/node/.hermes`

and persisted separately with the `paperclip-hermes` Docker volume.

Paperclip's native `hermes_local` adapter can therefore run Hermes locally
inside the Paperclip container. No Hermes adapter/plugin installation is
required.

## Bifrost

Bifrost provides the OpenAI-compatible and Anthropic-compatible AI endpoints:

* OpenAI-compatible:
    `https://bifrost.phoenix-rtp.com/v1`
* Anthropic-compatible:
    `https://bifrost.phoenix-rtp.com/anthropic`

The current Paperclip-facing model reference is:

`bifrost/main-free`

The distinction between the Paperclip model reference and the provider's
underlying model ID is intentional:

* Paperclip/OpenCode model reference: `bifrost/main-free`
* Paperclip/Pi model reference: `bifrost/main-free`
* Paperclip/Codex provider: `bifrost`
* Bifrost model ID sent by the adapters: `main-free`
* Hermes provider: `bifrost`
* Hermes model ID: `main-free`

The deployment exposes Bifrost as a provider to Paperclip's local:

* OpenCode adapter
* Pi adapter
* Codex adapter

This is done through:

* `PAPERCLIP_OPENCODE_PROVIDERS`
* `PAPERCLIP_PI_PROVIDERS`
* `PAPERCLIP_CODEX_PROVIDERS`

The provider definitions are runtime configuration supplied by the Paperclip
server; they do not require manually editing the CLI configuration files.

## Bifrost credentials

`BIFROST_API_KEY` is the Paperclip Bifrost virtual key exposed internally to
the local Paperclip adapters.

It is mapped from:

`BIFROST_PAPERCLIP_API_KEY`

The CEO Hermes dashboard receives a separate Bifrost virtual key:

`BIFROST_CEO_API_KEY`

This is intentionally separate from the Paperclip credential.

`BIFROST_API_KEY` is a Bifrost virtual key. It is not an upstream provider
credential.

## Anthropic-compatible integrations

`ANTHROPIC_BASE_URL` points Claude Code and compatible integrations to
Bifrost's Anthropic-compatible endpoint.

`ANTHROPIC_API_KEY` therefore contains the Bifrost credential expected by that
endpoint.

## Persistent storage

Three Docker volumes are used:

* `paperclip-data` — Paperclip application data, backups, and persistent files
* `paperclip-postgres` — PostgreSQL data
* `paperclip-hermes` — Hermes installation, configuration, sessions, skills,
  and state

Hermes is intentionally kept separate from `/paperclip`.

## First deployment

1. Create:
    * `compose.yaml`
    * `.env`
    * `Dockerfile`
2. Populate `.env` and generate the required secrets.
3. Deploy the stack from Dokploy.
4. Verify PostgreSQL becomes healthy and Paperclip starts successfully.
5. Open:
    `https://paperclip.phoenix-rtp.com`
6. Install LLM Wiki from:
    `Settings -> Plugins -> Install Plugin`
    Package:
    `@paperclipai/plugin-llm-wiki`
7. Enable the plugin and approve its requested capabilities.
8. Bootstrap the Wiki root under persistent `/paperclip` storage.

## Important

`BIFROST_SELECTED_MODEL` is the Paperclip-facing model reference:

`bifrost/main-free`

The provider-specific configuration intentionally uses the underlying
model ID:

`main-free`

Do not remove the `bifrost/` prefix from `BIFROST_SELECTED_MODEL`.

Do not add the `bifrost/` prefix to the model ID inside the Pi or OpenCode
provider registry, because those registries are already scoped to the
provider named `bifrost`.

Codex similarly selects the provider separately with:

`model_provider = bifrost`

and therefore uses:

`model = main-free`

Hermes uses its named custom provider `bifrost` and likewise uses:

`default_model: main-free`

## Hermes persistence

The Dockerfile seeds the correct fresh Hermes configuration.

The existing `paperclip-hermes` volume is persistent and therefore takes
precedence over the image's seeded `/home/node/.hermes/config.yaml`.

If an existing deployment contains an older Hermes model reference, update
the persistent Hermes configuration deliberately rather than assuming that
rebuilding the image will replace it.

## Provider credentials

Provider credentials may later be stored in Paperclip's company secret store
and referenced by individual agents.

The process-level provider variables remain intentionally available because
Paperclip and its adapters use them for custom provider configuration and
provider/model discovery.

## Do not rotate deployment secrets casually

Do not delete or regenerate these secrets after deployment unless performing
the corresponding rotation or migration:

* `BETTER_AUTH_SECRET`
* `PAPERCLIP_TOOL_ACTION_SIGNING_SECRET`
* `PAPERCLIP_SECRETS_MASTER_KEY`
* `POSTGRES_PASSWORD`

## Current infrastructure state

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

# CEO Dashboard password hash
# Generate the CEO Dashboard password hash with:
`python3 -c 'import base64,hashlib,secrets; p="strongpassword"; salt=secrets.token_bytes(16); dk=hashlib.scrypt(p.encode(),salt=salt,n=2**14,r=8,p=1,dklen=32,maxmem=0); print(f"scrypt$16384$8$1${base64.b64encode(salt).decode()}${base64.b64encode(dk).decode()}')`
# Onboardin:
PC=$(docker ps --filter "name=paperclip" --format '{{.Names}}' | grep -v postgres | head -1)

docker exec -it --user node "$PC" sh -lc '
  /app/cli/node_modules/.bin/tsx \
    /app/cli/src/index.ts \
    onboard
'
# Postgres Connection String:
postgresql://paperclip:${POSTGRES_PASSWORD}@paperclip-postgres:5432/paperclip
# Board Operator Cli Token:
docker exec -it "$PC" sh -lc '
  /app/cli/node_modules/.bin/tsx \
    /app/cli/src/index.ts \
    connect \
    --persona board \
    --api-base https://paperclip.phoenix-rtp.com
'