FROM ubuntu:24.04

ENV container=docker
ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    systemd \
    systemd-sysv \
    dbus \
    curl \
    ca-certificates \
    iproute2 \
    iputils-ping \
    iptables \
    jq \
    openssl \
    unzip \
    python3 \
    iperf3 \
    tar \
    figlet \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

STOPSIGNAL SIGRTMIN+3

CMD ["/sbin/init"]