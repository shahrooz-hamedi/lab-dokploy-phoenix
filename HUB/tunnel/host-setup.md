Run this command on the hub's host (verify container name first):

set -eu

cd /etc/dokploy/compose/hub-tunnel-kflvaq/code

install -o root -g root -m 0755 \
  HUB/tunnel/hub-host-routes.sh \
  /usr/local/sbin/hub-host-routes

install -o root -g root -m 0644 \
  HUB/tunnel/hub-host-routes.service \
  /etc/systemd/system/hub-host-routes.service

systemctl daemon-reload
systemctl enable hub-host-routes.service
systemctl restart hub-host-routes.service

systemctl --no-pager --full status hub-host-routes.service

ip route show | grep -E \
  '172\.19\.0\.0|192\.168\.(10|11)\.0|10\.100\.(20|30)\.'