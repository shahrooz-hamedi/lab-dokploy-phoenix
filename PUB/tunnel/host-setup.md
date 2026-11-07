Run this command on the pub's host (verify container name first):

set -eu

cd /etc/dokploy/compose/pub-tunnel-wj5p4n/code

install -o root -g root -m 0755 \
  PUB/tunnel/pub-host-routes.sh \
  /usr/local/sbin/pub-host-routes

install -o root -g root -m 0644 \
  PUB/tunnel/pub-host-routes.service \
  /etc/systemd/system/pub-host-routes.service

systemctl daemon-reload
systemctl enable pub-host-routes.service
systemctl restart pub-host-routes.service

systemctl --no-pager --full status pub-host-routes.service

ip route show | grep -E \
  '192\.168\.(10|11)\.0|172\.23\.0\.0|10\.100\.(20|10)\.'