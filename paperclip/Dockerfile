FROM ghcr.io/paperclipai/paperclip:2026.1001.0

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && PIP_DEFAULT_TIMEOUT=120 \
       PIP_RETRIES=10 \
       python3 -m pip install \
       --no-cache-dir \
       --break-system-packages \
       hermes-agent

USER node