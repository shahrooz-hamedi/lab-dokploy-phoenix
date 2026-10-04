# =============================================================================
# Paperclip image
# =============================================================================

ARG PAPERCLIP_IMAGE=ghcr.io/paperclipai/paperclip:2026.916.1

FROM ${PAPERCLIP_IMAGE}

USER root

ARG HERMES_VERSION=v2026.9.24
ARG HERMES_COMMIT=f97608f178d1ffeca59860195ab7da295f7c8e5f

ENV DEBIAN_FRONTEND=noninteractive \
    HOME=/home/node \
    PAPERCLIP_HOME=/paperclip \
    HERMES_HOME=/home/node/.hermes \
    PATH=/home/node/.local/bin:/usr/local/bin:/usr/bin:/bin

# =============================================================================
# OS dependencies
# =============================================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        python3-venv \
        build-essential \
        unzip \
        zip \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Hermes Agent
#
# Pin the installer to the released Hermes tag and exact release commit.
# =============================================================================

RUN mkdir -p /home/node/.hermes \
    && chown -R node:node /home/node/.hermes \
    && su -s /bin/bash node -c '\
        set -eu; \
        export HOME=/home/node; \
        export HERMES_HOME=/home/node/.hermes; \
        export PATH="$HOME/.local/bin:$PATH"; \
        curl -fsSL \
          "https://raw.githubusercontent.com/NousResearch/hermes-agent/${HERMES_VERSION}/scripts/install.sh" \
          | bash -s -- \
              --non-interactive \
              --skip-browser \
              --skip-computer-use \
              --hermes-home /home/node/.hermes \
              --commit "${HERMES_COMMIT}"; \
    ' \
    && test -x /home/node/.local/bin/hermes \
    && ln -sf /home/node/.local/bin/hermes /usr/local/bin/hermes \
    && su -s /bin/bash node -c '\
        export HOME=/home/node; \
        export HERMES_HOME=/home/node/.hermes; \
        export PATH="$HOME/.local/bin:$PATH"; \
        hermes --version \
    '

# =============================================================================
# Hermes Python runtime dependencies
#
# Hermes is already installed by its official shell installer above.
# Do NOT `pip install .`: Hermes intentionally refuses wheel/sdist builds.
#
# Instead, install exactly the dependencies declared in Hermes'
# [project].dependencies section. This includes pathspec==1.1.1, which is
# required by main_web_build.py for calculating the web UI source hash.
# =============================================================================

RUN su -s /bin/bash node -c '\
        set -eu; \
        export HOME=/home/node; \
        export HERMES_HOME=/home/node/.hermes; \
        export PATH="$HOME/.local/bin:$PATH"; \
        cd /home/node/.hermes/hermes-agent; \
        python3 -c "\
import tomllib; \
from pathlib import Path; \
data = tomllib.loads(Path(\"pyproject.toml\").read_text(encoding=\"utf-8\")); \
Path(\"/tmp/hermes-runtime-requirements.txt\").write_text(\
    \"\\n\".join(data[\"project\"][\"dependencies\"]) + \"\\n\",\
    encoding=\"utf-8\"\
); \
print(\"Hermes dependencies:\", len(data[\"project\"][\"dependencies\"]))\
"; \
        python3 -m pip install \
            --user \
            --break-system-packages \
            -r /tmp/hermes-runtime-requirements.txt; \
        python3 -c "import pathspec; print(\"pathspec\", pathspec.__version__)"; \
        rm -f /tmp/hermes-runtime-requirements.txt; \
    '

# =============================================================================
# Hermes Web Dashboard
#
# Build the web UI into the image so the dashboard never needs to run npm
# install against the persistent runtime volume.
#
# Hermes determines whether a rebuild is required using:
#
#   - web_dist existence
#   - web-ui-build-stamp.json
#   - source-tree content hash
#
# Generate the stamp only after the complete web build and verify it
# immediately during the image build.
# =============================================================================

RUN su -s /bin/bash node -c '\
        set -eu; \
        export HOME=/home/node; \
        export HERMES_HOME=/home/node/.hermes; \
        export PATH="$HOME/.local/bin:$PATH"; \
        cd /home/node/.hermes/hermes-agent; \
        npm install --workspace web --include=dev; \
        npm run build -w web; \
        python3 -c "\
from pathlib import Path; \
from hermes_cli.main_web_build import (\
    _write_web_ui_build_stamp,\
    _web_project_root,\
    _web_ui_build_needed,\
); \
web = Path(\"/home/node/.hermes/hermes-agent/web\"); \
_write_web_ui_build_stamp(_web_project_root(web), web); \
assert not _web_ui_build_needed(web), \"Hermes web UI build stamp is invalid\"; \
print(\"Hermes web UI build: ready\")\
"; \
    '

# =============================================================================
# Verify Hermes web build state at image-build time
#
# This makes the Docker build fail if the resulting image cannot satisfy
# Hermes' runtime web-build check.
# =============================================================================

RUN su -s /bin/bash node -c '\
        set -eu; \
        export HOME=/home/node; \
        export HERMES_HOME=/home/node/.hermes; \
        export PATH="$HOME/.local/bin:$PATH"; \
        cd /home/node/.hermes/hermes-agent; \
        test -f /home/node/.hermes/web-ui-build-stamp.json; \
        python3 -c "\
from pathlib import Path; \
from hermes_cli.main_web_build import _web_ui_build_needed; \
web = Path(\"/home/node/.hermes/hermes-agent/web\"); \
needed = _web_ui_build_needed(web); \
print(\"Hermes web build needed:\", needed); \
assert not needed\
"; \
    '

# =============================================================================
# Hermes initial configuration
# =============================================================================

RUN cat > /home/node/.hermes/config.yaml <<'EOF'
model:
  provider: custom:bifrost
  default: openrouter/bifrost/main-free
  context_length: 1000000

providers:
  bifrost:
    name: Bifrost
    api: https://bifrost.phoenix-rtp.com/v1
    key_env: BIFROST_API_KEY
    transport: chat_completions
    default_model: openrouter/bifrost/main-free
    context_length: 1000000
EOF

RUN chown node:node /home/node/.hermes/config.yaml \
    && chmod 600 /home/node/.hermes/config.yaml

# =============================================================================
# Pi
# =============================================================================

RUN npm install -g --ignore-scripts @earendil-works/pi-coding-agent@1.0.0 \
    && pi --version

# =============================================================================
# Grok
# =============================================================================

RUN npm install -g @xai-official/grok@1.0.46 \
    && grok --version

# =============================================================================
# Cursor Agent
# =============================================================================

RUN su -s /bin/bash node -c '\
        set -eu; \
        export HOME=/home/node; \
        export PATH="$HOME/.local/bin:$PATH"; \
        curl -fsSL https://cursor.com/install | bash \
    ' \
    && test -x /home/node/.local/bin/agent \
    && ln -sf /home/node/.local/bin/agent /usr/local/bin/agent \
    && su -s /bin/bash node -c '\
        export HOME=/home/node; \
        export PATH="$HOME/.local/bin:$PATH"; \
        agent --version \
    '

USER node