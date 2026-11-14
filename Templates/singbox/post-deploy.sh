
#!/usr/bin/env bash
set -Eeuo pipefail

PROXY="socks5h://172.23.0.50:1080"
CONTAINER="hub-sing-box"
DOCKER_PROXY_FILE="/etc/systemd/system/docker.service.d/proxy.conf"
APT_PROXY_FILE="/etc/apt/apt.conf.d/90sing-box-proxy"
OLD_APT_PROXY_FILE="/etc/apt/apt.conf.d/90mac-socks-proxy"

if [[ "$EUID" -ne 0 ]]; then
    echo "ERROR: Run this script as root."
    exit 1
fi

echo "========== VERIFY SING-BOX =========="

if [[ "$(docker inspect -f '{{.State.Status}}' "$CONTAINER")" != "running" ]]; then
    echo "ERROR: $CONTAINER is not running."
    exit 1
fi

HTTP_STATUS=$(curl -sS \
    --connect-timeout 10 \
    --max-time 30 \
    --proxy "$PROXY" \
    -o /dev/null \
    -w '%{http_code}' \
    https://ghcr.io/v2/)

if [[ "$HTTP_STATUS" != "401" && "$HTTP_STATUS" != "200" ]]; then
    echo "ERROR: GHCR connectivity failed. HTTP $HTTP_STATUS"
    exit 1
fi

echo "Sing-box SOCKS: operational"
echo "GHCR HTTP status: $HTTP_STATUS"

echo
echo "========== CONFIGURE DOCKER PROXY =========="

DOCKER_CONFIG=$(cat <<'EOF'
[Service]
Environment="HTTP_PROXY=socks5h://172.23.0.50:1080"
Environment="HTTPS_PROXY=socks5h://172.23.0.50:1080"
Environment="NO_PROXY=localhost,127.0.0.1,::1,10.0.0.0/8,172.16.0.0/12,192.168.0.0/16"
EOF
)

mkdir -p /etc/systemd/system/docker.service.d

CHANGED=0

if [[ ! -f "$DOCKER_PROXY_FILE" ]] ||
   [[ "$(cat "$DOCKER_PROXY_FILE")" != "$DOCKER_CONFIG" ]]; then
    printf '%s\n' "$DOCKER_CONFIG" > "$DOCKER_PROXY_FILE"
    CHANGED=1
fi

echo
echo "========== CONFIGURE APT PROXY =========="

APT_CONFIG=$(cat <<'EOF'
Acquire::http::Proxy "socks5h://172.23.0.50:1080/";
Acquire::https::Proxy "socks5h://172.23.0.50:1080/";
EOF
)

if [[ ! -f "$APT_PROXY_FILE" ]] ||
   [[ "$(cat "$APT_PROXY_FILE")" != "$APT_CONFIG" ]]; then
    printf '%s\n' "$APT_CONFIG" > "$APT_PROXY_FILE"
    CHANGED=1
fi

if [[ -f "$OLD_APT_PROXY_FILE" ]]; then
    rm -f "$OLD_APT_PROXY_FILE"
    CHANGED=1
fi

if [[ "$CHANGED" -eq 1 ]]; then
    echo
    echo "========== RELOAD SYSTEMD =========="
    systemctl daemon-reload

    echo
    echo "========== RESTART DOCKER =========="
    systemctl restart docker
else
    echo "Proxy configuration already correct; Docker restart skipped."
fi

echo
echo "========== VERIFY DOCKER =========="

systemctl is-active docker

systemctl show docker -p Environment

echo
echo "========== VERIFY APT =========="

cat "$APT_PROXY_FILE"

echo
echo "========== VERIFY SING-BOX AFTER DOCKER RESTART =========="

for i in {1..30}; do
    STATUS=$(docker inspect -f '{{.State.Status}}' "$CONTAINER" 2>/dev/null || true)

    if [[ "$STATUS" == "running" ]]; then
        break
    fi

    sleep 2
done

if [[ "$STATUS" != "running" ]]; then
    echo "ERROR: Sing-box did not return to running state."
    exit 1
fi

echo "Sing-box: $STATUS"

echo
echo "========== VERIFY SWARM SERVICES =========="

docker service ls

echo
echo "========== VERIFY DOCKER REGISTRY ACCESS =========="

docker pull ghcr.io/sagernet/sing-box:v1.14.2

echo
echo "========== POST-DEPLOY COMPLETE =========="
