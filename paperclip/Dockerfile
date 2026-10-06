FROM ghcr.io/paperclipai/paperclip:2026.1001.0

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       git \
       libatomic1 \
       libx11-6 \
       libxi6 \
       libxkbcommon0 \
    && rm -rf /var/lib/apt/lists/*

USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:${PATH}

# ------------------------------------------------------------
# Install Hermes using the official Hermes installer.
#
# Hermes owns its own Python runtime and dependency management.
# ------------------------------------------------------------
RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh \
    | bash -s -- --non-interactive

# ------------------------------------------------------------
# Solstice provider bootstrap fix
#
# Hermes discovers bundled model-provider plugins while the
# installation environment is still being prepared.
#
# Solstice's __init__.py eagerly imports transport.py:
#
#   from .transport import INFERENCE_BASE_URL, SolsticeClient
#
# transport.py ultimately depends on the Gemini adapter/httpx.
# This causes provider discovery to fail with:
#
#   Failed to load bundled provider plugin solstice:
#   No module named 'httpx'
#
# Keep Solstice fully installed and functional, but defer the
# SolsticeClient import until create_client() is actually called.
# ------------------------------------------------------------
RUN python3 - <<'PY'
from pathlib import Path

p = Path("/home/node/.hermes/hermes-agent/plugins/model-providers/solstice/__init__.py")

text = p.read_text()

old_import = "from .transport import INFERENCE_BASE_URL, SolsticeClient"
new_import = 'INFERENCE_BASE_URL = "https://generativelanguage.googleapis.com/v1alpha"'

if old_import not in text:
    raise SystemExit(
        "Expected Solstice import was not found; refusing to modify the file."
    )

text = text.replace(old_import, new_import, 1)

old_create = '''class SolsticeProfile(ProviderProfile):
    def create_client(self, **client_kwargs: Any) -> Any:
        allowed = {"api_key", "base_url", "default_headers", "timeout", "http_client"}
        return SolsticeClient(**{k: v for k, v in client_kwargs.items() if k in allowed})
'''

new_create = '''class SolsticeProfile(ProviderProfile):
    def create_client(self, **client_kwargs: Any) -> Any:
        from .transport import SolsticeClient

        allowed = {"api_key", "base_url", "default_headers", "timeout", "http_client"}
        return SolsticeClient(**{k: v for k, v in client_kwargs.items() if k in allowed})
'''

if old_create not in text:
    raise SystemExit(
        "Expected Solstice create_client() block was not found; refusing to modify the file."
    )

text = text.replace(old_create, new_create, 1)

p.write_text(text)
PY

# Keep the duplicated installed workspace in sync with the source tree
# used by Hermes' isolated runtime.
RUN python3 - <<'PY'
from pathlib import Path

src = Path("/home/node/.hermes/hermes-agent/plugins/model-providers/solstice/__init__.py")

for p in Path("/home/node/.hermes/installs").glob(
    "*/environments/*/workspace/plugins/model-providers/solstice/__init__.py"
):
    p.write_text(src.read_text())
PY

# ------------------------------------------------------------
# Configure Hermes to use the named Bifrost provider.
#
# Bifrost remains the only inference gateway.
#
# IMPORTANT:
# Hermes has both:
#   model.base_url
# and:
#   providers.bifrost.base_url
#
# Both must point to Bifrost.
# ------------------------------------------------------------
RUN hermes config set --force model.provider custom:bifrost \
    && hermes config set --force model.default openrouter/bifrost/main-free \
    && hermes config set --force model.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.name Bifrost \
    && hermes config set --force providers.bifrost.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.key_env BIFROST_CEO_API_KEY \
    && hermes config set --force providers.bifrost.discover_models true

# ------------------------------------------------------------
# Preserve the complete Hermes installation in the image.
#
# The runtime named volume at /home/node/.hermes is initialized
# from this seed on first startup.
# ------------------------------------------------------------
USER root

RUN cp -a /home/node/.hermes /opt/hermes-seed \
    && chown -R node:node /opt/hermes-seed

# ------------------------------------------------------------
# Runtime entrypoint.
#
# Starts as root because the persistent Hermes volume may be
# empty and needs ownership initialization.
# ------------------------------------------------------------
RUN cat > /usr/local/bin/paperclip-hermes-entrypoint <<'EOF'
#!/bin/sh
set -eu

HERMES_HOME="/home/node/.hermes"
HERMES_SEED="/opt/hermes-seed"
HERMES_MARKER="${HERMES_HOME}/.hermes-bootstrap-complete"

if [ ! -f "${HERMES_MARKER}" ]; then
    echo "Initializing persistent Hermes home..."

    cp -a "${HERMES_SEED}/." "${HERMES_HOME}/"
    chown -R node:node "${HERMES_HOME}"

    touch "${HERMES_MARKER}"
    chown node:node "${HERMES_MARKER}"
fi

# ------------------------------------------------------------
# Reconcile the active Hermes model endpoint on every startup.
#
# This is intentionally separate from providers.bifrost.base_url.
# Hermes uses model.base_url for the active custom provider
# endpoint, so a persistent Hermes volume must not retain the
# installer's default OpenRouter endpoint.
# ------------------------------------------------------------
hermes config set --force model.base_url https://bifrost.phoenix-rtp.com/v1

exec /usr/bin/tini -- \
    /usr/local/bin/docker-entrypoint.sh \
    node --import ./server/node_modules/tsx/dist/loader.mjs server/dist/index.js
EOF

RUN chmod +x /usr/local/bin/paperclip-hermes-entrypoint

USER root

ENTRYPOINT ["/usr/local/bin/paperclip-hermes-entrypoint"]