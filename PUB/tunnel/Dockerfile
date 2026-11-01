FROM ubuntu:24.04

ENV container=docker
ENV DEBIAN_FRONTEND=noninteractive

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

STOPSIGNAL SIGRTMIN+3

CMD ["/sbin/init"]