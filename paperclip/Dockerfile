# =============================================================================
# Paperclip image
# =============================================================================

ARG PAPERCLIP_IMAGE=ghcr.io/paperclipai/paperclip:2026.916.1

FROM ${PAPERCLIP_IMAGE}

USER root

ARG HERMES_VERSION=v2026.9.24
ARG HERMES_COMMIT=f97608f178d1ffeca59860195ab7da295f7c8e5f

ENV HOME=/home/node \
    PAPERCLIP_HOME=/paperclip \
    HERMES_HOME=/home/node/.hermes \
    PATH=/home/node/.local/bin:/usr/local/bin:/usr/bin:/bin

# =============================================================================
# OS dependencies
# =============================================================================

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        python3 \
        build-essential \
    && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Hermes Agent
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
              --hermes-home /home/node/.hermes \
              --commit "${HERMES_COMMIT}"; \
        test -x /home/node/.local/bin/hermes; \
        hermes --version \
    ' \
    && ln -sf /home/node/.local/bin/hermes /usr/local/bin/hermes

# =============================================================================
# Hermes configuration
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