#!/bin/bash
# mkrig2.sh BASE TAG: the row 299 rig layer over BASE (mkrig.sh): AT-SPI for pressing DriveSync's buttons by name, a test
# certificate authority trusted by the system store and the fake Google service's certificate for Google's four host
# names, the stand-in browser as the default https handler, and the fake-input client.
# Env: DOCKER_HOST, REPO (published tree), HTTPS_ONLY_APT, RIGDIR (this folder), FAKEINPUT_SRC (the proof rig's scripts folder), CONTAINER_IDS.
set -euo pipefail
BASE=${1:?base image}; TAG=${2:?tag}
: "${HTTPS_ONLY_APT:?}" "${RIGDIR:?}" "${FAKEINPUT_SRC:?}" "${CONTAINER_IDS:?}"
NAME=${PREFIX:-standin}-mkrig2-$$
docker create --name "$NAME" --ulimit core=1 --platform linux/amd64 --cpus 2 \
	--add-host repo.sparkyos.org:127.0.0.1 --add-host d2server:127.0.0.1 \
	--mount type=bind,src=/etc/ssl/certs/ca-certificates.crt,dst=/run/host-ca.crt,readonly \
	--mount "type=bind,src=$HTTPS_ONLY_APT,dst=/run/https-only-apt.sh,readonly" \
	--mount "type=bind,src=${REPO:?},dst=/repo,readonly" --mount "type=bind,src=$RIGDIR,dst=/rigsrc,readonly" --mount "type=bind,src=$FAKEINPUT_SRC,dst=/fisrc,readonly" \
	"$BASE" sh -c '
set -e; export DEBIAN_FRONTEND=noninteractive
sh /run/https-only-apt.sh
apt-get -y update > /dev/null 2>&1
apt-get -y --no-install-recommends install at-spi2-core gir1.2-atspi-2.0 curl socat > /tmp/apt.log 2>&1 || { tail -20 /tmp/apt.log; exit 1; }
rm -f /etc/apt/sources.list.d/sparky-stereo.sources
mkdir -p /rig && cd /rig
openssl req -x509 -newkey rsa:2048 -nodes -keyout ca.key -out ca.crt -days 60 -subj "/CN=DriveSync rig 299 test CA" \
	-addext basicConstraints=critical,CA:TRUE -addext keyUsage=critical,keyCertSign,cRLSign 2>/dev/null
openssl req -newkey rsa:2048 -nodes -keyout server.key -out server.csr -subj "/CN=www.googleapis.com" 2>/dev/null
printf "subjectAltName=DNS:www.googleapis.com,DNS:oauth2.googleapis.com,DNS:openidconnect.googleapis.com,DNS:accounts.google.com\nbasicConstraints=CA:FALSE\nkeyUsage=critical,digitalSignature,keyEncipherment\nextendedKeyUsage=serverAuth\n" > ext.cnf
openssl x509 -req -in server.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out server.crt -days 60 -extfile ext.cnf 2>/dev/null
chmod 644 server.key
cp ca.crt /usr/local/share/ca-certificates/drivesync-rig-299.crt && update-ca-certificates > /dev/null 2>&1
cp /rigsrc/fakegoogle.py /rig/ && cp /rigsrc/atspi.py /rig/ && cp /rigsrc/fake-nm.py /rig/ && cp /rigsrc/kwallet-login.py /rig/
install -m 755 /rigsrc/rig-browser /usr/local/bin/rig-browser
printf "[Desktop Entry]\nType=Application\nName=Rig Browser\nExec=/usr/local/bin/rig-browser %%u\nMimeType=x-scheme-handler/https;x-scheme-handler/http;\nNoDisplay=true\n" > /usr/share/applications/rig-browser.desktop
printf "[Default Applications]\nx-scheme-handler/https=rig-browser.desktop\nx-scheme-handler/http=rig-browser.desktop\n" > /etc/xdg/mimeapps.list
update-desktop-database /usr/share/applications 2>/dev/null || true
mkdir -p /tools && sh /fisrc/build-fakeinput.sh /tools > /dev/null
apt-get clean; rm -rf /var/lib/apt/lists/*' > /dev/null
docker inspect -f '{{.Id}}' "$NAME" >> "$CONTAINER_IDS"
status=0; docker start -a "$NAME" || status=$?
if [ "$status" != 0 ]; then docker rm -f "$NAME" > /dev/null; echo "rig layer failed ($status)" >&2; exit "$status"; fi
docker commit -c 'ENTRYPOINT []' -c 'CMD ["/bin/bash"]' "$NAME" "$TAG" > /dev/null
docker rm -f "$NAME" > /dev/null
echo "built $TAG"
