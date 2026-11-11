# Dograh API with the Speechify aiohttp proxy fix.
# Pin to the upstream image digest verified on HUB.
FROM ghcr.io/dograh-hq/dograh-api@sha256:715398c8376f8b6f04e46900d685693019fd3e016646c5df933358eb7d341fe0

USER root

COPY patch-speechify-proxy.py /tmp/patch-speechify-proxy.py

RUN python /tmp/patch-speechify-proxy.py \
    && chown dograh:dograh /app/api/services/pipecat/service_factory.py \
    && chmod 0644 /app/api/services/pipecat/service_factory.py \
    && rm -f /tmp/patch-speechify-proxy.py

USER dograh