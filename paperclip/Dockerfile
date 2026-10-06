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
# Configure Hermes to use the named Bifrost provider.
#
# Bifrost remains the only inference gateway.
# ------------------------------------------------------------
RUN hermes config set model.provider custom:bifrost \
    && hermes config set model.default openrouter/bifrost/main-free \
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
# Must start as root because the persistent Hermes volume may be
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

exec /usr/bin/tini -- \
    /usr/local/bin/docker-entrypoint.sh \
    node --import ./server/node_modules/tsx/dist/loader.mjs server/dist/index.js
EOF

RUN chmod +x /usr/local/bin/paperclip-hermes-entrypoint

USER root

ENTRYPOINT ["/usr/local/bin/paperclip-hermes-entrypoint"]