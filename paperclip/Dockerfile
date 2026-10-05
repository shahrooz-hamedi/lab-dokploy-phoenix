FROM ghcr.io/paperclipai/paperclip:2026.1001.0

USER root

# System dependencies required by Hermes' supported installer.
# libatomic1 is required by the managed Node.js runtime used by
# the current Hermes package manager.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       git \
       libatomic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Hermes Agent using the official supported Linux installer.
#
# Hermes manages its own Python/Node/tool runtime under HERMES_HOME.
# No pip/venv installation is used here.
USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:${PATH}

RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh \
    | bash -s -- --non-interactive

USER node