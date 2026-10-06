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
# Hermes
#
# IMPORTANT:
# This diagnostic intentionally does NOT install httpx,
# modify PYTHONPATH, modify Hermes source, disable Solstice,
# or configure a provider.
#
# We want to observe the official installer exactly as-is.
# ------------------------------------------------------------

USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:${PATH}

# ------------------------------------------------------------
# Run the official Hermes installer unchanged.
# ------------------------------------------------------------

RUN curl -fsSL \
      https://hermes-agent.nousresearch.com/install.sh \
      | bash -s -- --non-interactive

# ------------------------------------------------------------
# DIAGNOSTICS
#
# The installer has now completed. Extract the exact paths
# and source involved in bundled provider discovery.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: ENVIRONMENT"; \
    echo "============================================================"; \
    echo "USER:"; id; \
    echo; \
    echo "HOME=${HOME}"; \
    echo "HERMES_HOME=${HERMES_HOME}"; \
    echo "PATH=${PATH}"; \
    echo "PYTHONPATH=${PYTHONPATH:-<unset>}"; \
    echo; \
    echo "python3:"; \
    command -v python3 || true; \
    python3 --version || true; \
    python3 -c 'import sys; print("sys.executable =", sys.executable); print("sys.prefix =", sys.prefix); print("sys.path ="); [print("  ", x) for x in sys.path]' || true; \
    echo; \
    echo "uv:"; \
    command -v uv || true; \
    uv --version || true; \
    echo; \
    echo "hermes launcher:"; \
    command -v hermes || true; \
    ls -l /home/node/.local/bin/hermes 2>/dev/null || true; \
    sed -n '1,80p' /home/node/.local/bin/hermes 2>/dev/null || true

# ------------------------------------------------------------
# Locate Hermes source and every relevant Python executable.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: INSTALLATION TREE"; \
    echo "============================================================"; \
    echo "HERMES_HOME:"; \
    find /home/node/.hermes -maxdepth 3 \
      -type d \
      -print 2>/dev/null \
      | sort \
      | head -300; \
    echo; \
    echo "Python executables:"; \
    find /home/node/.hermes \
      -type f \
      \( -name python -o -name python3 -o -name python3.14 \) \
      -perm -111 \
      -print 2>/dev/null \
      | sort

# ------------------------------------------------------------
# Locate the provider registry and Solstice source.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: PROVIDER SOURCE"; \
    echo "============================================================"; \
    echo "Provider registry files:"; \
    find /home/node/.hermes/hermes-agent \
      -type f \
      \( \
        -path '*/providers/__init__.py' \
        -o -path '*/providers/README.md' \
        -o -path '*/plugins/model-providers/*/__init__.py' \
      \) \
      -print 2>/dev/null \
      | sort; \
    echo; \
    echo "Solstice files:"; \
    find /home/node/.hermes/hermes-agent \
      -type f \
      -path '*/solstice/*' \
      -print 2>/dev/null \
      | sort

# ------------------------------------------------------------
# Print the exact provider discovery implementation.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: PROVIDER DISCOVERY CODE"; \
    echo "============================================================"; \
    REGISTRY="$(find /home/node/.hermes/hermes-agent \
      -type f \
      -path '*/providers/__init__.py' \
      -print -quit 2>/dev/null || true)"; \
    echo "REGISTRY=${REGISTRY:-<not found>}"; \
    if [ -n "${REGISTRY}" ]; then \
      echo; \
      sed -n '1,320p' "${REGISTRY}"; \
    fi

# ------------------------------------------------------------
# Print Solstice imports and package metadata.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: SOLSTICE IMPORTS"; \
    echo "============================================================"; \
    SOLSTICE_DIR="$(find /home/node/.hermes/hermes-agent \
      -type d \
      -path '*/plugins/model-providers/solstice' \
      -print -quit 2>/dev/null || true)"; \
    echo "SOLSTICE_DIR=${SOLSTICE_DIR:-<not found>}"; \
    if [ -n "${SOLSTICE_DIR}" ]; then \
      echo; \
      find "${SOLSTICE_DIR}" -maxdepth 2 -type f -print | sort; \
      echo; \
      grep -RniE \
        '(^|[^A-Za-z])(httpx|importlib|import_module|provider|discover|register)' \
        "${SOLSTICE_DIR}" \
        2>/dev/null \
        | head -300 || true; \
    fi

