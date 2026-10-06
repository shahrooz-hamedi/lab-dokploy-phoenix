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

# ------------------------------------------------------------------
# Install Hermes.
# ------------------------------------------------------------------
RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh \
    | bash -s -- --non-interactive

# ------------------------------------------------------------------
# Configure Hermes.
#
# DO NOT CHANGE THESE VALUES:
#   provider = custom:bifrost
#   model    = openrouter/bifrost/main-free
# ------------------------------------------------------------------
RUN hermes config set model.provider custom:bifrost \
    && hermes config set model.default openrouter/bifrost/main-free \
    && hermes config set --force providers.bifrost.name Bifrost \
    && hermes config set --force providers.bifrost.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.key_env BIFROST_CEO_API_KEY \
    && hermes config set --force providers.bifrost.discover_models true

# ------------------------------------------------------------------
# Ensure Hermes' own PM-managed dependency environment is populated.
#
# This is intentionally Hermes PM, not pip/system Python.
# ------------------------------------------------------------------
RUN hermes pm install --trust-recorded

# ------------------------------------------------------------------
# Preserve the complete Hermes installation, including the PM-managed
# dependency environments, in the image seed.
# ------------------------------------------------------------------
USER root

RUN cp -a /home/node/.hermes /opt/hermes-seed \
    && chown -R node:node /opt/hermes-seed

# ------------------------------------------------------------------
# Runtime entrypoint.
#
# The Hermes named volume hides /home/node/.hermes from the image,
# therefore initialize a fresh volume from the image seed once.
#
# The wrapper remains root because it must be able to chown the newly
# created named volume before Paperclip starts as node.
# ------------------------------------------------------------------
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

exec /usr/bin/tini -- \
    /usr/local/bin/docker-entrypoint.sh \
    node --import ./server/node_modules/tsx/dist/loader.mjs server/dist/index.js
EOF

RUN chmod +x /usr/local/bin/paperclip-hermes-entrypoint

# The entrypoint intentionally starts as root so it can initialize the
# Hermes named volume. Paperclip's official entrypoint then handles the
# application startup.
USER root

ENTRYPOINT ["/usr/local/bin/paperclip-hermes-entrypoint"]