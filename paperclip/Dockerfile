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
# Global Python dependency required during Hermes installation
#
# Hermes provider discovery can happen during installation.
# Solstice imports httpx at that stage, before Hermes finishes
# preparing its isolated runtime.
#
# The Paperclip base image uses an externally-managed system
# Python environment (PEP 668), so --break-system-packages is
# required for this intentional Docker-image-level installation.
# ------------------------------------------------------------

RUN curl -LsSf https://astral.sh/uv/install.sh \
      | env UV_INSTALL_DIR=/usr/local/bin sh \
    && /usr/local/bin/uv --version \
    && /usr/local/bin/uv pip install \
       --system \
       --break-system-packages \
       --no-cache \
       httpx==0.28.1 \
    && python3 -c \
       'import httpx; print("Global httpx:", httpx.__file__); print("Global httpx version:", httpx.__version__)'

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
# Verify the Hermes PM environment created by the
# official installer.
# ------------------------------------------------------------

RUN cd /home/node/.hermes/hermes-agent \
    && PYTHON="$(python3 -c 'from pathlib import Path; from pm.environments import project_python; print(project_python(Path("/home/node/.hermes/hermes-agent")))')" \
    && echo "Hermes PM Python: ${PYTHON}" \
    && test -x "${PYTHON}" \
    && "${PYTHON}" -c \
       'import sys, httpx; print("Hermes runtime:", sys.executable); print("httpx:", httpx.__file__); print("httpx version:", httpx.__version__)'

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