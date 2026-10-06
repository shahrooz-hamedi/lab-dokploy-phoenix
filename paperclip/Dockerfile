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
# Install Hermes into the image.
#
# HERMES_HOME is deliberately the normal Hermes location here.
# The completed installation is copied to /opt/hermes-seed below.
# At runtime, the persistent hermes-data volume is mounted at
# /home/node/.hermes and initialized from this seed on first start.
# ------------------------------------------------------------------
RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh \
    | bash -s -- --non-interactive

# ------------------------------------------------------------------
# Configure the Hermes provider.
# ------------------------------------------------------------------
RUN hermes config set model.provider custom:bifrost \
    && hermes config set model.default openrouter/bifrost/main-free \
    && hermes config set --force providers.bifrost.name Bifrost \
    && hermes config set --force providers.bifrost.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.key_env BIFROST_CEO_API_KEY \
    && hermes config set --force providers.bifrost.discover_models true

# ------------------------------------------------------------------
# Preserve the complete, installed Hermes home inside the image.
# The runtime volume will be initialized from this directory.
# ------------------------------------------------------------------
RUN cp -a /home/node/.hermes /opt/hermes-seed

USER root

RUN cat > /usr/local/bin/paperclip-hermes-entrypoint <<'EOF'
#!/bin/sh
set -eu

HERMES_HOME="/home/node/.hermes"
HERMES_SEED="/opt/hermes-seed"

# Initialize the persistent Hermes volume only when it is empty.
if [ ! -f "${HERMES_HOME}/.hermes-bootstrap-complete" ]; then
    echo "Initializing persistent Hermes home..."

    cp -a "${HERMES_SEED}/." "${HERMES_HOME}/"

    chown -R node:node "${HERMES_HOME}"
fi

exec /app/start.sh
EOF

RUN chmod +x /usr/local/bin/paperclip-hermes-entrypoint

USER node

ENTRYPOINT ["/usr/local/bin/paperclip-hermes-entrypoint"]