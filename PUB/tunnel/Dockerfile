FROM ubuntu:24.04

ENV container=docker
ENV DEBIAN_FRONTEND=noninteractive

ARG CTUNNEL_VERSION=v1.0.0

# --------------------------------------------------
# Base packages
# --------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    systemd \
    systemd-sysv \
    dbus \
    curl \
    wget \
    ca-certificates \
    git \
    iproute2 \
    iputils-ping \
    iputils-tracepath \
    iptables \
    wireguard-tools \
    dnsutils \
    net-tools \
    netcat-openbsd \
    socat \
    jq \
    openssl \
    unzip \
    zip \
    python3 \
    python3-pip \
    python3-venv \
    iperf3 \
    tcpdump \
    procps \
    psmisc \
    tar \
    figlet \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# --------------------------------------------------
# Install C-Tunnel
# --------------------------------------------------
RUN set -eux; \
    case "$(dpkg --print-architecture)" in \
        amd64) ARCH=amd64 ;; \
        arm64) ARCH=arm64 ;; \
        *) echo "Unsupported architecture"; exit 1 ;; \
    esac; \
    WORK="$(mktemp -d)"; \
    cd "$WORK"; \
    BASE="https://github.com/CIAUB/C-Tunnel/releases/download/${CTUNNEL_VERSION}"; \
    ASSETS="ctunnel-linux-${ARCH} ctunnel-engine-linux-${ARCH} ctunnel-kernel.sh ctunnel@.service ctunnel-engine@.service ctunnel-panel.service ctunnel-agent.service"; \
    curl -fsSLO "${BASE}/SHA256SUMS"; \
    for FILE in $ASSETS; do \
        curl -fsSLO "${BASE}/${FILE}"; \
        awk -v name="$FILE" '$2 == name {found=1; print} END {if (!found) exit 1}' SHA256SUMS | sha256sum -c -; \
    done; \
    install -D -m 0755 "ctunnel-linux-${ARCH}" /usr/local/bin/ctunnel; \
    install -D -m 0755 "ctunnel-engine-linux-${ARCH}" /usr/local/bin/ctunnel-engine; \
    ln -sf /usr/local/bin/ctunnel /usr/local/bin/c-tunnel; \
    install -D -m 0755 ctunnel-kernel.sh /usr/local/lib/ctunnel/ctunnel-kernel; \
    install -D -m 0644 ctunnel@.service /etc/systemd/system/ctunnel@.service; \
    install -D -m 0644 ctunnel-engine@.service /etc/systemd/system/ctunnel-engine@.service; \
    install -D -m 0644 ctunnel-panel.service /etc/systemd/system/ctunnel-panel.service; \
    install -D -m 0644 ctunnel-agent.service /etc/systemd/system/ctunnel-agent.service; \
    mkdir -p \
        /etc/ctunnel/tunnels \
        /etc/ctunnel/certs \
        /etc/systemd/system/multi-user.target.wants; \
    ln -sfn ../ctunnel-panel.service \
        /etc/systemd/system/multi-user.target.wants/ctunnel-panel.service; \
    ln -sfn ../ctunnel-agent.service \
        /etc/systemd/system/multi-user.target.wants/ctunnel-agent.service; \
    rm -rf "$WORK"

# --------------------------------------------------
# C-Tunnel automatic HTTPS initialization
# --------------------------------------------------
COPY ctunnel-panel-start /usr/local/sbin/ctunnel-panel-start

RUN chmod 0755 /usr/local/sbin/ctunnel-panel-start \
    && mkdir -p /etc/systemd/system/ctunnel-panel.service.d \
    && printf '[Service]\nExecStart=\nExecStart=/usr/local/sbin/ctunnel-panel-start\n' \
       > /etc/systemd/system/ctunnel-panel.service.d/https.conf

# --------------------------------------------------
# Permanent PUB <-> LAB routes
# Apply only to the existing pub-lab tunnel instance.
# --------------------------------------------------
COPY pub-site-routes /usr/local/sbin/pub-site-routes

RUN chmod 0755 /usr/local/sbin/pub-site-routes \
    && mkdir -p /etc/systemd/system/ctunnel-engine@pub-lab.service.d \
    && printf '[Service]\nExecStartPost=/usr/local/sbin/pub-site-routes\n' \
       > /etc/systemd/system/ctunnel-engine@pub-lab.service.d/site-routes.conf

# --------------------------------------------------
# Container runtime
# --------------------------------------------------
STOPSIGNAL SIGRTMIN+3

CMD ["/sbin/init"]