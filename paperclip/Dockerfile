FROM ghcr.io/paperclipai/paperclip:2026.1001.0

# ------------------------------------------------------------
# OS dependencies
# ------------------------------------------------------------

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
# Hermes bootstrap
#
# Hermes provider discovery can happen during the official
# installer before Hermes has finished preparing its isolated
# runtime. Solstice requires httpx at that stage.
#
# Make httpx available to the global Python environment first.
# ------------------------------------------------------------

RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && /root/.local/bin/uv pip install \
       --system \
       --no-cache \
       httpx==0.28.1 \
    && python3 -c 'import httpx; print("Global httpx:", httpx.__file__); print("Global httpx version:", httpx.__version__)'

# ------------------------------------------------------------
# Hermes
# Install and configure Hermes entirely as node.
# ------------------------------------------------------------

USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:${PATH}

RUN curl -fsSL \
      https://hermes-agent.nousresearch.com/install.sh \
      | bash -s -- --non-interactive

# ------------------------------------------------------------
# Verify Hermes PM environment
#
# The official installer creates the managed environment and
# provides its own httpx there as well.
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
# Runtime
# ------------------------------------------------------------

USER node

RUN cat > /home/node/paperclip-hermes-entrypoint <<'EOF'
#!/bin/sh
set -eu

export HOME=/home/node
export HERMES_HOME=/home/node/.hermes
export PATH=/home/node/.local/bin:$PATH

exec /usr/bin/tini -- \
  /usr/local/bin/docker-entrypoint.sh \
  node --import ./server/node_modules/tsx/dist/loader.mjs \
  server/dist/index.js
EOF

RUN chmod +x /home/node/paperclip-hermes-entrypoint

ENTRYPOINT ["/home/node/paperclip-hermes-entrypoint"]