# ------------------------------------------------------------
# Find the EXACT source of the error message.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: ERROR MESSAGE SOURCE"; \
    echo "============================================================"; \
    grep -RniF \
      'Failed to load bundled provider plugin' \
      /home/node/.hermes/hermes-agent \
      2>/dev/null \
      | head -100 || true

# ------------------------------------------------------------
# Find every place Hermes imports/mentions httpx.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: ALL HTTPX REFERENCES"; \
    echo "============================================================"; \
    grep -RniE \
      '(^|[^A-Za-z])import httpx|(^|[^A-Za-z])from httpx|httpx' \
      /home/node/.hermes/hermes-agent \
      2>/dev/null \
      | head -500 || true

# ------------------------------------------------------------
# Inspect PM's environment metadata.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: PM ENVIRONMENTS"; \
    echo "============================================================"; \
    find /home/node/.hermes/installs \
      -maxdepth 6 \
      -type f \
      \( \
        -name pyvenv.cfg \
        -o -name pyproject.toml \
        -o -name uv.lock \
        -o -name requirements.txt \
        -o -name '*.json' \
      \) \
      -print 2>/dev/null \
      | sort \
      | head -300; \
    echo; \
    find /home/node/.hermes/installs \
      -type f \
      -path '*/bin/python*' \
      -perm -111 \
      -print 2>/dev/null \
      | sort

# ------------------------------------------------------------
# For every discovered Hermes Python, show its identity and
# whether it can import httpx.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: PYTHON IMPORT TESTS"; \
    echo "============================================================"; \
    for PY in \
      /home/node/.hermes/hermes-agent/.hermes/bin/python \
      /home/node/.hermes/hermes-agent/venv/bin/python \
      /home/node/.hermes/hermes-agent/.venv/bin/python \
      /home/node/.hermes/installs/*/environments/*/venv/bin/python \
      /home/node/.hermes/installs/*/bin/python \
      /home/node/.hermes/installs/*/python/bin/python; \
    do \
      if [ -x "$PY" ]; then \
        echo; \
        echo "----- $PY -----"; \
        "$PY" --version || true; \
        "$PY" -c 'import sys; print("executable:", sys.executable); print("prefix:", sys.prefix); print("base_prefix:", sys.base_prefix); print("path:"); [print(" ", x) for x in sys.path]' || true; \
        "$PY" -c 'import httpx; print("httpx:", httpx.__file__); print("httpx version:", httpx.__version__)' 2>&1 || true; \
      fi; \
    done

# ------------------------------------------------------------
# Inspect the actual hermes executable and PM entry points.
# ------------------------------------------------------------

RUN set -eux; \
    echo; \
    echo "============================================================"; \
    echo "HERMES DIAGNOSTIC: EXECUTABLES"; \
    echo "============================================================"; \
    find /home/node/.hermes/hermes-agent \
      -maxdepth 5 \
      -type f \
      \( \
        -name hermes \
        -o -name pm \
        -o -name '*.py' \
      \) \
      -perm -111 \
      -print 2>/dev/null \
      | sort \
      | head -300; \
    echo; \
    echo "PM modules:"; \
    find /home/node/.hermes/hermes-agent \
      -type f \
      -path '*/pm/*' \
      -print 2>/dev/null \
      | sort \
      | head -300

# ------------------------------------------------------------
# Configure Hermes -> Bifrost
# ------------------------------------------------------------
#
# This is deliberately retained only so the resulting image
# remains structurally identical to the deployment image.
# It is NOT part of the diagnostic.
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