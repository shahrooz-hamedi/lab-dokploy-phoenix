FROM ghcr.io/paperclipai/paperclip:2026.1001.0

USER root

RUN apt-get update \
    && apt-get install -y --no-install-recommends python3-pip python3-venv \
    && rm -rf /var/lib/apt/lists/* \
    && python3 -m venv /opt/hermes \
    && PIP_DEFAULT_TIMEOUT=120 \
       PIP_RETRIES=10 \
       /opt/hermes/bin/pip install \
       --no-cache-dir \
       hermes-agent \
    && ln -s /opt/hermes/bin/hermes /usr/local/bin/hermes

USER node