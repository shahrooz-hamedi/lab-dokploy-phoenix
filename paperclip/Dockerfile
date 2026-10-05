FROM ghcr.io/paperclipai/paperclip:2026.1001.0

USER root

# Hermes' supported Linux installer requires curl and git.
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       curl \
       git \
    && rm -rf /var/lib/apt/lists/*

# Install Hermes Agent using the official Hermes installer.
#
# - Runs as the Paperclip runtime user, not root.
# - Uses Hermes' own managed Python/runtime environment.
# - Keeps Hermes state under /home/node/.hermes.
# - Non-interactive mode skips interactive setup/gateway installation.
# - Browser tooling remains available to Hermes.
USER node

ENV HOME=/home/node
ENV HERMES_HOME=/home/node/.hermes
ENV PATH=/home/node/.local/bin:${PATH}

RUN curl -fsSL https://hermes-agent.nousresearch.com/install.sh \
    | bash -s -- --non-interactive

USER node