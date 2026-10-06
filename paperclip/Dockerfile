FROM ghcr.io/paperclipai/paperclip:2026.1001.0

USER root

# ------------------------------------------------------------
# System prerequisites
# ------------------------------------------------------------
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
# Hermes runs as the Paperclip "node" service user.
#
# Hermes owns:
#   - its source checkout
#   - its PM tool store
#   - its managed Python environment
#   - its Python dependencies
# ------------------------------------------------------------
USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:${PATH}

# ------------------------------------------------------------
# Pi
#
# Paperclip's pi_local adapter expects the `pi` CLI to already
# exist in the container.
#
# Pi is a Node CLI, independent of Hermes' Python environment.
# Pin the version for reproducible Paperclip builds.
# ------------------------------------------------------------
USER root

RUN npm install -g @earendil-works/pi-coding-agent@0.99.1 \
    && command -v pi \
    && pi --version

USER node

# ------------------------------------------------------------
# Hermes installation
#
# We intentionally run the official installer by stage instead
# of doing the entire installer in one opaque RUN.
#
# This lets us:
#
#   1. clone Hermes
#   2. bootstrap Hermes PM
#   3. install Hermes' locked Python environment
#   4. explicitly repair that PM-managed environment
#   5. verify httpx in the selected PM Python
#   6. ONLY THEN run Hermes product/provider completion
#
# We do NOT pip-install httpx into system Python.
# We do NOT modify Solstice to hide its dependency.
# ------------------------------------------------------------
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

# ------------------------------------------------------------
# Verify and repair the Hermes PM-managed dependency environment
# BEFORE Hermes performs source/product completion.
#
# Hermes documentation explicitly provides:
#
#   hermes pm repair
#
# for repairing the managed Python dependency generation.
# ------------------------------------------------------------
RUN /home/node/.hermes/hermes-agent/.hermes/bin/hermes pm repair

# ------------------------------------------------------------
# Hard build-time verification:
#
# The PM-selected Hermes Python must be able to import httpx.
#
# If this fails, the image build stops here instead of producing
# an image with a hidden provider-environment problem.
# ------------------------------------------------------------
RUN cd /home/node/.hermes/hermes-agent \
    && python3 - <<'PY'
from pathlib import Path

from pm.environments import project_python

root = Path("/home/node/.hermes/hermes-agent")
python = project_python(root)

print(f"PM project Python: {python}")

if not python.exists():
    raise SystemExit(f"PM project Python does not exist: {python}")
PY

RUN cd /home/node/.hermes/hermes-agent \
    && PYTHON="$(
         python3 - <<'PY'
from pathlib import Path
from pm.environments import project_python

print(project_python(Path("/home/node/.hermes/hermes-agent")))
PY
       )" \
    && "$PYTHON" -c '
import sys
import httpx

print("Hermes PM Python:", sys.executable)
print("httpx:", httpx.__file__)
print("httpx version:", httpx.__version__)
'

# ------------------------------------------------------------
# Now complete the official Hermes installation.
#
# At this point PM has already created/repaired the dependency
# environment and httpx has been verified in the selected
# Hermes Python.
#
# This is the stage at which Hermes builds/publishes its command
# and performs provider/product completion.
# ------------------------------------------------------------
RUN curl -fsSL \
      https://hermes-agent.nousresearch.com/install.sh \
      -o /tmp/hermes-install.sh \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage products \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage config \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage complete \
    && rm -f /tmp/hermes-install.sh

# ------------------------------------------------------------
# Configure Hermes to use Bifrost.
#
# These are the user's existing model/provider references.
# Do not replace them with a raw provider model ID.
# ------------------------------------------------------------
RUN hermes config set --force model.provider custom:bifrost \
    && hermes config set --force model.default openrouter/bifrost/main-free \
    && hermes config set --force model.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.name Bifrost \
    && hermes config set --force providers.bifrost.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.key_env BIFROST_CEO_API_KEY \
    && hermes config set --force providers.bifrost.discover_models true

# ------------------------------------------------------------
# Final Hermes verification.
# ------------------------------------------------------------
RUN command -v hermes \
    && hermes --version \
    && command -v pi \
    && pi --version

# ------------------------------------------------------------
# Seed the complete Hermes installation.
#
# Runtime uses a persistent Docker volume at /home/node/.hermes.
# The first container start copies this fully prepared installation
# into that volume.
# ------------------------------------------------------------
USER root

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

# Keep the persistent Hermes configuration pointed at Bifrost.
# Do this as the Hermes service user rather than root.
exec su -s /bin/sh node -c '
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