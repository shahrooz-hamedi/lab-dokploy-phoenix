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
#
# Hermes owns its Python runtime and dependencies through PM.
# Do NOT install Hermes Python packages with system pip.
# ============================================================
USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:/home/node/.hermes/bin:${PATH}

# ============================================================
# Install Hermes using the official installer, stage by stage.
#
# We deliberately separate python-deps and products.
#
# python-deps:
#   PM creates/synchronizes Hermes' managed Python environment.
#
# products:
#   source_completion.py enters the PM-selected environment
#   and performs provider/product completion.
#
# This lets us verify the actual PM environment before the
# provider discovery which previously produced:
#
#   Failed to load bundled provider plugin solstice:
#   No module named 'httpx'
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
# Verify the PM-managed Hermes Python environment.
#
# This MUST resolve to Hermes PM's selected interpreter.
# ============================================================
RUN cd /home/node/.hermes/hermes-agent \
    && python -c '
import sys
import pm
from pathlib import Path
from pm.environments import project_python

root = Path("/home/node/.hermes/hermes-agent")
python = project_python(root)

print("=== HERMES PM ENVIRONMENT ===")
print("python:", python)
print("current interpreter:", sys.executable)
print("pm:", pm.__file__)

if not python.exists():
    raise SystemExit(f"PM project Python does not exist: {python}")
'

# ============================================================
# Verify httpx in the ACTUAL PM-selected interpreter.
#
# We do not use pip.
# We do not modify Solstice.
# We do not install httpx globally.
# ============================================================
RUN cd /home/node/.hermes/hermes-agent \
    && python -c '
from pathlib import Path
import subprocess
from pm.environments import project_python

root = Path("/home/node/.hermes/hermes-agent")
python = project_python(root)

print("=== HERMES HTTPX CHECK ===")
print("PM Python:", python)

result = subprocess.run(
    [
        str(python),
        "-c",
        (
            "import sys, httpx; "
            "print(\"runtime:\", sys.executable); "
            "print(\"httpx:\", httpx.__file__); "
            "print(\"httpx version:\", httpx.__version__)"
        ),
    ],
    check=False,
)

if result.returncode != 0:
    raise SystemExit(
        "Hermes PM environment cannot import httpx. "
        "Refusing to continue to provider/product completion."
    )
'

# ============================================================
# Repair only through Hermes PM if the selected dependency
# generation needs reconstruction.
#
# PM documentation explicitly defines `pm repair` as the
# supported repair operation for damaged dependencies.
# ============================================================
RUN hermes pm repair

# ============================================================
# Re-verify httpx AFTER PM repair.
# ============================================================
RUN cd /home/node/.hermes/hermes-agent \
    && python -c '
from pathlib import Path
import subprocess
from pm.environments import project_python

root = Path("/home/node/.hermes/hermes-agent")
python = project_python(root)

subprocess.run(
    [
        str(python),
        "-c",
        (
            "import sys, httpx; "
            "print(\"Hermes PM Python:\", sys.executable); "
            "print(\"httpx:\", httpx.__file__); "
            "print(\"httpx version:\", httpx.__version__)"
        ),
    ],
    check=True,
)
'

# ============================================================
# Complete Hermes product/provider installation.
#
# IMPORTANT:
# There is NO Solstice patch here.
#
# The official source_completion implementation is responsible
# for re-entering the PM-selected Python environment.
# ============================================================
RUN curl -fsSL \
      https://hermes-agent.nousresearch.com/install.sh \
      -o /tmp/hermes-install.sh \
    && bash /tmp/hermes-install.sh \
         --non-interactive \
         --stage products \
    && rm -f /tmp/hermes-install.sh

# ============================================================
# Prepare Hermes configuration directories.
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
# Configure Hermes -> Bifrost.
#
# Keep the existing model/provider references exactly as used
# by the deployment.
# ============================================================
RUN hermes config set --force model.provider custom:bifrost \
    && hermes config set --force model.default openrouter/bifrost/main-free \
    && hermes config set --force model.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.name Bifrost \
    && hermes config set --force providers.bifrost.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.key_env BIFROST_CEO_API_KEY \
    && hermes config set --force providers.bifrost.discover_models true

# ============================================================
# Pi
#
# Paperclip's pi_local adapter requires the Pi CLI to be
# installed in the Paperclip runtime.
#
# The current package has moved from the old @mariozechner
# namespace to @earendil-works.
#
# Do not configure Pi's provider here. Paperclip supplies
# PAPERCLIP_PI_PROVIDERS at runtime and writes its managed
# models.json.
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
# Seed Hermes into /opt.
#
# /home/node/.hermes is a persistent Docker volume at runtime.
# The first startup copies this fully prepared installation into
# that volume.
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

# Run the Paperclip server as the same service user that owns
# Hermes. This prevents root-owned Hermes state/configuration.
exec su -s /bin/sh node -c '
    set -eu

    export HOME=/home/node
    export HERMES_HOME=/home/node/.hermes
    export PATH=/home/node/.local/bin:/home/node/.hermes/bin:$PATH

    # Persistent Hermes volumes may contain an older endpoint.
    # Reassert Bifrost on every startup.
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