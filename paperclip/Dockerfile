FROM ghcr.io/paperclipai/paperclip:2026.1001.0

USER root

# ============================================================
# System prerequisites
# ============================================================
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

# ============================================================
# Hermes environment
# ============================================================
USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:${PATH}

# ============================================================
# Hermes official installer
#
# Keep Hermes' own PM-managed Python environment intact.
# Do NOT install Hermes Python dependencies with pip.
# ============================================================

RUN curl -fsSL \
      https://hermes-agent.nousresearch.com/install.sh \
      -o /tmp/hermes-install.sh \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage prerequisites \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage repository \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage venv \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage python-deps \
    && rm -f /tmp/hermes-install.sh

# ============================================================
# Verify the Hermes PM environment.
#
# IMPORTANT:
# This uses a single-line Python command so Docker cannot
# mistake Python source for a Dockerfile instruction.
# ============================================================

RUN cd /home/node/.hermes/hermes-agent \
    && PYTHON="$(python3 -c 'from pathlib import Path; from pm.environments import project_python; print(project_python(Path("/home/node/.hermes/hermes-agent")))')" \
    && echo "Hermes PM Python: ${PYTHON}" \
    && test -x "${PYTHON}" \
    && "${PYTHON}" -c 'import sys; import httpx; print("Hermes runtime:", sys.executable); print("httpx:", httpx.__file__); print("httpx version:", httpx.__version__)'

# ============================================================
# Ask Hermes PM to repair/rebuild its managed dependency
# generation.
#
# This is Hermes' supported mechanism for repairing dependency
# state. We do NOT use pip or modify Solstice.
# ============================================================

RUN hermes pm repair

# ============================================================
# Verify httpx AGAIN after PM repair.
# ============================================================

RUN cd /home/node/.hermes/hermes-agent \
    && PYTHON="$(python3 -c 'from pathlib import Path; from pm.environments import project_python; print(project_python(Path("/home/node/.hermes/hermes-agent")))')" \
    && echo "Hermes PM Python after repair: ${PYTHON}" \
    && test -x "${PYTHON}" \
    && "${PYTHON}" -c 'import sys; import httpx; print("Hermes runtime:", sys.executable); print("httpx:", httpx.__file__); print("httpx version:", httpx.__version__)'

# ============================================================
# Complete Hermes products/provider installation.
#
# This is the stage where the official source completion code
# performs provider discovery.
#
# There is NO Solstice source patch.
# ============================================================

RUN curl -fsSL \
      https://hermes-agent.nousresearch.com/install.sh \
      -o /tmp/hermes-install.sh \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage products \
    && rm -f /tmp/hermes-install.sh

# ============================================================
# Prepare Hermes configuration and mark installation complete.
# ============================================================

RUN curl -fsSL \
      https://hermes-agent.nousresearch.com/install.sh \
      -o /tmp/hermes-install.sh \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage config \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage complete \
    && rm -f /tmp/hermes-install.sh

# ============================================================
# Configure Hermes -> Bifrost
# ============================================================

RUN hermes config set --force model.provider custom:bifrost \
    && hermes config set --force model.default openrouter/bifrost/main-free \
    && hermes config set --force model.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.name Bifrost \
    && hermes config set --force providers.bifrost.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.key_env BIFROST_CEO_API_KEY \
    && hermes config set --force providers.bifrost.discover_models true

# ============================================================
# Install Pi
#
# Paperclip's pi_local adapter requires the Pi CLI to exist
# inside the same container.
# ============================================================

USER root

RUN npm install -g @earendil-works/pi-coding-agent \
    && command -v pi \
    && pi --version

# ============================================================
# Final executable verification
# ============================================================

RUN command -v hermes \
    && hermes --version \
    && command -v pi \
    && pi --version

# ============================================================
# Seed Hermes installation
# ============================================================

RUN cp -a /home/node/.hermes /opt/hermes-seed \
    && chown -R node:node /opt/hermes-seed

# ============================================================
# Runtime entrypoint
# ============================================================

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