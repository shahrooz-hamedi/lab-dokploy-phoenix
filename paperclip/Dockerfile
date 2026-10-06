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

# ------------------------------------------------------------
# Hermes
# ------------------------------------------------------------

USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:${PATH}

RUN curl -fsSL \
      https://hermes-agent.nousresearch.com/install.sh \
      | bash -s -- --non-interactive

# ------------------------------------------------------------
# Verify the Hermes PM environment that the official installer
# created. This is the important test.
# ------------------------------------------------------------

RUN cd /home/node/.hermes/hermes-agent \
    && PYTHON="$(python3 -c 'from pathlib import Path; from pm.environments import project_python; print(project_python(Path("/home/node/.hermes/hermes-agent")))')" \
    && echo "Hermes PM Python: ${PYTHON}" \
    && test -x "${PYTHON}" \
    && "${PYTHON}" -c 'import sys, httpx; print("Hermes runtime:", sys.executable); print("httpx:", httpx.__file__); print("httpx version:", httpx.__version__)'

# ------------------------------------------------------------
# Configure Hermes -> Bifrost
# ------------------------------------------------------------

RUN /home/node/.local/bin/hermes config set --force model.provider custom:bifrost \
    && /home/node/.local/bin/hermes config set --force model.default openrouter/bifrost/main-free \
    && /home/node/.local/bin/hermes config set --force model.base_url https://bifrost.phoenix-rtp.com/v1 \
    && /home/node/.local/bin/hermes config set --force providers.bifrost.name Bifrost \
    && /home/node/.local/bin/hermes config set --force providers.bifrost.base_url https://bifrost.phoenix-rtp.com/v1 \
    && /home/node/.local/bin/hermes config set --force providers.bifrost.key_env BIFROST_CEO_API_KEY \
    && /home/node/.local/bin/hermes config set --force providers.bifrost.discover_models true

# ------------------------------------------------------------
# Pi
# ------------------------------------------------------------

USER root

RUN npm install -g @earendil-works/pi-coding-agent \
    && command -v pi \
    && pi --version

# ------------------------------------------------------------
# Seed Hermes installation for the persistent runtime volume
# ------------------------------------------------------------

RUN cp -a /home/node/.hermes /opt/hermes-seed \
    && chown -R node:node /opt/hermes-seed

# ------------------------------------------------------------
# Runtime entrypoint
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

exec su -s /bin/sh node -c '
    set -eu

    export HOME=/home/node
    export HERMES_HOME=/home/node/.hermes
    export PATH=/home/node/.local/bin:$PATH

    hermes config set --force \
      model.base_url https://bifrost.phoenix-rtp.com/v1

    exec /usr/bin/tini -- \
      /usr/local/bin/docker-entrypoint.sh \
      node --import ./server/node_modules/tsx/dist/loader.mjs \
      server/dist/index.js
'
EOF

RUN chmod +x /usr/local/bin/paperclip-hermes-entrypoint

ENTRYPOINT ["/usr/local/bin/paperclip-hermes-entrypoint"]