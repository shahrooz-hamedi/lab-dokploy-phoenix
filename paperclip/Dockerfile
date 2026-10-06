FROM ghcr.io/paperclipai/paperclip:2026.1001.0

USER root

# System dependencies required by Hermes and its managed tools.
#
# libatomic1:
#   Required by the managed Node.js runtime used by Hermes PM.
#
# libx11-6:
#   Provides libX11.so.6 required by the Hermes cua-driver
#   Computer Use package during installation.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       git \
       libatomic1 \
       libx11-6 \
    && rm -rf /var/lib/apt/lists/*

USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:${PATH}

# Install Hermes Agent using the official supported installer.
#
# Hermes manages its own runtime and tool packages under HERMES_HOME.
# No pip/venv installation is used.
RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh \
    | bash -s -- --non-interactive

# ------------------------------------------------------------------
# Hermes -> Bifrost
#
# Proven runtime configuration:
#   provider: custom:bifrost
#   model:    openrouter/bifrost/main-free
#
# The Bifrost credential is deliberately NOT stored in the image.
# Hermes resolves BIFROST_CEO_API_KEY from the runtime environment.
# ------------------------------------------------------------------

RUN hermes config set model.provider custom:bifrost \
    && hermes config set model.default openrouter/bifrost/main-free \
    && hermes config set --force providers.bifrost.name Bifrost \
    && hermes config set --force providers.bifrost.base_url https://bifrost.phoenix-rtp.com/v1 \
    && hermes config set --force providers.bifrost.key_env BIFROST_CEO_API_KEY \
    && hermes config set --force providers.bifrost.discover_models true \
    && hermes config check

USER node